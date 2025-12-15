from uuid import UUID, uuid4
from typing import Optional, List
from datetime import datetime
from fastapi import HTTPException
import logging
import json
import asyncio

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
    AnalysisSummaryResponse,
    AnalysisSummaryData,
    PhysicalRiskScores,
    AALScores,
    AnalysisOptions,
)
from src.schemas.common import HazardType, SSPScenario, SiteInfo, Priority

# ai_agent 호출
from ai_agent import SKAXPhysicalRiskAnalyzer
from ai_agent.config.settings import load_config

# Database 연동
from ai_agent.utils.database import DatabaseManager


# 9개 리스크 타입 상수 (영문 - DB 저장 형식)
RISK_TYPES = [
    'extreme_heat',
    'extreme_cold',
    'river_flood',
    'urban_flood',
    'drought',
    'water_stress',
    'sea_level_rise',
    'typhoon',
    'wildfire'
]

# 영문 → 한글 매핑
RISK_TYPE_KR_MAPPING = {
    'extreme_heat': '폭염',
    'extreme_cold': '한파',
    'wildfire': '산불',
    'drought': '가뭄',
    'water_stress': '물부족',
    'sea_level_rise': '해안침수',
    'river_flood': '내륙침수',
    'urban_flood': '도시침수',
    'typhoon': '태풍'
}

# 분석 기준 연도 및 시나리오
TARGET_YEAR = 2040
SSP_SCENARIO = 'ssp245'  # SSP2-4.5


