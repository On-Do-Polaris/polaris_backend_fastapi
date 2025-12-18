from uuid import UUID, uuid4
from typing import Optional, List, Dict
from datetime import datetime
from fastapi import HTTPException
import logging
import json
import asyncio
import os

from src.core.config import settings
from src.core.errors import ErrorCode, ErrorSeverity, create_error_detail
from src.schemas.analysis import (
    StartAnalysisRequest,
    AnalysisJobStatus,
    PhysicalRiskScoreResponse,
    PastEventsResponse,
    FinancialImpactResponse,
    VulnerabilityResponse,
    VulnerabilityData,
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

# 역매핑: 한글 → 영어 (프론트엔드 요청 처리용)
RISK_TYPE_EN_MAPPING = {v: k for k, v in RISK_TYPE_KR_MAPPING.items()}

# 추가 한글 별칭 매핑 (프론트엔드 호환성)
RISK_TYPE_ALIAS_MAPPING = {
    '극심한 고온': 'extreme_heat',
    '극심한 저온': 'extreme_cold',
    '극심한 한파': 'extreme_cold',
    '극한 고온': 'extreme_heat',
    '극한 저온': 'extreme_cold',
    '극한 한파': 'extreme_cold',
    '고온': 'extreme_heat',
    '저온': 'extreme_cold',
    '하천 홍수': 'river_flood',
    '내륙 홍수': 'river_flood',
    '도시 홍수': 'urban_flood',
    '해수면 상승': 'sea_level_rise',
    '해안 침수': 'sea_level_rise',
    '물 부족': 'water_stress',
}

# RISK_TYPE_EN_MAPPING에 별칭 추가
RISK_TYPE_EN_MAPPING.update(RISK_TYPE_ALIAS_MAPPING)

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
        self._running_tasks = {}  # job_id별 실행 중인 asyncio.Task 추적
        self._cancellation_flags = {}  # job_id별 취소 플래그
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

    def _cleanup_task(self, job_id: UUID):
        """Task 완료 시 자동 정리"""
        if job_id in self._running_tasks:
            del self._running_tasks[job_id]
        if job_id in self._cancellation_flags:
            del self._cancellation_flags[job_id]
        self.logger.info(f"[CLEANUP] Task 정리 완료: job_id={job_id}")

    def _check_cancellation(self, job_id: UUID) -> bool:
        """취소 요청 확인"""
        return self._cancellation_flags.get(job_id, False)

    async def cancel_analysis(self, job_id: UUID) -> dict:
        """
        실행 중인 분석 작업 강제 중단

        Args:
            job_id: 중단할 작업의 ID

        Returns:
            dict: 취소 결과 (success, message)
        """
        self.logger.info(f"[CANCEL] 분석 작업 취소 요청: job_id={job_id}")

        # 실행 중인 Task 확인
        task = self._running_tasks.get(job_id)
        if not task:
            self.logger.warning(f"[CANCEL] 실행 중인 작업을 찾을 수 없음: job_id={job_id}")
            return {
                "success": False,
                "message": f"실행 중인 작업을 찾을 수 없습니다. (job_id: {job_id})"
            }

        # 취소 플래그 설정
        self._cancellation_flags[job_id] = True

        # Task 취소
        task.cancel()

        # DB 상태 업데이트
        try:
            self._save_job_to_db(
                job_id=job_id,
                user_id=None,
                site_infos=[],
                hazard_types=[],
                priority=Priority.NORMAL,
                options=None,
                status="done",
                progress=0,
                results={"message": "사용자에 의해 취소됨"}
            )
        except Exception as e:
            self.logger.error(f"[CANCEL] DB 상태 업데이트 실패: {e}")

        self.logger.info(f"[CANCEL] 작업 취소 완료: job_id={job_id}")
        return {
            "success": True,
            "message": f"분석 작업이 성공적으로 취소되었습니다. (job_id: {job_id})"
        }

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
            if status == 'done':
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
        # asyncio.Task로 래핑하여 취소 가능하도록 함
        task = asyncio.create_task(self._run_multi_analysis_background(job_id, request))
        self._running_tasks[job_id] = task
        self._cancellation_flags[job_id] = False

        # Task 완료 시 자동 정리를 위한 콜백
        task.add_done_callback(lambda t: self._cleanup_task(job_id))

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

            # ModelOps에 보낼 연도 리스트 생성 (2021~2100 + 장기년도)
            target_years_for_modelops = [str(year) for year in range(2021, 2101)]  # 2021~2100
            target_years_for_modelops.extend(['2020s', '2030s', '2040s', '2050s'])  # 장기년도 추가
            self.logger.info(f"  [ModelOps] target_years 생성 완료: {len(target_years_for_modelops)}개 연도 (2021-2100 + 장기년도)")

            # 1-1. calculate API 호출 (비동기 트리거)
            # 몇 시간 걸릴 수 있으므로 트리거만 하고 결과를 기다리지 않음
            # TCFD Agent가 DB에서 데이터를 체크하면서 대기
            self.logger.info(f"  [ModelOps] calculate API 트리거: {len(sites_dict)}개 사업장, {len(target_years_for_modelops)}개 연도")
            try:
                calculate_result = modelops_client.calculate_site_risk(
                    sites=sites_dict,
                    building_info=building_info,
                    asset_info=asset_info,
                    target_years=target_years_for_modelops
                )
                self.logger.info(f"  [ModelOps] calculate 트리거 완료: {calculate_result.get('status')}")
            except Exception as e:
                # 트리거 실패해도 Agent는 계속 진행 (DB 체크 로직이 있음)
                self.logger.warning(f"  [ModelOps] calculate 트리거 실패: {str(e)}")

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

                # Spring Boot API 호출 (userId 전송)
                # request.user_id가 None일 수 있으므로 DB에서 조회
                user_id_to_notify = request.user_id
                if user_id_to_notify is None:
                    # DB에서 created_by 조회
                    try:
                        query = "SELECT created_by FROM batch_jobs WHERE batch_id = %s"
                        result = self.db.execute_query(query, (str(job_id),))
                        if result and result[0].get('created_by'):
                            user_id_to_notify = UUID(result[0]['created_by'])
                            self.logger.info(f"[BACKGROUND] DB에서 user_id 조회 성공: {user_id_to_notify}")
                    except Exception as e:
                        self.logger.warning(f"[BACKGROUND] DB에서 user_id 조회 실패: {e}")

                await self._notify_springboot_completion(job_id, user_id_to_notify)
            else:
                # Agent만 완료, Recommendation 대기 중
                self._update_job_in_db(job_id, status='ing', progress=90, results=agent_result, error=error)
                self.logger.info(f"[BACKGROUND] Agent 완료, Recommendation 대기 중: job_id={job_id}")

        except Exception as e:
            self.logger.error(f"[BACKGROUND] 다중 사업장 분석 실패: job_id={job_id}, error={str(e)}", exc_info=True)
            error = {"code": "ANALYSIS_FAILED", "message": str(e)}
            self._update_job_in_db(job_id, status='done', progress=100, error=error)

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
        TCFD Report Workflow 실행 (백그라운드, 비동기)

        이 메서드는 _run_multi_analysis_background 내에서 호출되며,
        이미 백그라운드 태스크로 실행 중입니다.
        """
        try:
            from ai_agent.agents.tcfd_report.workflow import create_tcfd_workflow
            from ai_agent.agents.tcfd_report.state import TCFDReportState
            from langchain_openai import ChatOpenAI
            from qdrant_client import QdrantClient
            import os

            self.logger.info(f"[TCFD] 워크플로우 시작: {len(target_locations)}개 사업장")

            # site_ids 추출
            site_ids = [loc['id'] for loc in target_locations]

            # 의존성 초기화
            # API 키에서 개행 문자 제거 (환경변수 파일에서 개행이 포함될 수 있음)
            openai_api_key = os.environ.get('OPENAI_API_KEY', '').strip()
            llm = ChatOpenAI(
                model="gpt-4o",
                temperature=0.7,
                api_key=openai_api_key
            )

            # Qdrant 클라이언트 (없으면 None으로 전달)
            try:
                # QDRANT_STORAGE 환경변수 확인
                qdrant_storage = os.environ.get('QDRANT_STORAGE')

                if qdrant_storage:
                    # QDRANT_STORAGE가 있으면 path 파라미터로 전달
                    qdrant_url = os.environ.get('QDRANT_HOST', 'http://localhost:6333')
                    self.logger.info(f"[TCFD] Using QDRANT_STORAGE path: {qdrant_storage}")
                    qdrant_client = QdrantClient(url=qdrant_url, path=qdrant_storage)
                else:
                    # 기존 방식: host와 port 사용
                    qdrant_client = QdrantClient(
                        host=os.environ.get('QDRANT_HOST', 'localhost'),
                        port=int(os.environ.get('QDRANT_PORT', 6333))
                    )
            except Exception as e:
                self.logger.warning(f"[TCFD] Qdrant 연결 실패 (RAG 비활성화): {e}")
                qdrant_client = None

            # Application DB 연결 (TCFD 리포트 저장용)
            from ai_agent.utils.database import DatabaseManager
            app_db = DatabaseManager(
                db_host=os.environ.get('APPLICATION_DB_HOST'),
                db_port=os.environ.get('APPLICATION_DB_PORT', '5432'),
                db_name=os.environ.get('APPLICATION_DB_NAME'),
                db_user=os.environ.get('APPLICATION_DB_USER'),
                db_password=os.environ.get('APPLICATION_DB_PASSWORD')
            )

            # 초기 상태 설정
            initial_state: TCFDReportState = {
                "site_ids": site_ids,
                "user_id": str(user_id) if user_id else None,
                # target_years는 Node 0에서 자동 설정 (2026~2030 + 2020s~2050s)
                "errors": [],
                "current_step": "initialized"
            }

            # 워크플로우 생성 (Application DB 전달)
            workflow = create_tcfd_workflow(app_db, llm, qdrant_client)

            # 워크플로우 실행 (비동기 호출)
            # 모든 노드가 async 함수이므로 ainvoke 사용
            self.logger.info(f"[TCFD] 워크플로우 실행 중...")
            final_state = await workflow.ainvoke(initial_state)

            # 결과 확인
            if final_state.get('errors'):
                self.logger.error(f"[TCFD] 워크플로우 오류: {final_state['errors']}")
                return {
                    'workflow_status': 'failed',
                    'errors': final_state['errors']
                }

            report_id = final_state.get('report_id')
            success = final_state.get('success', False)
            self.logger.info(f"[TCFD] 워크플로우 완료: report_id={report_id}, success={success}")

            return {
                'workflow_status': 'completed',
                'report_id': report_id,
                'success': success,
                'final_state': final_state
            }

        except Exception as e:
            self.logger.error(f"[TCFD] 워크플로우 실행 실패: {e}", exc_info=True)
            return {
                'workflow_status': 'failed',
                'errors': [str(e)]
            }


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
                        actual_status = 'done'

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
                        actual_status = 'done'

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

            # hazard_type이 한글인 경우 영어로 변환 (프론트엔드 호환성)
            risk_type_en = None
            if hazard_type:
                # 한글인지 영어인지 확인
                if hazard_type in RISK_TYPE_EN_MAPPING:
                    risk_type_en = RISK_TYPE_EN_MAPPING[hazard_type]
                    self.logger.info(f"[PHYSICAL_RISK] hazard_type 변환: '{hazard_type}' → '{risk_type_en}'")
                elif hazard_type in RISK_TYPE_KR_MAPPING:
                    risk_type_en = hazard_type  # 이미 영어
                else:
                    self.logger.warning(f"[PHYSICAL_RISK] 알 수 없는 hazard_type: {hazard_type}")
                    risk_type_en = hazard_type  # 그대로 사용

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
            # exposure_results에서 위경도를 가져와서 hazard_results에서 최근접 검색
            # 먼저 exposure_results에서 site_id의 위경도를 조회
            location_query = """
                SELECT DISTINCT latitude, longitude
                FROM exposure_results
                WHERE site_id = %s
                LIMIT 1
            """
            location_result = db.execute_query(location_query, (str(site_id),))

            if not location_result:
                self.logger.warning(f"[PHYSICAL_RISK] site_id={site_id}에 대한 위경도 정보가 없습니다")
                return None

            site_latitude = location_result[0]['latitude']
            site_longitude = location_result[0]['longitude']

            # DISTINCT ON을 사용하여 각 (risk_type, target_year) 조합에서 최근접 hazard 값을 찾음
            query = """
                SELECT DISTINCT ON (h.risk_type, h.target_year)
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
                    e.site_id = %s AND
                    h.risk_type = e.risk_type AND
                    h.target_year = e.target_year
                JOIN vulnerability_results v ON
                    e.site_id = v.site_id AND
                    e.risk_type = v.risk_type AND
                    e.target_year = v.target_year
                WHERE h.target_year = ANY(%s)
            """
            params = [str(site_id), target_years]

            if risk_type_en:
                query += " AND h.risk_type = %s"
                params.append(risk_type_en)

            query += """
                ORDER BY h.risk_type, h.target_year, (
                    POW(h.latitude - %s, 2) + POW(h.longitude - %s, 2)
                ) ASC
            """
            params.extend([site_latitude, site_longitude])

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
                    # H 값이 None이면 1로 처리
                    h_val = h_val if h_val is not None else 1
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

            # hazard_type이 한글인 경우 영어로 변환 (프론트엔드 호환성)
            risk_type_en = None
            if hazard_type:
                # 한글인지 영어인지 확인
                if hazard_type in RISK_TYPE_EN_MAPPING:
                    risk_type_en = RISK_TYPE_EN_MAPPING[hazard_type]
                    self.logger.info(f"[FINANCIAL_IMPACT] hazard_type 변환: '{hazard_type}' → '{risk_type_en}'")
                elif hazard_type in RISK_TYPE_KR_MAPPING:
                    risk_type_en = hazard_type  # 이미 영어
                else:
                    self.logger.warning(f"[FINANCIAL_IMPACT] 알 수 없는 hazard_type: {hazard_type}")
                    risk_type_en = hazard_type  # 그대로 사용

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

            if risk_type_en:
                query += " AND risk_type = %s"
                params.append(risk_type_en)

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
        """
        Spring Boot API 호환 - 취약성 분석

        Application DB의 sites 테이블에서 주소를 가져오고,
        Datawarehouse DB의 building_aggregate_cache 테이블에서 건물 정보를 가져옴.
        AI 요약은 workflow state의 building_data에서 조회.
        """
        if settings.USE_MOCK_DATA:
            mock_data = VulnerabilityData(
                siteId=site_id,
                latitude=37.36633726,
                longitude=127.10661717,
                area=1228.5,
                grndflrCnt=5,
                ugrnFlrCnt=1,
                rserthqkDsgnApplyYn="Y",
                aisummry="해당 건물은 내진 설계가 되어 있어 지진에 대한 리스크가 낮습니다."
            )
            return VulnerabilityResponse(result="success", data=mock_data)

        self.logger.info(f"[VULNERABILITY] 건물 특성 분석 데이터 조회 시작: site_id={site_id}")

        try:
            # 1. Application DB에서 site 정보 조회 (주소 정보)
            app_db = DatabaseManager(
                db_host=os.environ.get('APPLICATION_DB_HOST'),
                db_port=os.environ.get('APPLICATION_DB_PORT', '5432'),
                db_name=os.environ.get('APPLICATION_DB_NAME'),
                db_user=os.environ.get('APPLICATION_DB_USER'),
                db_password=os.environ.get('APPLICATION_DB_PASSWORD')
            )

            site_query = """
                SELECT
                    id,
                    name,
                    road_address,
                    jibun_address,
                    latitude,
                    longitude
                FROM sites
                WHERE id = %s
            """
            site_result = app_db.execute_query(site_query, (str(site_id),))

            if not site_result:
                self.logger.warning(f"[VULNERABILITY] site_id={site_id}에 대한 사업장 정보가 없습니다")
                return None

            site_info = site_result[0]
            latitude = site_info.get('latitude')
            longitude = site_info.get('longitude')
            road_address = site_info.get('road_address')
            jibun_address = site_info.get('jibun_address')

            self.logger.info(f"[VULNERABILITY] site 정보 조회 완료: road_address={road_address}, jibun_address={jibun_address}")

            dw_db = DatabaseManager()  # Datawarehouse DB (기본 설정)

            # 2. building_aggregate_cache 조회 (우선순위: cache_id → 주소 코드)
            building_result = None

            # 2-1. cache_id = site_id로 직접 조회 시도 (최우선)
            cache_id_query = """
                SELECT
                    jibun_address,
                    road_address,
                    building_count,
                    structure_types,
                    purpose_types,
                    max_ground_floors,
                    max_underground_floors,
                    min_underground_floors,
                    buildings_with_seismic,
                    buildings_without_seismic,
                    oldest_approval_date,
                    newest_approval_date,
                    oldest_building_age_years,
                    total_floor_area_sqm,
                    total_building_area_sqm
                FROM building_aggregate_cache
                WHERE cache_id = %s
            """
            building_result = dw_db.execute_query(cache_id_query, (str(site_id),))

            if building_result:
                self.logger.info(f"[VULNERABILITY] cache_id로 건물 정보 조회 성공: site_id={site_id}")
                building_info = building_result[0]
            else:
                # 2-2. Fallback: 주소 코드 기반 조회 (기존 방식)
                self.logger.info(f"[VULNERABILITY] cache_id 조회 실패, 주소 기반 조회로 fallback")

                # VWorld Geocode 캐시에서 주소 정보 조회 (위경도 기반)
                geocode_query = """
                    SELECT
                        sigungu_cd,
                        bjdong_cd,
                        bun,
                        ji,
                        parcel_address,
                        road_address
                    FROM api_vworld_geocode
                    WHERE latitude = %s AND longitude = %s
                    LIMIT 1
                """
                geocode_result = dw_db.execute_query(geocode_query, (latitude, longitude))

                if not geocode_result:
                    self.logger.warning(f"[VULNERABILITY] 위경도({latitude}, {longitude})에 대한 geocode 정보가 없습니다")
                    # 주소가 없으면 AI 요약만 반환
                    aisummry = self._get_ai_summary_from_state(site_id)
                    return VulnerabilityResponse(
                        result="success",
                        data=VulnerabilityData(
                            siteId=site_id,
                            latitude=latitude,
                            longitude=longitude,
                            area=None,
                            grndflrCnt=None,
                            ugrnFlrCnt=None,
                            rserthqkDsgnApplyYn=None,
                            aisummry=aisummry
                        )
                    )

                geocode_info = geocode_result[0]
                sigungu_cd = geocode_info.get('sigungu_cd')
                bjdong_cd = geocode_info.get('bjdong_cd')
                bun = geocode_info.get('bun')
                ji = geocode_info.get('ji')

                self.logger.info(f"[VULNERABILITY] geocode 정보 조회 완료: sigungu_cd={sigungu_cd}, bjdong_cd={bjdong_cd}, bun={bun}, ji={ji}")

                # 3. building_aggregate_cache 테이블에서 건물 정보 조회 (주소 코드 기반)
                building_query = """
                    SELECT
                        jibun_address,
                        road_address,
                        building_count,
                        structure_types,
                        purpose_types,
                        max_ground_floors,
                        max_underground_floors,
                        min_underground_floors,
                        buildings_with_seismic,
                        buildings_without_seismic,
                        oldest_approval_date,
                        newest_approval_date,
                        oldest_building_age_years,
                        total_floor_area_sqm,
                        total_building_area_sqm
                    FROM building_aggregate_cache
                    WHERE sigungu_cd = %s
                        AND bjdong_cd = %s
                        AND bun = %s
                        AND ji = %s
                """
                building_result = dw_db.execute_query(building_query, (sigungu_cd, bjdong_cd, bun, ji))

                if not building_result:
                    self.logger.warning(f"[VULNERABILITY] 건물 정보가 없습니다: sigungu_cd={sigungu_cd}, bjdong_cd={bjdong_cd}, bun={bun}, ji={ji}")
                    # 건물 정보가 없으면 AI 요약만 반환
                    aisummry = self._get_ai_summary_from_state(site_id)
                    return VulnerabilityResponse(
                        result="success",
                        data=VulnerabilityData(
                            siteId=site_id,
                            latitude=latitude,
                            longitude=longitude,
                            area=None,
                            grndflrCnt=None,
                            ugrnFlrCnt=None,
                            rserthqkDsgnApplyYn=None,
                            aisummry=aisummry
                        )
                    )

                building_info = building_result[0]
                self.logger.info(f"[VULNERABILITY] 주소 코드로 건물 정보 조회 성공")

            # 4. AI 요약은 state에서 가져오기 (기존 로직 유지)
            aisummry = self._get_ai_summary_from_state(site_id)

            # 5. VulnerabilityData 생성
            # 내진설계 여부 판단 (buildings_with_seismic > 0이면 Y)
            buildings_with_seismic = building_info.get('buildings_with_seismic', 0) or 0
            buildings_without_seismic = building_info.get('buildings_without_seismic', 0) or 0

            # 내진설계 여부 로직 개선: 내진 건물이 있으면 Y, 없으면 N, 둘 다 0이면 None
            if buildings_with_seismic > 0:
                rserthqk_dsgn_apply_yn = 'Y'
            elif buildings_without_seismic > 0:
                rserthqk_dsgn_apply_yn = 'N'
            else:
                rserthqk_dsgn_apply_yn = None

            # 응답 필드명에 맞게 매핑 (DB 컬럼명과 다름)
            # area: 면적 (total_floor_area_sqm 또는 total_building_area_sqm 사용)
            # grndflrCnt: 지상층수 (max_ground_floors)
            # ugrnFlrCnt: 지하층수 (max_underground_floors)
            area_value = building_info.get('total_floor_area_sqm')
            if area_value is None:
                area_value = building_info.get('total_building_area_sqm')

            vulnerability_data = VulnerabilityData(
                siteId=site_id,
                latitude=latitude,
                longitude=longitude,
                area=area_value,
                grndflrCnt=building_info.get('max_ground_floors'),
                ugrnFlrCnt=building_info.get('max_underground_floors'),
                rserthqkDsgnApplyYn=rserthqk_dsgn_apply_yn,
                aisummry=aisummry
            )

            self.logger.info(
                f"[VULNERABILITY] 건물 데이터 매핑 완료: "
                f"area={area_value}, grndflrCnt={building_info.get('max_ground_floors')}, "
                f"ugrnFlrCnt={building_info.get('max_underground_floors')}, "
                f"rserthqk={rserthqk_dsgn_apply_yn}"
            )

            self.logger.info(f"[VULNERABILITY] 건물 특성 분석 데이터 조회 성공: site_id={site_id}")

            # VulnerabilityResponse 반환
            return VulnerabilityResponse(
                result="success",
                data=vulnerability_data
            )

        except Exception as e:
            self.logger.error(f"[VULNERABILITY] 건물 특성 분석 데이터 조회 실패: {e}", exc_info=True)
            return None

    def _get_ai_summary_from_state(self, site_id: UUID) -> str:
        """
        메모리의 state에서 AI 요약 추출

        Args:
            site_id: 사업장 ID

        Returns:
            AI 요약 문자열
        """
        site_id_str = str(site_id)
        building_analysis = None

        # 1. building_data 찾기
        for job_id, cached_state in self._cached_states.items():
            final_state = cached_state.get('final_state', {})
            building_data = final_state.get('building_data', {})

            if site_id_str in building_data:
                building_analysis = building_data[site_id_str]
                self.logger.info(f"[VULNERABILITY] 캐시에서 AI 요약 발견: job_id={job_id}, site_id={site_id}")
                break

        if not building_analysis:
            for job_id, result in self._analysis_results.items():
                final_state = result.get('final_state', {})
                building_data = final_state.get('building_data', {})

                if site_id_str in building_data:
                    building_analysis = building_data[site_id_str]
                    self.logger.info(f"[VULNERABILITY] 분석 결과에서 AI 요약 발견: job_id={job_id}, site_id={site_id}")
                    break

        if not building_analysis:
            self.logger.warning(f"[VULNERABILITY] AI 요약을 찾을 수 없음: site_id={site_id}")
            return "건물 특성 분석 데이터가 없습니다."

        # 2. agent_guidelines에서 AI 분석 요약 추출
        agent_guidelines = building_analysis.get('agent_guidelines', {})
        if not agent_guidelines:
            self.logger.warning(f"[VULNERABILITY] agent_guidelines가 없음: site_id={site_id}")
            return "건물 특성 분석 데이터가 없습니다."

        data_summary = agent_guidelines.get('data_summary', {})

        # AI 요약: one_liner + key_characteristics 결합
        one_liner = data_summary.get('one_liner', '')
        key_chars = data_summary.get('key_characteristics', [])

        aisummry = one_liner
        if key_chars:
            # 주요 특성 3개까지만 추가
            aisummry += " " + " ".join(key_chars[:3])

        return aisummry

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

    async def _notify_springboot_completion(self, job_id: UUID, user_id: Optional[UUID]):
        """Spring Boot API 호출 헬퍼 메서드"""
        try:
            if user_id:
                from ai_agent.services import get_springboot_client
                springboot_client = get_springboot_client()

                # agent_result에서 use_additional_data 확인
                report = False
                if self.db:
                    try:
                        query = "SELECT results FROM batch_jobs WHERE batch_id = %s"
                        result = self.db.execute_query(query, (str(job_id),))
                        if result and result[0].get('results'):
                            agent_results = result[0]['results']
                            if isinstance(agent_results, dict):
                                report = agent_results.get('use_additional_data', False)
                                self.logger.info(f"[SPRINGBOOT] use_additional_data 확인: report={report}")
                    except Exception as e:
                        self.logger.warning(f"[SPRINGBOOT] use_additional_data 조회 실패: {e}")

                self.logger.info(f"[SPRINGBOOT] API 호출: job_id={job_id}, user_id={user_id}, report={report}")
                springboot_client.notify_analysis_completion(user_id, report=report)
                self.logger.info(f"[SPRINGBOOT] API 호출 성공: job_id={job_id}")

                # 해당 user_id의 모든 batch_jobs를 done으로 업데이트
                if self.db:
                    try:
                        update_query = """
                            UPDATE batch_jobs
                            SET status = 'done', progress = 100
                            WHERE created_by = %s AND status != 'done'
                        """
                        self.db.execute_update(update_query, (str(user_id),))
                        self.logger.info(f"[SPRINGBOOT] user_id={user_id}의 모든 batch_jobs를 done으로 업데이트 완료")
                    except Exception as db_error:
                        self.logger.error(f"[SPRINGBOOT] batch_jobs 업데이트 실패: {db_error}", exc_info=True)
            else:
                self.logger.warning(f"[SPRINGBOOT] user_id가 없습니다: job_id={job_id}")
        except Exception as e:
            self.logger.error(f"[SPRINGBOOT] API 호출 실패: job_id={job_id}, error={e}", exc_info=True)
            # API 호출 실패해도 전체 프로세스는 계속 진행

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
            user_id = job.get('created_by')
            await self._notify_springboot_completion(batch_id, user_id)
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
            # Use nearest neighbor search for latitude/longitude (handles floating point precision issues)
            # 각 리스크 타입별로 최근접 위경도 값을 찾음 (거리 제한 없이 가장 가까운 값)
            hazard_query = """
                SELECT DISTINCT ON (risk_type)
                    risk_type,
                    ssp245_score_100,
                    latitude,
                    longitude
                FROM hazard_results
                WHERE target_year = %s
                    AND risk_type = ANY(%s)
                ORDER BY risk_type, (
                    POW(latitude - %s, 2) + POW(longitude - %s, 2)
                ) ASC
            """
            hazard_rows = db.execute_query(hazard_query, (str(TARGET_YEAR), RISK_TYPES, latitude, longitude))
            hazard_data = {row['risk_type']: row for row in hazard_rows}

            exposure_query = "SELECT risk_type, COALESCE(exposure_score, 0) as exposure_score FROM exposure_results WHERE site_id = %s AND target_year = %s"
            exposure_rows = db.execute_query(exposure_query, (str(site_id), str(TARGET_YEAR)))
            exposure_data = {row['risk_type']: row for row in exposure_rows}

            vulnerability_query = "SELECT risk_type, COALESCE(vulnerability_score, 0) as vulnerability_score FROM vulnerability_results WHERE site_id = %s AND target_year = %s"
            vulnerability_rows = db.execute_query(vulnerability_query, (str(site_id), str(TARGET_YEAR)))
            vulnerability_data = {row['risk_type']: row for row in vulnerability_rows}

            aal_query = "SELECT risk_type, COALESCE(ssp245_final_aal, 0.0) as ssp245_final_aal FROM aal_scaled_results WHERE site_id = %s AND target_year = %s"
            aal_rows = db.execute_query(aal_query, (str(site_id), str(TARGET_YEAR)))
            aal_data = {row['risk_type']: row for row in aal_rows}
            
            # Data validation and processing
            missing_risks = [rt for rt in RISK_TYPES if rt not in hazard_data or rt not in exposure_data or rt not in vulnerability_data or rt not in aal_data]
            if missing_risks:
                raise HTTPException(status_code=404, detail=f"Missing data for year {TARGET_YEAR}, SSP2 scenario. Risk types: {', '.join(missing_risks)}")

            physical_risk_scores_dict = {}
            aal_scores_dict = {}
            for risk_type in RISK_TYPES:
                # Get raw values for NULL detection logging
                h_val = hazard_data[risk_type]['ssp245_score_100']
                e_val = exposure_data[risk_type]['exposure_score']
                v_val = vulnerability_data[risk_type]['vulnerability_score']
                aal_val = aal_data[risk_type]['ssp245_final_aal']

                # Log warning if NULL values detected
                if h_val is None or e_val is None or v_val is None or aal_val is None:
                    self.logger.warning(
                        f"[SUMMARY] NULL values detected for {risk_type}: "
                        f"H={h_val}, E={e_val}, V={v_val}, AAL={aal_val}"
                    )

                # Apply defaults with NULL safety
                H = h_val if h_val is not None else 1
                E = e_val or 0
                V = v_val or 0

                physical_risk_score = int(round((H * E * V) / 10000))
                physical_risk_scores_dict[risk_type] = physical_risk_score
                aal_scores_dict[risk_type] = float(aal_val or 0.0)

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
