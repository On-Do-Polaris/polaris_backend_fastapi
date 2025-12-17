from uuid import UUID, uuid4
from typing import Optional, List, Dict
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
            from ai_agent.services import get_modelops_client
            modelops_client = get_modelops_client()

            # Step 1: ModelOps API 트리거 (모든 사업장을 한 번에 처리)
            # building_info는 null로 처리 (요구사항)
            building_info = None
            asset_info = {
                'total_value': 50000000000,
                'insurance_coverage_rate': 0.3
            }

            # 모든 사업장의 위치 정보를 sites 딕셔너리로 구성
            sites_dict = {}
            for site in request.sites:
                sites_dict[str(site.id)] = {
                    'latitude': site.latitude,
                    'longitude': site.longitude
                }

            # 1-1. calculate API 호출 (동기) - 다중 사업장 병렬 처리
            self.logger.info(f"  [ModelOps] calculate API 호출: {len(sites_dict)}개 사업장")
            calculate_result = modelops_client.calculate_site_risk(
                sites=sites_dict,
                building_info=building_info,
                asset_info=asset_info
            )
            self.logger.info(f"  [ModelOps] calculate 완료: {calculate_result.get('status')}, {calculate_result.get('calculated_at')}")

            # 1-2. recommend-locations API 호출 (비동기 트리거) - 다중 사업장 병렬 처리
            # candidate_grids는 None으로 전달하여 ModelOps가 고정 위치 사용하도록 함
            self.logger.info(f"  [ModelOps] recommend-locations API 트리거: {len(sites_dict)}개 사업장, batch_id={job_id}")
            # 비동기 트리거만 하고 결과는 기다리지 않음 (요구사항)
            try:
                modelops_client.recommend_relocation_sites(
                    sites=sites_dict,
                    candidate_grids=None,  # None이면 ModelOps가 고정 위치 사용
                    building_info=building_info,
                    batch_id=str(job_id),
                    asset_info=asset_info,
                    max_candidates=3,
                    ssp_scenario="SSP245",
                    target_year=2040
                )
                self.logger.info(f"  [ModelOps] recommend-locations 트리거 완료")
            except Exception as e:
                # 비동기 트리거 실패해도 전체 프로세스는 계속 진행
                self.logger.warning(f"  [ModelOps] recommend-locations 트리거 실패: {str(e)}")

            # Step 2: Agent 호출 (기존 로직 유지)
            target_locations = []
            building_infos = []
            asset_infos = []

            for site in request.sites:
                target_locations.append({
                    'latitude': site.latitude,
                    'longitude': site.longitude,
                    'name': site.name,
                    'id': str(site.id)
                })
                building_infos.append({})  # null로 처리
                asset_infos.append({'total_asset_value': 50000000000})

            analysis_params = {
                'time_horizon': '2050',
                'analysis_period': '2025-2050'
            }

            agent_result = await self._run_agent_multiple_analysis_wrapper(
                target_locations=target_locations,
                building_infos=building_infos,
                asset_infos=asset_infos,
                analysis_params=analysis_params,
                user_id=request.user_id,
                hazard_types=request.hazard_types,
                priority=request.priority,
                options=request.options,
            )

            error = {"code": "ANALYSIS_FAILED", "message": str(agent_result.get('errors', []))} if agent_result and agent_result.get('errors') else None

            self._analysis_results[job_id] = agent_result
            self._cached_states[job_id] = agent_result.copy()

            # Agent 완료 플래그 설정
            self._update_job_flags_in_db(
                job_id=job_id,
                agent_completed=True,
                error=error
            )

            # 두 플래그 모두 True인지 체크 (Agent AND ModelOps Recommendation)
            if self._check_both_completed(job_id):
                # 둘 다 완료되면 status='done' 설정
                self._update_job_in_db(job_id, status='done', progress=100, results=agent_result, error=error)
                self.logger.info(f"[BACKGROUND] 모든 작업 완료 (Agent + Recommendation): job_id={job_id}")
            else:
                # Agent만 완료, Recommendation 대기 중
                self._update_job_in_db(job_id, status='ing', progress=90, results=agent_result, error=error)
                self.logger.info(f"[BACKGROUND] Agent 완료, Recommendation 대기 중: job_id={job_id}")

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
                        # use_additional_data가 true이면 'done-a', 아니면 'done'
                        use_additional_data = agent_results.get('use_additional_data', False)
                        actual_status = 'done-a' if use_additional_data else 'done'
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

            # --- [수정된 부분 시작] ---
            # 조회된 결과가 없으면 가상의 완료 상태(done)를 반환
            if not result or len(result) == 0:
                self.logger.info(f"No jobs found for user {user_id}, returning default DONE status")
                return AnalysisJobStatus(
                    jobId=uuid4(),          # 임시 ID 생성
                    siteId=uuid4(),         # 임시 ID 생성
                    status="done",          # 요청하신 대로 'done' 설정
                    progress=100,           # 완료되었으므로 100
                    currentNode="done",     # 완료 상태 표시
                    currentHazard=None,
                    startedAt=datetime.now(),
                    completedAt=datetime.now(),
                    estimatedCompletionTime=None,
                    error=None
                )
            # --- [수정된 부분 끝] ---

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
                        # use_additional_data가 true이면 'done-a', 아니면 'done'
                        use_additional_data = agent_results.get('use_additional_data', False)
                        actual_status = 'done-a' if use_additional_data else 'done'
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
        self, site_id: UUID, hazard_type: Optional[str], term: Optional[str] = None
    ) -> Optional[PhysicalRiskScoreResponse]:
        """
        Spring Boot API 호환 - 시나리오별 물리적 리스크 점수 조회

        Args:
            site_id: 사업장 ID
            hazard_type: 위험 유형 (선택)
            term: 분석 기간 (short/mid/long) (선택)
        """
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

        self.logger.info(f"[PHYSICAL_RISK] 물리적 리스크 점수 조회: site_id={site_id}, hazard_type={hazard_type}, term={term}")

        try:
            db = DatabaseManager()

            # term에 따라 조회할 연도 결정 (DB에는 varchar로 저장)
            # 단기(short): '2026' (1개)
            # 중기(mid): '2026', '2027', '2028', '2029', '2030' (5개)
            # 장기(long): '2020s', '2030s', '2040s', '2050s' (4개)
            target_years = []
            if term == 'short':
                target_years = ['2026']
            elif term == 'mid':
                target_years = ['2026', '2027', '2028', '2029', '2030']
            elif term == 'long':
                target_years = ['2020s', '2030s', '2040s', '2050s']
            else:
                # term이 없거나 잘못된 경우 모든 연도 조회
                target_years = ['2026', '2027', '2028', '2029', '2030', '2020s', '2030s', '2040s', '2050s']

            # H × E × V / 10000 계산을 위해 3개 테이블 JOIN
            query = """
                SELECT
                    h.risk_type,
                    h.target_year,
                    h.ssp126_score_100 as h_ssp126,
                    h.ssp245_score_100 as h_ssp245,
                    h.ssp370_score_100 as h_ssp370,
                    h.ssp585_score_100 as h_ssp585,
                    e.exposure_score,
                    v.vulnerability_score
                FROM hazard_results h
                JOIN exposure_results e ON
                    h.latitude = e.latitude AND
                    h.longitude = e.longitude AND
                    h.risk_type = e.risk_type AND
                    h.target_year = e.target_year
                JOIN vulnerability_results v ON
                    e.site_id = v.site_id AND
                    e.risk_type = v.risk_type AND
                    e.target_year = v.target_year
                WHERE e.site_id = %s
                    AND h.target_year = ANY(%s)
            """
            params = [str(site_id), target_years]

            if hazard_type:
                query += " AND h.risk_type = %s"
                params.append(hazard_type)

            query += " ORDER BY h.risk_type, h.target_year"

            rows = db.execute_query(query, tuple(params))
            self.logger.info(f"[PHYSICAL_RISK] 쿼리 실행 완료: {len(rows)}개 행 조회됨")

            if not rows:
                self.logger.warning(f"[PHYSICAL_RISK] 데이터 없음: site_id={site_id}, hazard_type={hazard_type}, term={term}")
                return None

            # [수정 1] risk_type별 데이터 구조화 (값 하나가 아닌 dict 저장)
            risk_data = {}
            for row in rows:
                risk_type = row['risk_type']
                target_year = row['target_year']

                if risk_type not in risk_data:
                    risk_data[risk_type] = {}

                # 공통 Exposure, Vulnerability
                E = row['exposure_score'] or 0
                V = row['vulnerability_score'] or 0

                # 각 시나리오별 H 값 추출 및 Total 계산 함수
                def calc_score(h_val):
                    h_val = h_val or 0
                    return {
                        "total": (h_val * E * V) / 10000,
                        "h": h_val,
                        "e": E,
                        "v": V
                    }

                risk_data[risk_type][target_year] = {
                    'ssp126': calc_score(row['h_ssp126']),
                    'ssp245': calc_score(row['h_ssp245']),
                    'ssp370': calc_score(row['h_ssp370']),
                    'ssp585': calc_score(row['h_ssp585']),
                }

            # SSP 시나리오별로 결과 생성
            scenarios = []

            empty_score = {"total": 0, "h": 0, "e": 0, "v": 0}
            
            for risk_type, year_data in risk_data.items():
                risk_type_korean = RISK_TYPE_KR_MAPPING.get(risk_type, risk_type)

                for scenario_enum, scenario_key in [
                    (SSPScenario.SSP1_26, 'ssp126'),
                    (SSPScenario.SSP2_45, 'ssp245'),
                    (SSPScenario.SSP3_70, 'ssp370'),
                    (SSPScenario.SSP5_85, 'ssp585')
                ]:
                    # 단기: 2026년 데이터
                    short_score = {
                        'point1': year_data.get('2026', {}).get(scenario_key, empty_score)
                    }

                    # 중기: 2026-2030년 데이터
                    mid_scores = {
                        'point1': year_data.get('2026', {}).get(scenario_key, empty_score),
                        'point2': year_data.get('2027', {}).get(scenario_key, empty_score),
                        'point3': year_data.get('2028', {}).get(scenario_key, empty_score),
                        'point4': year_data.get('2029', {}).get(scenario_key, empty_score),
                        'point5': year_data.get('2030', {}).get(scenario_key, empty_score),
                    }

                    # 장기: 2020s, 2030s, 2040s, 2050s
                    long_scores = {
                        'point1': year_data.get('2020s', {}).get(scenario_key, empty_score),
                        'point2': year_data.get('2030s', {}).get(scenario_key, empty_score),
                        'point3': year_data.get('2040s', {}).get(scenario_key, empty_score),
                        'point4': year_data.get('2050s', {}).get(scenario_key, empty_score),
                    }

                    scenarios.append(SSPScenarioScore(
                        scenario=scenario_enum,
                        riskType=risk_type_korean,
                        shortTerm=ShortTermScore(**short_score),
                        midTerm=MidTermScore(**mid_scores),
                        longTerm=LongTermScore(**long_scores),
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

    async def get_financial_impacts(
        self, site_id: UUID, hazard_type: Optional[str] = None, term: Optional[str] = None
    ) -> Optional[FinancialImpactResponse]:
        """
        Spring Boot API 호환 - 시나리오별 재무 영향(AAL) 조회

        Args:
            site_id: 사업장 ID
            hazard_type: 위험 유형 (선택)
            term: 분석 기간 (short/mid/long) (선택)
        """
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

        self.logger.info(f"[FINANCIAL_IMPACT] 재무 영향 데이터 조회 시작: site_id={site_id}, hazard_type={hazard_type}, term={term}")
        try:
            db = DatabaseManager()

            # term에 따라 조회할 연도 결정 (DB에는 varchar로 저장)
            # 단기(short): '2026' (1개)
            # 중기(mid): '2026', '2027', '2028', '2029', '2030' (5개)
            # 장기(long): '2020s', '2030s', '2040s', '2050s' (4개)
            target_years = []
            if term == 'short':
                target_years = ['2026']
            elif term == 'mid':
                target_years = ['2026', '2027', '2028', '2029', '2030']
            elif term == 'long':
                target_years = ['2020s', '2030s', '2040s', '2050s']
            else:
                # term이 없거나 잘못된 경우 모든 연도 조회
                target_years = ['2026', '2027', '2028', '2029', '2030', '2020s', '2030s', '2040s', '2050s']

            # aal_scaled_results 테이블에서 직접 AAL 조회
            query = """
                SELECT
                    risk_type,
                    target_year,
                    ssp126_final_aal,
                    ssp245_final_aal,
                    ssp370_final_aal,
                    ssp585_final_aal
                FROM aal_scaled_results
                WHERE site_id = %s
                    AND target_year = ANY(%s)
            """
            params = [str(site_id), target_years]

            if hazard_type:
                query += " AND risk_type = %s"
                params.append(hazard_type)

            query += " ORDER BY risk_type, target_year"

            rows = db.execute_query(query, tuple(params))
            self.logger.info(f"[FINANCIAL_IMPACT] 쿼리 실행 완료: {len(rows)}개 행 조회됨")

            if not rows:
                self.logger.warning(f"[FINANCIAL_IMPACT] site_id={site_id}에 대한 AAL 데이터가 없습니다")
                return None

            # risk_type별로 그룹화
            aal_data = {}
            for row in rows:
                risk_type = row['risk_type']
                target_year = row['target_year']

                if risk_type not in aal_data:
                    aal_data[risk_type] = {}

                aal_data[risk_type][target_year] = {
                    'ssp126': row['ssp126_final_aal'] if row['ssp126_final_aal'] else 0,
                    'ssp245': row['ssp245_final_aal'] if row['ssp245_final_aal'] else 0,
                    'ssp370': row['ssp370_final_aal'] if row['ssp370_final_aal'] else 0,
                    'ssp585': row['ssp585_final_aal'] if row['ssp585_final_aal'] else 0,
                }

            # SSP 시나리오별로 결과 생성
            scenarios = []
            for risk_type, year_data in aal_data.items():
                risk_type_korean = RISK_TYPE_KR_MAPPING.get(risk_type, risk_type)

                for scenario_enum, scenario_key in [
                    (SSPScenario.SSP1_26, 'ssp126'),
                    (SSPScenario.SSP2_45, 'ssp245'),
                    (SSPScenario.SSP3_70, 'ssp370'),
                    (SSPScenario.SSP5_85, 'ssp585')
                ]:
                    # 단기: 2026년 데이터를 4분기로 분할 (동일한 값)
                    short_aal = {
                        'point1': year_data.get('2026', {}).get(scenario_key, 0),
                    }
                    # 중기: 2026-2030년 데이터
                    mid_aal = {
                        'point1': year_data.get('2026', {}).get(scenario_key, 0),
                        'point2': year_data.get('2027', {}).get(scenario_key, 0),
                        'point3': year_data.get('2028', {}).get(scenario_key, 0),
                        'point4': year_data.get('2029', {}).get(scenario_key, 0),
                        'point5': year_data.get('2030', {}).get(scenario_key, 0),
                    }

                    # 장기: 2020s, 2030s, 2040s, 2050s
                    long_aal ={
                        'point1': year_data.get('2020s', {}).get(scenario_key, 0),
                        'point2': year_data.get('2030s', {}).get(scenario_key, 0),
                        'point3': year_data.get('2040s', {}).get(scenario_key, 0),
                        'point4': year_data.get('2050s', {}).get(scenario_key, 0),
                    }

                    scenarios.append(SSPScenarioImpact(
                        scenario=scenario_enum,
                        riskType=risk_type_korean,
                        shortTerm=ShortTermAAL(**short_aal),
                        midTerm=MidTermAAL(**mid_aal),
                        longTerm=LongTermAAL(**long_aal),
                    ))

            if not scenarios:
                return None
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

    def _update_job_flags_in_db(
        self,
        job_id: UUID,
        agent_completed: Optional[bool] = None,
        modelops_recommendation_completed: Optional[bool] = None,
        error: Optional[dict] = None
    ):
        """batch_jobs 테이블의 완료 플래그 업데이트"""
        if not self.db:
            return

        updates = []
        params = []

        if agent_completed is not None:
            updates.append("agent_completed = %s")
            params.append(agent_completed)

        if modelops_recommendation_completed is not None:
            updates.append("modelops_recommendation_completed = %s")
            params.append(modelops_recommendation_completed)

        if error:
            updates.append("error_message = %s")
            params.append(json.dumps(error))

        if not updates:
            return

        params.append(str(job_id))

        query = f"""
            UPDATE batch_jobs
            SET {', '.join(updates)}
            WHERE batch_id = %s
        """
        try:
            self.db.execute_update(query, tuple(params))
            self.logger.info(f"Job flags updated: job_id={job_id}, agent_completed={agent_completed}, modelops_recommendation_completed={modelops_recommendation_completed}")
        except Exception as e:
            self.logger.error(f"Failed to update job flags: {e}")

    def _check_both_completed(self, job_id: UUID) -> bool:
        """Agent와 ModelOps 둘 다 완료되었는지 체크"""
        if not self.db:
            return False

        query = """
            SELECT agent_completed, modelops_recommendation_completed
            FROM batch_jobs
            WHERE batch_id = %s
        """
        try:
            result = self.db.execute_query(query, (str(job_id),))

            if not result:
                return False

            row = result[0]
            both_completed = row['agent_completed'] and row['modelops_recommendation_completed']
            self.logger.debug(f"Both completed check: job_id={job_id}, agent={row['agent_completed']}, modelops={row['modelops_recommendation_completed']}, result={both_completed}")
            return both_completed
        except Exception as e:
            self.logger.error(f"Failed to check completion flags: {e}")
            return False

    def _get_latest_job_by_user_and_status(self, user_id: UUID, status: str) -> Optional[dict]:
        """user_id와 status로 가장 최근 job 조회"""
        if not self.db:
            return None

        query = """
            SELECT * FROM batch_jobs
            WHERE created_by = %s AND status = %s
            ORDER BY created_at DESC
            LIMIT 1
        """
        try:
            result = self.db.execute_query(query, (str(user_id), status))
            return result[0] if result else None
        except Exception as e:
            self.logger.error(f"Failed to get latest job: {e}")
            return None

    async def mark_modelops_recommendation_completed(self, batch_id: UUID):
        """ModelOps 서버에서 후보지 추천 완료 시 호출하는 메서드"""
        self.logger.info(f"[MODELOPS] 후보지 추천 완료 알림 수신: batch_id={batch_id}")

        # batch_id로 job 조회
        if not self.db:
            self.logger.error("[MODELOPS] DB 연결 없음")
            return

        query = """
            SELECT * FROM batch_jobs
            WHERE batch_id = %s
        """
        try:
            result = self.db.execute_query(query, (str(batch_id),))
            if not result:
                self.logger.warning(f"[MODELOPS] batch_id={batch_id}에 해당하는 작업이 없습니다.")
                return

            job = result[0]
        except Exception as e:
            self.logger.error(f"[MODELOPS] Job 조회 실패: {e}")
            return

        # Recommendation 완료 플래그 설정
        self._update_job_flags_in_db(
            job_id=batch_id,
            modelops_recommendation_completed=True
        )

        # 두 플래그 모두 True인지 체크
        if self._check_both_completed(batch_id):
            # results 조회 (agent_result)
            results = job.get('results')
            self._update_job_in_db(batch_id, status='done', progress=100, results=results)
            self.logger.info(f"[MODELOPS] 모든 작업 완료: batch_id={batch_id}")

            # Spring Boot API 호출 (userId 전송)
            try:
                # created_by에서 userId 추출
                user_id = job.get('created_by')

                if user_id:
                    from ai_agent.services import get_springboot_client
                    springboot_client = get_springboot_client()

                    self.logger.info(f"[MODELOPS] Spring Boot API 호출: user_id={user_id}")
                    springboot_client.notify_analysis_completion(user_id)
                    self.logger.info(f"[MODELOPS] Spring Boot API 호출 성공")
                else:
                    self.logger.warning(f"[MODELOPS] user_id가 없습니다: batch_id={batch_id}")
            except Exception as e:
                self.logger.error(f"[MODELOPS] Spring Boot API 호출 실패: {e}", exc_info=True)
                # API 호출 실패해도 전체 프로세스는 계속 진행
        else:
            self.logger.info(f"[MODELOPS] Recommendation 완료, Agent 대기 중: batch_id={batch_id}")

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
            hazard_rows = db.execute_query(hazard_query, (latitude, longitude, str(TARGET_YEAR)))
            hazard_data = {row['risk_type']: row for row in hazard_rows}

            exposure_query = "SELECT risk_type, exposure_score FROM exposure_results WHERE site_id = %s AND target_year = %s"
            exposure_rows = db.execute_query(exposure_query, (str(site_id), str(TARGET_YEAR)))
            exposure_data = {row['risk_type']: row for row in exposure_rows}
            
            vulnerability_query = "SELECT risk_type, vulnerability_score FROM vulnerability_results WHERE site_id = %s AND target_year = %s"
            vulnerability_rows = db.execute_query(vulnerability_query, (str(site_id), str(TARGET_YEAR)))
            vulnerability_data = {row['risk_type']: row for row in vulnerability_rows}

            aal_query = "SELECT risk_type, ssp245_final_aal FROM aal_scaled_results WHERE site_id = %s AND target_year = %s"
            aal_rows = db.execute_query(aal_query, (str(site_id), str(TARGET_YEAR)))
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