class AnalysisService:
    """분석 서비스 - ai_agent를 호출하여 분석 수행"""

    def __init__(self):
        """서비스 초기화"""
        self._analyzer = None
        self._analysis_results = {}  # (job_id별 Agent 결과 저장)
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

    def _save_job_to_db(self, job_id: UUID, user_id: Optional[UUID], site_infos: list[SiteInfo], hazard_types: list[str], priority: Priority, options: Optional[AnalysisOptions], status: str, progress: int = 0, results: dict = None):
        """batch_jobs 테이블에 job 저장 (다중 사업장 요청 전체에 대한 단일 Job)"""
        if not self.db:
            return

        try:
            # Prepare input_params with full request details
            input_params = {
                'user_id': str(user_id) if user_id else None,
                'site_ids': [str(s.id) for s in site_infos], # Store all site IDs
                'site_names': [s.name for s in site_infos], # Store all site names
                'hazard_types': hazard_types,
                'priority': priority.value if priority else 'normal',
                'options': options.model_dump() if options else {} # Store options
            }

            query = """
                INSERT INTO batch_jobs (
                    batch_id, job_type, status, progress,
                    input_params, results, created_at, started_at, created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW(), %s)
                ON CONFLICT (batch_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    progress = EXCLUDED.progress,
                    results = EXCLUDED.results,
                    input_params = EXCLUDED.input_params,
                    started_at = COALESCE(batch_jobs.started_at, NOW())
            """
            self.db.execute_update(query, (
                str(job_id),
                'multi_site_analysis', # Job type changed
                status,
                progress,
                json.dumps(input_params),
                json.dumps(results) if results else None,
                str(user_id) if user_id else None
            ))
            self.logger.info(f"Job {job_id} saved to batch_jobs table")
        except Exception as e:
            self.logger.error(f"Failed to save job to DB: {e}")

    def _update_job_in_db(self, job_id: UUID, status: str, progress: int, results: dict = None, error: dict = None):
        """batch_jobs 테이블의 job 상태 업데이트"""
        if not self.db:
            return

        try:
            # done일 때는 completed_at 설정 (상태는 ing와 done만 있음)
            if status == 'done' or status == 'failed': # Added 'failed' status for completion
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
                # ing 상태
                query = """
                    UPDATE batch_jobs
                    SET status = %s, progress = %s
                    WHERE batch_id = %s
                """
                self.db.execute_update(query, (status, progress, str(job_id)))
            self.logger.info(f"Job {job_id} updated in batch_jobs table: status={status}")
        except Exception as e:
            self.logger.error(f"Failed to update job in DB: {e}")

    async def start_analysis_async(self, request: StartAnalysisRequest, background_tasks) -> AnalysisJobStatus:
        """
        복수 사업장에 대한 분석 작업 시작 (비동기) - 단일 job_id로 관리

        즉시 202 Accepted를 반환하고 백그라운드에서 모든 사업장에 대한 분석을 실행
        """
        job_id = uuid4()
        started_at = datetime.now()

        # DB에 단일 배치 job 생성 (ing 상태)
        self._save_job_to_db(
            job_id=job_id,
            user_id=request.user_id,
            site_infos=request.sites,
            hazard_types=request.hazard_types,
            priority=request.priority,
            options=request.options,
            status='ing',
            progress=0
        )

        if settings.USE_MOCK_DATA:
            # For mock data, pick the first site's ID for the response
            first_site_id = request.sites[0].id if request.sites else uuid4()
            return AnalysisJobStatus(
                jobId=job_id,
                siteId=first_site_id,
                status="ing",
                progress=0,
                currentNode="started",
                startedAt=started_at,
            )

        # 백그라운드에서 실제 분석 실행
        background_tasks.add_task(self._run_multi_analysis_background, job_id, request)

        # For the response, pick the first site's ID for compatibility with existing clients
        first_site_id = request.sites[0].id if request.sites else uuid4()
        return AnalysisJobStatus(
            jobId=job_id,
            siteId=first_site_id,
            status="ing",
            progress=0,
            currentNode="started",
            startedAt=started_at,
        )

    async def _run_multi_analysis_background(self, job_id: UUID, request: StartAnalysisRequest):
        """백그라운드에서 실행되는 실제 다중 사업장 분석 로직"""
        self.logger.info(f"[BACKGROUND] 다중 사업장 분석 시작: job_id={job_id}, site_count={len(request.sites)}")

        try:
            # Prepare inputs for the agent's multi-site method
            target_locations = []
            building_infos = [] # Assuming Agent will handle defaults if dict is empty
            asset_infos = [] # Assuming Agent will handle defaults if dict is empty

            for site in request.sites:
                target_locations.append({
                    'latitude': site.latitude,
                    'longitude': site.longitude,
                    'name': site.name,
                })
                # For simplicity, pass empty dicts for building_info and asset_info
                # The agent method analyze_multiple_sites will need to handle defaults or derive them per site.
                building_infos.append({}) 
                asset_infos.append({'total_asset_value': 50000000000}) # Pass default asset value

            analysis_params = {
                'time_horizon': '2050',
                'analysis_period': '2025-2050'
            }
            
            # This is the core assumption based on user's instruction.
            # Call the assumed multi-site agent method.
            # Expected to return a dict or list of dicts that represent the consolidated result.
            agent_result = await self._run_agent_multiple_analysis_wrapper(
                target_locations=target_locations,
                building_infos=building_infos,
                asset_infos=asset_infos,
                analysis_params=analysis_params,
                user_id=request.user_id, # Pass user_id
                hazard_types=request.hazard_types, # Pass hazard_types
                priority=request.priority, # Pass priority
                options=request.options, # Pass options
            )

            error = {"code": "ANALYSIS_FAILED", "message": str(agent_result.get('errors', []))} if agent_result and agent_result.get('errors') else None
            status = 'done' if not error else 'failed'
            progress = 100
            
            self._analysis_results[job_id] = agent_result
            self._cached_states[job_id] = agent_result.copy()

            self._update_job_in_db(job_id, status=status, progress=progress, results=agent_result, error=error)

            self.logger.info(f"[BACKGROUND] 다중 사업장 분석 완료: job_id={job_id}, status={status}")

        except Exception as e:
            self.logger.error(f"[BACKGROUND] 다중 사업장 분석 실패: job_id={job_id}, error={str(e)}", exc_info=True)
            error = {"code": "ANALYSIS_FAILED", "message": str(e)}
            self._update_job_in_db(job_id, status='failed', progress=100, error=error)

    async def _run_agent_multiple_analysis_wrapper(
        self,
        target_locations: List[dict],
        building_infos: List[dict],
        asset_infos: List[dict],
        analysis_params: dict,
        user_id: Optional[UUID],
        hazard_types: List[str], # New parameter
        priority: Priority, # New parameter
        options: Optional[AnalysisOptions], # New parameter
        additional_data: Optional[dict] = None,
        language: str = 'ko'
    ) -> dict:
        """
        ai_agent의 다중 사업장 분석 메소드 래퍼 (비동기)
        Agent에 analyze_multiple_sites 메소드가 있다고 가정
        """
        analyzer = self._get_analyzer()
        loop = asyncio.get_event_loop()
        
        # assumed Agent's method is synchronous
        # TODO: The actual agent method might be named 'analyze_integrated'.
        # For now, we assume 'analyze_multiple_sites' exists or will exist.
        if not hasattr(analyzer, 'analyze_multiple_sites'):
            # Fallback or error if the method doesn't exist yet
            self.logger.error("Agent method 'analyze_multiple_sites' not found. This needs to be implemented in the agent.")
            raise NotImplementedError("Agent method 'analyze_multiple_sites' is not implemented.")

        result = await loop.run_in_executor(
            None,
            analyzer.analyze_multiple_sites, # Assumed new method
            target_locations,
            building_infos,
            asset_infos,
            analysis_params,
            user_id,
            hazard_types,
            priority,
            options,
            additional_data,
            language
        )
        return result


    # async def enhance_analysis(
    #     self,
    #     site_id: UUID,
    #     job_id: UUID,
    #     additional_data_dict: dict,
    #     request_id: Optional[str] = None
    # ) -> AnalysisJobStatus:
    #     """
    #     추가 데이터를 반영하여 분석 향상 (Node 5 이후 재실행)

    #     Args:
    #         site_id: 사업장 ID
    #         job_id: 원본 분석 작업 ID
    #         additional_data_dict: 추가 데이터
    #             - raw_text: 자유 형식 텍스트
    #             - metadata: 메타데이터
    #         request_id: 요청 ID (추적용)

    #     Returns:
    #         향상된 분석 작업 상태
    #     """
    #     # 로깅용 컨텍스트
    #     log_extra = {
    #         "request_id": request_id,
    #         "site_id": str(site_id),
    #         "original_job_id": str(job_id)
    #     }

    #     self.logger.info(
    #         f"Enhancement started for site_id={site_id}, job_id={job_id}",
    #         extra=log_extra
    #     )

    #     # 캐싱된 State 확인
    #     cached_state = self._cached_states.get(job_id)
    #     if not cached_state:
    #         self.logger.warning(
    #             f"Cache miss for job_id={job_id}",
    #             extra=log_extra
    #         )

    #         error_detail = create_error_detail(
    #             code=ErrorCode.ENHANCEMENT_CACHE_NOT_FOUND,
    #             detail=f"Cached state not found for job_id: {job_id}. Please run basic analysis first.",
    #             request_id=request_id,
    #             severity=ErrorSeverity.MEDIUM,
    #             context={"job_id": str(job_id), "site_id": str(site_id)}
    #         )

    #         raise HTTPException(
    #             status_code=404,
    #             detail=error_detail.dict()
    #         )

    #     self.logger.info(
    #         f"Cache hit for job_id={job_id}",
    #         extra=log_extra
    #     )

    #     # 새로운 job_id 생성
    #     new_job_id = uuid4()
    #     log_extra["new_job_id"] = str(new_job_id)

    #     try:
    #         analyzer = self._get_analyzer()

    #         self.logger.info(
    #             f"Calling AI agent for enhancement (new_job_id={new_job_id})",
    #             extra=log_extra
    #         )

    #         # cached_state에 request_id 추가 (AI agent 로깅용)
    #         cached_state_with_id = cached_state.copy()
    #         cached_state_with_id['_request_id'] = request_id

    #         # Node 5 이후 재실행
    #         result = analyzer.enhance_with_additional_data(
    #             cached_state=cached_state_with_id,
    #             additional_data=additional_data_dict
    #         )

    #         # 결과 저장
    #         # TODO: 다중 사업장 캐싱 전략 재고 (site_id vs job_id)
    #         self._analysis_results[job_id] = result # Store result by job_id

    #         # 새로운 State도 캐싱 (추가 향상 가능)
    #         self._cached_states[new_job_id] = result.copy()

    #         status = "completed" if result.get('workflow_status') == 'completed' else "failed"

    #         if status == "completed":
    #             self.logger.info(
    #                 f"Enhancement completed successfully (new_job_id={new_job_id})",
    #                 extra=log_extra
    #             )
    #         else:
    #             self.logger.warning(
    #                 f"Enhancement completed with errors (new_job_id={new_job_id})",
    #                 extra={**log_extra, "errors": result.get('errors', [])}
    #             )

    #         return AnalysisJobStatus(
    #             jobId=new_job_id,
    #             siteId=site_id,
    #             status=status,
    #             progress=100 if status == "completed" else 0,
    #             currentNode="completed" if status == "completed" else "failed",
    #             startedAt=datetime.now(),
    #             completedAt=datetime.now() if status == "completed" else None,
    #             error={"code": "ENHANCEMENT_FAILED", "message": str(result.get('errors', []))} if result.get('errors') else None,
    #         )

    #     except HTTPException:
    #         # HTTPException은 그대로 전파
    #         raise

    #     except Exception as e:
    #         self.logger.error(
    #             f"Enhancement failed: {str(e)}",
    #             extra=log_extra,
    #             exc_info=True
    #         )

    #         error_detail = create_error_detail(
    #             code=ErrorCode.ENHANCEMENT_FAILED,
    #             detail=str(e),
    #             request_id=request_id,
    #             severity=ErrorSeverity.HIGH,
    #             context={"job_id": str(job_id), "site_id": str(site_id)}
    #         )

    #         return AnalysisJobStatus(
    #             jobId=new_job_id,
    #             siteId=site_id,
    #             status="failed",
    #             progress=0,
    #             currentNode="failed",
    #             startedAt=datetime.now(),
    #             error=error_detail.dict(),
    #         )

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
                jobId=job_id,
                siteId=site_id or uuid4(),
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

            # site_id 추출 (input_params에서). multi_site_analysis의 경우 첫 번째 site_id
            job_site_ids = input_params.get('site_ids') if isinstance(input_params, dict) else []
            first_site_id = UUID(job_site_ids[0]) if job_site_ids else (site_id or uuid4())

            # error_message 파싱
            error_msg = job.get('error_message')
            error_dict = None
            if error_msg:
                try:
                    error_dict = json.loads(error_msg) if isinstance(error_msg, str) else error_msg
                except:
                    error_dict = {"code": "UNKNOWN_ERROR", "message": str(error_msg)}

            # 실제 상태와 진행률 계산
            actual_status = job['status']
            actual_progress = job.get('progress', 0)
            
            if job['job_type'] == 'multi_site_analysis':
                agent_results = job.get('results')
                if agent_results and isinstance(agent_results, dict):
                    if agent_results.get('workflow_status') == 'completed':
                        actual_progress = 100
                        actual_status = 'done'
                    elif agent_results.get('workflow_status') == 'failed':
                        actual_progress = 100
                        actual_status = 'failed'

            return AnalysisJobStatus(
                jobId=job['batch_id'],
                siteId=first_site_id,
                status=actual_status,
                progress=actual_progress,
                currentNode=actual_status,
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
        """
        return await self.get_job_status(job_id)

    async def get_latest_job_status_by_user(self, user_id: UUID) -> Optional[AnalysisJobStatus]:
        """
        userId로 가장 최근 분석 작업 상태 조회 (Spring Boot 클라이언트 호환)
        """
        if settings.USE_MOCK_DATA:
             return AnalysisJobStatus(
                jobId=uuid4(),
                siteId=uuid4(),
                status="completed",
                progress=100,
                currentNode="completed",
                startedAt=datetime.now(),
                completedAt=datetime.now(),
            )

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
                WHERE created_by = %s AND (job_type = 'multi_site_analysis' OR job_type = 'physical_risk_analysis')
                ORDER BY created_at DESC
                LIMIT 1
            """
            result = self.db.execute_query(query, (str(user_id),))

            if not result or len(result) == 0:
                self.logger.warning(f"No jobs found for user {user_id}")
                return None

            job = result[0]
            input_params = job.get('input_params', {})
            
            job_site_ids = input_params.get('site_ids') if isinstance(input_params, dict) else []
            first_site_id = UUID(job_site_ids[0]) if job_site_ids else uuid4()
            
            error_msg = job.get('error_message')
            error_dict = None
            if error_msg:
                try:
                    error_dict = json.loads(error_msg) if isinstance(error_msg, str) else error_msg
                except:
                    error_dict = {"code": "UNKNOWN_ERROR", "message": str(error_msg)}

            actual_status = job['status']
            actual_progress = job.get('progress', 0)
            
            if job['job_type'] == 'multi_site_analysis':
                agent_results = job.get('results')
                if agent_results and isinstance(agent_results, dict):
                    if agent_results.get('workflow_status') == 'completed':
                        actual_progress = 100
                        actual_status = 'done'
                    elif agent_results.get('workflow_status') == 'failed':
                        actual_progress = 100
                        actual_status = 'failed'

            return AnalysisJobStatus(
                jobId=job['batch_id'],
                siteId=first_site_id,
                status=actual_status,
                progress=actual_progress,
                currentNode=actual_status,
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
            risk_type = HazardType.HIGH_TEMPERATURE
            if hazard_type:
                try:
                    risk_type = HazardType[hazard_type]
                except KeyError:
                    try:
                        risk_type = HazardType(hazard_type)
                    except ValueError:
                        pass

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

        self.logger.info(f"[PHYSICAL_RISK] 물리적 리스크 점수 조회: site_id={site_id}, hazard_type={hazard_type}")

        try:
            db = DatabaseManager()
            risk_type_en = hazard_type

            query = """
                SELECT
                    site_id, risk_type, physical_risk_score_100 as risk_score, aal_percentage, risk_level
                FROM site_risk_results
                WHERE site_id = %s
            """
            params = [str(site_id)]
            if risk_type_en:
                query += " AND risk_type = %s"
                params.append(risk_type_en)

            rows = db.execute_query(query, tuple(params))
            self.logger.info(f"[PHYSICAL_RISK] 쿼리 실행 완료: {len(rows)}개 행 조회됨")

            if not rows:
                self.logger.warning(f"[PHYSICAL_RISK] 데이터 없음: site_id={site_id}, hazard_type={hazard_type}")
                return None

            # 결과를 SSP 시나리오별로 변환 (현재 DB 스키마는 시나리오별 데이터가 없으므로 임시 생성)
            scenarios = []
            for row in rows:
                risk_score = int(row.get('risk_score', 72))
                db_risk_type = row.get('risk_type', 'extreme_heat')
                risk_type_korean = RISK_TYPE_KR_MAPPING.get(db_risk_type, db_risk_type)

                for scenario in [SSPScenario.SSP1_26, SSPScenario.SSP2_45, SSPScenario.SSP3_70, SSPScenario.SSP5_85]:
                    scenarios.append(SSPScenarioScore(
                        scenario=scenario,
                        riskType=risk_type_korean,
                        shortTerm=ShortTermScore(q1=risk_score-5, q2=risk_score, q3=risk_score+5, q4=risk_score),
                        midTerm=MidTermScore(year2026=risk_score, year2027=risk_score+2, year2028=risk_score+4, year2029=risk_score+6, year2030=risk_score+8),
                        longTerm=LongTermScore(year2020s=risk_score, year2030s=risk_score+6, year2040s=risk_score+12, year2050s=risk_score+17),
                    ))
            
            return PhysicalRiskScoreResponse(scenarios=scenarios)

        except Exception as e:
            self.logger.error(f"[PHYSICAL_RISK] 데이터 조회 실패: {str(e)}", exc_info=True)
            return None

    async def get_past_events(self, site_id: UUID) -> Optional[PastEventsResponse]:
        """Spring Boot API 호환 - 과거 재난 이력 조회"""
        # This now delegates to DisasterHistoryService, but keeping mock as a fallback
        if settings.USE_MOCK_DATA:
            disasters = [
                DisasterEvent(disasterType="폭염", year=2023, warningDays=15, severeDays=5, overallStatus="심각"),
                DisasterEvent(disasterType="태풍", year=2022, warningDays=3, severeDays=2, overallStatus="주의"),
                DisasterEvent(disasterType="홍수", year=2020, warningDays=5, severeDays=3, overallStatus="심각"),
            ]
            return PastEventsResponse(siteId=site_id, siteName="서울 본사", disasters=disasters)
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

        self.logger.info(f"[FINANCIAL_IMPACT] 재무 영향 데이터 조회 시작: site_id={site_id}")
        try:
            db = DatabaseManager()
            query = "SELECT risk_type, aal_percentage FROM site_risk_results WHERE site_id = %s ORDER BY risk_type"
            rows = db.execute_query(query, (str(site_id),))
            if not rows:
                self.logger.warning(f"[FINANCIAL_IMPACT] site_id={site_id}에 대한 AAL 데이터가 없습니다")
                return None
            
            scenario_multipliers = {
                SSPScenario.SSP1_26: 0.8, SSPScenario.SSP2_45: 1.0,
                SSPScenario.SSP3_70: 1.3, SSPScenario.SSP5_85: 1.5,
            }
            scenarios = []
            for row in rows:
                db_risk_type = row['risk_type']
                aal_pct = row['aal_percentage']
                mapped_risk_type = RISK_TYPE_KR_MAPPING.get(db_risk_type, db_risk_type)
                base_aal = aal_pct / 100.0
                for scenario_enum, multiplier in scenario_multipliers.items():
                    scenario_aal = base_aal * multiplier
                    scenarios.append(SSPScenarioImpact(
                        scenario=scenario_enum, riskType=mapped_risk_type,
                        shortTerm=ShortTermAAL(q1=scenario_aal*0.95, q2=scenario_aal*1.0, q3=scenario_aal*1.05, q4=scenario_aal*1.02),
                        midTerm=MidTermAAL(year2026=scenario_aal*1.0, year2027=scenario_aal*1.05, year2028=scenario_aal*1.1, year2029=scenario_aal*1.15, year2030=scenario_aal*1.2),
                        longTerm=LongTermAAL(year2020s=scenario_aal*1.0, year2030s=scenario_aal*1.2, year2040s=scenario_aal*1.4, year2050s=scenario_aal*1.6)
                    ))
            if not scenarios: return None
            return FinancialImpactResponse(scenarios=scenarios)
        except Exception as e:
            self.logger.error(f"[FINANCIAL_IMPACT] DB 조회 실패: {e}", exc_info=True)
            return None

    async def get_vulnerability(self, site_id: UUID) -> Optional[VulnerabilityResponse]:
        """Spring Boot API 호환 - 취약성 분석 (메모리 캐시 또는 DB 조회)"""
        # This method is now complex due to multi-site analysis storing results under a job_id
        # For simplicity, we query the DB directly assuming Phase 1 results are stored per site_id
        if settings.USE_MOCK_DATA:
            vulnerabilities = [
                RiskVulnerability(riskType="폭염", vulnerabilityScore=75),
                RiskVulnerability(riskType="태풍", vulnerabilityScore=70),
            ]
            return VulnerabilityResponse(siteId=site_id, vulnerabilities=vulnerabilities)

        self.logger.info(f"[VULNERABILITY] 취약성 데이터 조회 시작: site_id={site_id}")
        try:
            db = DatabaseManager()
            query = "SELECT risk_type, vulnerability_score FROM vulnerability_results WHERE site_id = %s ORDER BY risk_type"
            rows = db.execute_query(query, (str(site_id),))
            if not rows:
                self.logger.warning(f"[VULNERABILITY] 데이터 없음: site_id={site_id}")
                return None

            vulnerabilities = [
                RiskVulnerability(
                    riskType=RISK_TYPE_KR_MAPPING.get(row['risk_type'], row['risk_type']),
                    vulnerabilityScore=int(row.get('vulnerability_score', 0))
                ) for row in rows
            ]
            return VulnerabilityResponse(siteId=site_id, vulnerabilities=vulnerabilities)
        except Exception as e:
            self.logger.error(f"[VULNERABILITY] 취약성 데이터 조회 실패: {e}", exc_info=True)
            return None

    async def get_total_analysis(
        self, site_id: UUID, hazard_type: str
    ) -> Optional[AnalysisTotalResponse]:
        """Spring Boot API 호환 - 특정 Hazard 기준 통합 분석 결과"""
        if settings.USE_MOCK_DATA:
            return AnalysisTotalResponse(
                siteId=site_id, siteName="서울 본사",
                physicalRisks=[
                    PhysicalRiskBarItem(riskType=ht, riskScore=70, financialLossRate=0.018)
                    for ht in HazardType
                ]
            )
        return None

    async def mark_modelops_recommendation_completed(self, user_id: UUID):
        """ModelOps 서버에서 후보지 추천 완료 시 호출하는 메서드"""
        # This method's logic may need review in context of multi-site jobs
        self.logger.info(f"[MODELOPS] 후보지 추천 완료 알림 수신: user_id={user_id}")
        return

    async def get_analysis_summary(
        self,
        site_id: UUID,
        latitude: float,
        longitude: float
    ) -> AnalysisSummaryResponse:
        """
        분석 요약 조회 - 2040년 SSP2-4.5 시나리오 기준
        """
        self.logger.info(f"[SUMMARY] 분석 요약 조회: site_id={site_id}, lat={latitude}, lon={longitude}")
        try:
            db = DatabaseManager()

            # Queries for H, E, V, AAL from respective tables
            hazard_query = "SELECT risk_type, ssp245_score_100 FROM hazard_results WHERE latitude = %s AND longitude = %s AND target_year = %s"
            hazard_rows = db.execute_query(hazard_query, (latitude, longitude, TARGET_YEAR))
            hazard_data = {row['risk_type']: row for row in hazard_rows}

            exposure_query = "SELECT risk_type, exposure_score FROM exposure_results WHERE site_id = %s AND target_year = %s"
            exposure_rows = db.execute_query(exposure_query, (str(site_id), TARGET_YEAR))
            exposure_data = {row['risk_type']: row for row in exposure_rows}
            
            vulnerability_query = "SELECT risk_type, vulnerability_score FROM vulnerability_results WHERE site_id = %s AND target_year = %s"
            vulnerability_rows = db.execute_query(vulnerability_query, (str(site_id), TARGET_YEAR))
            vulnerability_data = {row['risk_type']: row for row in vulnerability_rows}

            aal_query = "SELECT risk_type, ssp245_final_aal FROM aal_scaled_results WHERE site_id = %s AND target_year = %s"
            aal_rows = db.execute_query(aal_query, (str(site_id), TARGET_YEAR))
            aal_data = {row['risk_type']: row for row in aal_rows}
            
            # Data validation and processing
            missing_risks = [rt for rt in RISK_TYPES if rt not in hazard_data or rt not in exposure_data or rt not in vulnerability_data or rt not in aal_data]
            if missing_risks:
                raise HTTPException(status_code=404, detail=f"Missing data for year {TARGET_YEAR}, SSP2 scenario. Risk types: {', '.join(missing_risks)}")

            physical_risk_scores_dict = {}
            aal_scores_dict = {}
            for risk_type in RISK_TYPES:
                H = hazard_data[risk_type]['ssp245_score_100']
                E = exposure_data[risk_type]['exposure_score']
                V = vulnerability_data[risk_type]['vulnerability_score']
                physical_risk_score = int(round((H * E * V) / 10000))
                physical_risk_scores_dict[risk_type] = physical_risk_score
                aal_scores_dict[risk_type] = float(aal_data[risk_type]['ssp245_final_aal'])

            main_risk_type = max(physical_risk_scores_dict, key=physical_risk_scores_dict.get)

            return AnalysisSummaryResponse(
                result="success",
                data=AnalysisSummaryData(
                    mainClimateRisk=RISK_TYPE_KR_MAPPING[main_risk_type],
                    mainClimateRiskScore=physical_risk_scores_dict[main_risk_type],
                    mainClimateRiskAAL=aal_scores_dict[main_risk_type],
                    **{
                        "physical-risk-scores": PhysicalRiskScores(**physical_risk_scores_dict),
                        "aal-scores": AALScores(**aal_scores_dict)
                    }
                )
            )
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"[SUMMARY] 분석 요약 조회 실패: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")
