from uuid import UUID, uuid4
from typing import Optional
from datetime import datetime
from fastapi import HTTPException
import logging
import json

from src.core.config import settings
from src.core.errors import ErrorCode, ErrorSeverity, create_error_detail
from src.schemas.analysis import (
    StartAnalysisRequest,
    AnalysisJobStatus,
    PhysicalRiskScoreResponse,
    PastEventsResponse,
    FinancialImpactResponse,
    VulnerabilityResponse,
    AnalysisTotalResponse,
    PhysicalRiskBarItem,
    DisasterEvent,
    RiskVulnerability,
    SSPScenarioScore,
    SSPScenarioImpact,
    ShortTermScore,
    MidTermScore,
    LongTermScore,
    ShortTermAAL,
    MidTermAAL,
    LongTermAAL,
)
from src.schemas.common import HazardType, SSPScenario

# ai_agent 호출
from ai_agent import SKAXPhysicalRiskAnalyzer
from ai_agent.config.settings import load_config

# Database 연동
from ai_agent.utils.database import DatabaseManager


class AnalysisService:
    """분석 서비스 - ai_agent를 호출하여 분석 수행"""

    def __init__(self):
        """서비스 초기화"""
        self._analyzer = None
        self._analysis_results = {}  # site_id별 분석 결과 캐시
        self._cached_states = {}  # job_id별 State 캐시 (enhance용)
        self.logger = logging.getLogger("api.services.analysis")

        # batch_jobs 테이블 연동 (jobId 기반 조회용)
        try:
            self.db = DatabaseManager()
            self.logger.info("DatabaseManager initialized for batch_jobs tracking")
        except Exception as e:
            self.logger.warning(f"DatabaseManager initialization failed: {e}. Job tracking disabled.")
            self.db = None

    def _get_analyzer(self) -> SKAXPhysicalRiskAnalyzer:
        """ai_agent 분석기 인스턴스 반환 (lazy initialization)"""
        if self._analyzer is None:
            config = load_config()
            self._analyzer = SKAXPhysicalRiskAnalyzer(config)
        return self._analyzer

    async def _run_agent_analysis(
        self,
        site_info: dict,
        asset_value: float = 50000000000,
        additional_data: dict = None
    ) -> dict:
        """ai_agent 분석 실행 (ERD 기준)"""
        analyzer = self._get_analyzer()

        # SiteInfo에서 기본 위치 정보만 사용 (ERD 기준)
        target_location = {
            'latitude': site_info.get('lat', site_info.get('latitude', 37.5665)),
            'longitude': site_info.get('lng', site_info.get('longitude', 126.9780)),
            'name': site_info.get('name', 'Unknown Location'),
            'road_address': site_info.get('road_address'),
            'jibun_address': site_info.get('jibun_address')
        }

        # 건물/자산 정보는 additional_data에서 가져옴
        building_info = None
        asset_info = None

        if additional_data:
            # additional_data.building_info가 있으면 사용
            building_info = additional_data.get('building_info')
            asset_info = additional_data.get('asset_info')

        # 기본값 설정 (additional_data가 없을 경우)
        if not building_info:
            self.logger.warning("No building_info in additional_data, using minimal defaults")
            building_info = {}  # 빈 dict로 전달 (workflow에서 처리)

        if not asset_info:
            self.logger.warning("No asset_info in additional_data, using defaults")
            asset_info = {
                'total_asset_value': asset_value
            }

        analysis_params = {
            'time_horizon': '2050',
            'analysis_period': '2025-2050'
        }

        result = analyzer.analyze(
            target_location,
            building_info,
            asset_info,
            analysis_params,
            additional_data=additional_data
        )
        return result

    def _save_job_to_db(self, job_id: UUID, site_id: UUID, request: StartAnalysisRequest, status: str, progress: int = 0, results: dict = None):
        """batch_jobs 테이블에 job 저장"""
        if not self.db:
            return

        try:
            input_params = {
                'site_id': str(site_id),
                'user_id': str(request.user_id) if request.user_id else None,  # userId 추가 (Spring Boot 클라이언트 호환)
                'site_name': request.site.name,
                'hazard_types': request.hazard_types,
                'priority': request.priority.value if request.priority else 'normal',
                'options': {
                    'include_financial_impact': request.options.include_financial_impact if request.options else True,
                    'include_vulnerability': request.options.include_vulnerability if request.options else True,
                    'include_past_events': request.options.include_past_events if request.options else True,
                    'ssp_scenarios': [s.value for s in request.options.ssp_scenarios] if request.options else []
                }
            }

            query = """
                INSERT INTO batch_jobs (
                    batch_id, job_type, status, progress,
                    input_params, results, created_at, started_at
                ) VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT (batch_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    progress = EXCLUDED.progress,
                    results = EXCLUDED.results,
                    started_at = COALESCE(batch_jobs.started_at, NOW())
            """
            self.db.execute_update(query, (
                str(job_id),
                'physical_risk_analysis',
                status,
                progress,
                json.dumps(input_params),
                json.dumps(results) if results else None
            ))
            self.logger.info(f"Job {job_id} saved to batch_jobs table")
        except Exception as e:
            self.logger.error(f"Failed to save job to DB: {e}")

    def _update_job_in_db(self, job_id: UUID, status: str, progress: int, results: dict = None, error: dict = None):
        """batch_jobs 테이블의 job 상태 업데이트"""
        if not self.db:
            return

        try:
            if status in ['completed', 'failed']:
                query = """
                    UPDATE batch_jobs
                    SET status = %s, progress = %s, results = %s,
                        error_message = %s, completed_at = NOW()
                    WHERE batch_id = %s
                """
                self.db.execute_update(query, (
                    status,
                    progress,
                    json.dumps(results) if results else None,
                    json.dumps(error) if error else None,
                    str(job_id)
                ))
            else:
                query = """
                    UPDATE batch_jobs
                    SET status = %s, progress = %s
                    WHERE batch_id = %s
                """
                self.db.execute_update(query, (status, progress, str(job_id)))
            self.logger.info(f"Job {job_id} updated in batch_jobs table")
        except Exception as e:
            self.logger.error(f"Failed to update job in DB: {e}")

    async def start_analysis(self, site_id: UUID, request: StartAnalysisRequest) -> AnalysisJobStatus:
        """Spring Boot API 호환 - 분석 작업 시작 (문서 스펙 기준)"""
        job_id = uuid4()
        started_at = datetime.now()

        # DB에 job 생성 (queued 상태)
        self._save_job_to_db(job_id, site_id, request, status='queued', progress=0)

        if settings.USE_MOCK_DATA:
            self._update_job_in_db(job_id, status='running', progress=50)
            return AnalysisJobStatus(
                jobId=str(job_id),
                siteId=site_id,
                status="running",
                progress=50,
                currentNode="physical_risk_score",
                startedAt=started_at,
            )

        try:
            # 분석 시작
            self._update_job_in_db(job_id, status='running', progress=10)

            # Spring Boot 문서 스펙: site 객체 + hazardTypes, priority, options
            site_info = {
                'id': str(request.site.id),
                'name': request.site.name,
                'lat': request.site.latitude,
                'lng': request.site.longitude,
                'address': request.site.address,
                'type': request.site.industry
            }

            # Spring Boot는 additional_data를 보내지 않음
            result = await self._run_agent_analysis(site_info, additional_data=None)
            self._analysis_results[site_id] = result

            # State 캐싱 (enhance용) - Node 1~4 결과 포함
            self._cached_states[job_id] = result.copy()

            status = "completed" if result.get('workflow_status') == 'completed' else "failed"
            error = {"code": "ANALYSIS_FAILED", "message": str(result.get('errors', []))} if result.get('errors') else None

            # DB에 완료 상태 저장
            self._update_job_in_db(job_id, status=status, progress=100, results=result, error=error)

            return AnalysisJobStatus(
                jobId=str(job_id),
                siteId=site_id,
                status=status,
                progress=100 if status == "completed" else 0,
                currentNode="completed" if status == "completed" else "failed",
                startedAt=started_at,
                completedAt=datetime.now() if status == "completed" else None,
                error=error,
            )
        except Exception as e:
            error = {"code": "ANALYSIS_FAILED", "message": str(e)}
            self._update_job_in_db(job_id, status='failed', progress=0, error=error)

            return AnalysisJobStatus(
                jobId=str(job_id),
                siteId=site_id,
                status="failed",
                progress=0,
                currentNode="failed",
                startedAt=started_at,
                error=error,
            )

    async def enhance_analysis(
        self,
        site_id: UUID,
        job_id: UUID,
        additional_data_dict: dict,
        request_id: Optional[str] = None
    ) -> AnalysisJobStatus:
        """
        추가 데이터를 반영하여 분석 향상 (Node 5 이후 재실행)

        Args:
            site_id: 사업장 ID
            job_id: 원본 분석 작업 ID
            additional_data_dict: 추가 데이터
                - raw_text: 자유 형식 텍스트
                - metadata: 메타데이터
            request_id: 요청 ID (추적용)

        Returns:
            향상된 분석 작업 상태
        """
        # 로깅용 컨텍스트
        log_extra = {
            "request_id": request_id,
            "site_id": str(site_id),
            "original_job_id": str(job_id)
        }

        self.logger.info(
            f"Enhancement started for site_id={site_id}, job_id={job_id}",
            extra=log_extra
        )

        # 캐싱된 State 확인
        cached_state = self._cached_states.get(job_id)
        if not cached_state:
            self.logger.warning(
                f"Cache miss for job_id={job_id}",
                extra=log_extra
            )

            error_detail = create_error_detail(
                code=ErrorCode.ENHANCEMENT_CACHE_NOT_FOUND,
                detail=f"Cached state not found for job_id: {job_id}. Please run basic analysis first.",
                request_id=request_id,
                severity=ErrorSeverity.MEDIUM,
                context={"job_id": str(job_id), "site_id": str(site_id)}
            )

            raise HTTPException(
                status_code=404,
                detail=error_detail.dict()
            )

        self.logger.info(
            f"Cache hit for job_id={job_id}",
            extra=log_extra
        )

        # 새로운 job_id 생성
        new_job_id = uuid4()
        log_extra["new_job_id"] = str(new_job_id)

        try:
            analyzer = self._get_analyzer()

            self.logger.info(
                f"Calling AI agent for enhancement (new_job_id={new_job_id})",
                extra=log_extra
            )

            # cached_state에 request_id 추가 (AI agent 로깅용)
            cached_state_with_id = cached_state.copy()
            cached_state_with_id['_request_id'] = request_id

            # Node 5 이후 재실행
            result = analyzer.enhance_with_additional_data(
                cached_state=cached_state_with_id,
                additional_data=additional_data_dict
            )

            # 결과 저장
            self._analysis_results[site_id] = result

            # 새로운 State도 캐싱 (추가 향상 가능)
            self._cached_states[new_job_id] = result.copy()

            status = "completed" if result.get('workflow_status') == 'completed' else "failed"

            if status == "completed":
                self.logger.info(
                    f"Enhancement completed successfully (new_job_id={new_job_id})",
                    extra=log_extra
                )
            else:
                self.logger.warning(
                    f"Enhancement completed with errors (new_job_id={new_job_id})",
                    extra={**log_extra, "errors": result.get('errors', [])}
                )

            return AnalysisJobStatus(
                jobId=str(new_job_id),
                siteId=site_id,
                status=status,
                progress=100 if status == "completed" else 0,
                currentNode="completed" if status == "completed" else "failed",
                startedAt=datetime.now(),
                completedAt=datetime.now() if status == "completed" else None,
                error={"code": "ENHANCEMENT_FAILED", "message": str(result.get('errors', []))} if result.get('errors') else None,
            )

        except HTTPException:
            # HTTPException은 그대로 전파
            raise

        except Exception as e:
            self.logger.error(
                f"Enhancement failed: {str(e)}",
                extra=log_extra,
                exc_info=True
            )

            error_detail = create_error_detail(
                code=ErrorCode.ENHANCEMENT_FAILED,
                detail=str(e),
                request_id=request_id,
                severity=ErrorSeverity.HIGH,
                context={"job_id": str(job_id), "site_id": str(site_id)}
            )

            return AnalysisJobStatus(
                jobId=str(new_job_id),
                siteId=site_id,
                status="failed",
                progress=0,
                currentNode="failed",
                startedAt=datetime.now(),
                error=error_detail.dict(),
            )

    async def get_job_status(self, job_id: UUID, site_id: Optional[UUID] = None) -> Optional[AnalysisJobStatus]:
        """
        Spring Boot API 호환 - 작업 상태 조회

        Args:
            job_id: 작업 ID (필수)
            site_id: 사업장 ID (선택, 하위 호환성용)

        Returns:
            AnalysisJobStatus 또는 None (job이 없을 경우)
        """
        if settings.USE_MOCK_DATA:
            return AnalysisJobStatus(
                jobId=str(job_id),
                siteId=str(site_id) if site_id else "00000000-0000-0000-0000-000000000000",
                status="completed",
                progress=100,
                currentNode="completed",
                startedAt=datetime.now(),
                completedAt=datetime.now(),
            )

        # batch_jobs 테이블에서 jobId로 조회
        if not self.db:
            self.logger.warning("Database not available, cannot query job status")
            return None

        try:
            query = """
                SELECT
                    batch_id, job_type, status, progress,
                    input_params, results, error_message,
                    created_at, started_at, completed_at
                FROM batch_jobs
                WHERE batch_id = %s
            """
            result = self.db.execute_query(query, (str(job_id),))

            if not result or len(result) == 0:
                self.logger.warning(f"Job {job_id} not found in batch_jobs")
                return None

            job = result[0]
            input_params = job.get('input_params', {})

            # site_id 추출 (input_params에서)
            job_site_id = input_params.get('site_id') if isinstance(input_params, dict) else None

            # error_message 파싱
            error_msg = job.get('error_message')
            error_dict = None
            if error_msg:
                try:
                    error_dict = json.loads(error_msg) if isinstance(error_msg, str) else error_msg
                except:
                    error_dict = {"code": "UNKNOWN_ERROR", "message": str(error_msg)}

            return AnalysisJobStatus(
                jobId=str(job['batch_id']),
                siteId=job_site_id or (str(site_id) if site_id else None),
                status=job['status'],
                progress=job.get('progress', 0),
                currentNode=job['status'],  # status를 currentNode로 사용
                currentHazard=None,
                startedAt=job.get('started_at'),
                completedAt=job.get('completed_at'),
                estimatedCompletionTime=None,
                error=error_dict
            )
        except Exception as e:
            self.logger.error(f"Failed to query job status from DB: {e}")
            return None

    async def get_job_status_by_id(self, job_id: UUID) -> Optional[AnalysisJobStatus]:
        """
        jobId로 분석 작업 상태 조회 (Spring Boot 클라이언트 호환)

        Args:
            job_id: 작업 ID

        Returns:
            AnalysisJobStatus 또는 None (job이 없을 경우)
        """
        return await self.get_job_status(job_id)

    async def get_latest_job_status_by_user(self, user_id: UUID) -> Optional[AnalysisJobStatus]:
        """
        userId로 가장 최근 분석 작업 상태 조회 (Spring Boot 클라이언트 호환)

        Args:
            user_id: 사용자 ID

        Returns:
            AnalysisJobStatus 또는 None (해당 사용자의 job이 없을 경우)
        """
        if settings.USE_MOCK_DATA:
            return AnalysisJobStatus(
                jobId="00000000-0000-0000-0000-000000000000",
                siteId="00000000-0000-0000-0000-000000000000",
                status="completed",
                progress=100,
                currentNode="completed",
                startedAt=datetime.now(),
                completedAt=datetime.now(),
            )

        # batch_jobs 테이블에서 userId로 가장 최근 job 조회
        if not self.db:
            self.logger.warning("Database not available, cannot query job status")
            return None

        try:
            # TODO: batch_jobs 테이블에 user_id 컬럼 추가 필요
            # 현재는 input_params JSON 내부에서 user_id를 찾아야 함
            # 임시 구현: input_params::jsonb ? 'user_id' 조건 사용
            query = """
                SELECT
                    batch_id, job_type, status, progress,
                    input_params, results, error_message,
                    created_at, started_at, completed_at
                FROM batch_jobs
                WHERE input_params::jsonb->>'user_id' = %s
                ORDER BY created_at DESC
                LIMIT 1
            """
            result = self.db.execute_query(query, (str(user_id),))

            if not result or len(result) == 0:
                self.logger.warning(f"No jobs found for user {user_id}")
                return None

            job = result[0]
            input_params = job.get('input_params', {})

            # site_id 추출 (input_params에서)
            job_site_id = input_params.get('site_id') if isinstance(input_params, dict) else None

            # error_message 파싱
            error_msg = job.get('error_message')
            error_dict = None
            if error_msg:
                try:
                    error_dict = json.loads(error_msg) if isinstance(error_msg, str) else error_msg
                except:
                    error_dict = {"code": "UNKNOWN_ERROR", "message": str(error_msg)}

            return AnalysisJobStatus(
                jobId=str(job['batch_id']),
                siteId=job_site_id,
                status=job['status'],
                progress=job.get('progress', 0),
                currentNode=job['status'],  # status를 currentNode로 사용
                currentHazard=None,
                startedAt=job.get('started_at'),
                completedAt=job.get('completed_at'),
                estimatedCompletionTime=None,
                error=error_dict
            )
        except Exception as e:
            self.logger.error(f"Failed to query latest job status for user {user_id}: {e}")
            return None

    async def get_physical_risk_scores(
        self, site_id: UUID, hazard_type: Optional[str]
    ) -> Optional[PhysicalRiskScoreResponse]:
        """Spring Boot API 호환 - 시나리오별 물리적 리스크 점수 조회"""
        if settings.USE_MOCK_DATA:
            # hazard_type이 영문 이름이면 enum으로 변환
            risk_type = HazardType.HIGH_TEMPERATURE  # 기본값
            if hazard_type:
                try:
                    # HazardType enum의 name으로 조회 (예: "HIGH_TEMPERATURE")
                    risk_type = HazardType[hazard_type]
                except KeyError:
                    # 값으로 조회 시도 (예: "폭염")
                    try:
                        risk_type = HazardType(hazard_type)
                    except ValueError:
                        pass  # 기본값 사용

            scenarios = []
            for scenario in [SSPScenario.SSP1_26, SSPScenario.SSP2_45, SSPScenario.SSP3_70, SSPScenario.SSP5_85]:
                scenarios.append(SSPScenarioScore(
                    scenario=scenario,
                    riskType=risk_type,
                    shortTerm=ShortTermScore(q1=65, q2=72, q3=78, q4=70),
                    midTerm=MidTermScore(year2026=68, year2027=70, year2028=73, year2029=75, year2030=77),
                    longTerm=LongTermScore(year2020s=72, year2030s=78, year2040s=84, year2050s=89),
                ))

            return PhysicalRiskScoreResponse(scenarios=scenarios)

        return None

    async def get_past_events(self, site_id: UUID) -> Optional[PastEventsResponse]:
        """Spring Boot API 호환 - 과거 재난 이력 조회"""
        if settings.USE_MOCK_DATA:
            disasters = [
                DisasterEvent(
                    disasterType="폭염",
                    year=2023,
                    warningDays=15,
                    severeDays=5,
                    overallStatus="심각",
                ),
                DisasterEvent(
                    disasterType="태풍",
                    year=2022,
                    warningDays=3,
                    severeDays=2,
                    overallStatus="주의",
                ),
                DisasterEvent(
                    disasterType="홍수",
                    year=2020,
                    warningDays=5,
                    severeDays=3,
                    overallStatus="심각",
                ),
            ]

            return PastEventsResponse(
                siteId=site_id,
                siteName="서울 본사",
                disasters=disasters,
            )

        return None

    async def get_financial_impacts(self, site_id: UUID) -> Optional[FinancialImpactResponse]:
        """Spring Boot API 호환 - 시나리오별 재무 영향(AAL) 조회"""
        if settings.USE_MOCK_DATA:
            scenarios = []
            for scenario in [SSPScenario.SSP1_26, SSPScenario.SSP2_45, SSPScenario.SSP3_70, SSPScenario.SSP5_85]:
                scenarios.append(SSPScenarioImpact(
                    scenario=scenario,
                    riskType=HazardType.HIGH_TEMPERATURE,
                    shortTerm=ShortTermAAL(q1=0.015, q2=0.018, q3=0.021, q4=0.019),
                    midTerm=MidTermAAL(year2026=0.023, year2027=0.025, year2028=0.027, year2029=0.029, year2030=0.031),
                    longTerm=LongTermAAL(year2020s=0.028, year2030s=0.035, year2040s=0.042, year2050s=0.051),
                ))

            return FinancialImpactResponse(scenarios=scenarios)

        return None

    async def get_vulnerability(self, site_id: UUID) -> Optional[VulnerabilityResponse]:
        """Spring Boot API 호환 - 취약성 분석"""
        if settings.USE_MOCK_DATA:
            vulnerabilities = [
                RiskVulnerability(riskType="폭염", vulnerabilityScore=75),
                RiskVulnerability(riskType="태풍", vulnerabilityScore=70),
                RiskVulnerability(riskType="홍수", vulnerabilityScore=55),
                RiskVulnerability(riskType="가뭄", vulnerabilityScore=40),
            ]

            return VulnerabilityResponse(
                siteId=site_id,
                vulnerabilities=vulnerabilities,
            )

        # 실제 DB에서 조회
        from ai_agent.utils.database import get_db_connection

        logger.info(f"[VULNERABILITY] 취약성 데이터 조회 시작: site_id={site_id}")

        query = """
            SELECT
                risk_type,
                vulnerability_score
            FROM vulnerability_results
            WHERE site_id = %s
            ORDER BY risk_type
        """

        conn = None
        try:
            conn = get_db_connection()
            logger.info(f"[VULNERABILITY] DB 연결 성공")

            with conn.cursor() as cursor:
                cursor.execute(query, (str(site_id),))
                rows = cursor.fetchall()
                logger.info(f"[VULNERABILITY] 쿼리 실행 완료: {len(rows)}개 행 조회됨")

                if not rows:
                    logger.warning(f"[VULNERABILITY] 데이터 없음: site_id={site_id}")
                    return None

                # Risk type 매핑 (영문 -> 한글)
                risk_type_mapping = {
                    'high_temperature': '폭염',
                    'typhoon': '태풍',
                    'inland_flood': '내륙홍수',
                    'coastal_flood': '해안홍수',
                    'drought': '가뭄',
                    'cold_wave': '한파',
                    'wildfire': '산불',
                    'water_scarcity': '물부족',
                    'urban_flood': '도시홍수'
                }

                vulnerabilities = []
                for row in rows:
                    risk_type = row[0]
                    vulnerability_score = int(row[1]) if row[1] is not None else 0

                    # 한글 이름 변환
                    korean_name = risk_type_mapping.get(risk_type, risk_type)

                    vulnerabilities.append(
                        RiskVulnerability(
                            riskType=korean_name,
                            vulnerabilityScore=vulnerability_score
                        )
                    )

                return VulnerabilityResponse(
                    siteId=site_id,
                    vulnerabilities=vulnerabilities,
                )
        except Exception as e:
            logger.error(f"취약성 데이터 조회 실패: {str(e)}")
            return None
        finally:
            if conn:
                conn.close()

    async def get_total_analysis(
        self, site_id: UUID, hazard_type: str
    ) -> Optional[AnalysisTotalResponse]:
        """Spring Boot API 호환 - 특정 Hazard 기준 통합 분석 결과"""
        if settings.USE_MOCK_DATA:
            physical_risks = [
                PhysicalRiskBarItem(
                    riskType=HazardType.HIGH_TEMPERATURE,
                    riskScore=75,
                    financialLossRate=0.023,
                ),
                PhysicalRiskBarItem(
                    riskType=HazardType.TYPHOON,
                    riskScore=70,
                    financialLossRate=0.018,
                ),
                PhysicalRiskBarItem(
                    riskType=HazardType.INLAND_FLOOD,
                    riskScore=55,
                    financialLossRate=0.012,
                ),
                PhysicalRiskBarItem(
                    riskType=HazardType.DROUGHT,
                    riskScore=40,
                    financialLossRate=0.008,
                ),
                PhysicalRiskBarItem(
                    riskType=HazardType.COLD_WAVE,
                    riskScore=35,
                    financialLossRate=0.006,
                ),
                PhysicalRiskBarItem(
                    riskType=HazardType.WILDFIRE,
                    riskScore=25,
                    financialLossRate=0.004,
                ),
                PhysicalRiskBarItem(
                    riskType=HazardType.COASTAL_FLOOD,
                    riskScore=30,
                    financialLossRate=0.005,
                ),
                PhysicalRiskBarItem(
                    riskType=HazardType.URBAN_FLOOD,
                    riskScore=50,
                    financialLossRate=0.010,
                ),
                PhysicalRiskBarItem(
                    riskType=HazardType.WATER_SCARCITY,
                    riskScore=45,
                    financialLossRate=0.009,
                ),
            ]

            return AnalysisTotalResponse(
                siteId=site_id,
                siteName="서울 본사",
                physicalRisks=physical_risks,
            )

        return None

    def _check_and_send_completion_callback(self, user_id: UUID):
        """
        리포트 생성과 후보지 추천이 모두 완료되었는지 확인 후 Spring Boot 콜백

        Args:
            user_id: 사용자 ID
        """
        if not user_id or not self.db:
            return

        try:
            # batch_jobs에서 user_id의 작업 상태 확인
            query = """
                SELECT
                    input_params::jsonb->>'user_id' as user_id,
                    MAX(CASE WHEN job_type = 'physical_risk_analysis' AND status = 'completed' THEN 1 ELSE 0 END) as report_done,
                    MAX(CASE WHEN job_type = 'site_recommendation' AND status = 'completed' THEN 1 ELSE 0 END) as recommendation_done
                FROM batch_jobs
                WHERE input_params::jsonb->>'user_id' = %s
                GROUP BY input_params::jsonb->>'user_id'
            """
            result = self.db.execute_query(query, (str(user_id),))

            if result and len(result) > 0:
                row = result[0]
                report_done = row.get('report_done') == 1
                recommendation_done = row.get('recommendation_done') == 1

                # 둘 다 완료되었는지 확인
                if report_done and recommendation_done:
                    # 콜백 전송 여부 확인 (중복 방지)
                    callback_check_query = """
                        SELECT COUNT(*) as callback_sent
                        FROM batch_jobs
                        WHERE input_params::jsonb->>'user_id' = %s
                        AND job_type = 'spring_boot_callback'
                        AND status = 'completed'
                    """
                    callback_result = self.db.execute_query(callback_check_query, (str(user_id),))

                    if callback_result and callback_result[0].get('callback_sent', 0) == 0:
                        # Spring Boot 콜백 호출
                        from ai_agent.services.springboot_client import get_springboot_client

                        springboot_client = get_springboot_client()
                        springboot_client.notify_analysis_completion(user_id)

                        # 콜백 전송 기록 저장
                        self._save_callback_record(user_id)
                        self.logger.info(f"[CALLBACK] Spring Boot 알림 전송 완료: user_id={user_id}")
                    else:
                        self.logger.info(f"[CALLBACK] 이미 전송됨: user_id={user_id}")
                else:
                    self.logger.debug(f"[CALLBACK] 아직 미완료 - report: {report_done}, recommendation: {recommendation_done}")
        except Exception as e:
            self.logger.error(f"Spring Boot 콜백 확인/전송 실패: {str(e)}")
            # 에러 발생해도 분석 결과는 유효

    def _save_callback_record(self, user_id: UUID):
        """콜백 전송 기록 저장"""
        if not self.db:
            return

        try:
            query = """
                INSERT INTO batch_jobs (
                    batch_id, job_type, status, progress,
                    input_params, created_at, completed_at
                ) VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            """
            self.db.execute_update(query, (
                str(uuid4()),
                'spring_boot_callback',
                'completed',
                100,
                json.dumps({'user_id': str(user_id)})
            ))
        except Exception as e:
            self.logger.error(f"콜백 기록 저장 실패: {str(e)}")

    async def on_report_generation_completed(self, user_id: UUID):
        """리포트 생성 완료 시 호출"""
        self.logger.info(f"[CALLBACK] 리포트 생성 완료: user_id={user_id}")
        self._check_and_send_completion_callback(user_id)

    async def on_relocation_recommendation_completed(self, user_id: UUID):
        """후보지 추천 완료 시 호출"""
        self.logger.info(f"[CALLBACK] 후보지 추천 완료: user_id={user_id}")
        self._check_and_send_completion_callback(user_id)
