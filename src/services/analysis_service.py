from uuid import UUID, uuid4
from typing import Optional
from datetime import datetime
from fastapi import HTTPException
import logging

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


class AnalysisService:
    """분석 서비스 - ai_agent를 호출하여 분석 수행"""

    def __init__(self):
        """서비스 초기화"""
        self._analyzer = None
        self._analysis_results = {}  # site_id별 분석 결과 캐시
        self._cached_states = {}  # job_id별 State 캐시 (enhance용)
        self.logger = logging.getLogger("api.services.analysis")

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
        """ai_agent 분석 실행"""
        analyzer = self._get_analyzer()

        target_location = {
            'latitude': site_info.get('lat', site_info.get('latitude', 37.5665)),
            'longitude': site_info.get('lng', site_info.get('longitude', 126.9780)),
            'name': site_info.get('name', 'Unknown Location')
        }

        building_info = {
            'building_age': site_info.get('building_age', 20),
            'has_seismic_design': site_info.get('has_seismic_design', True),
            'fire_access': site_info.get('fire_access', True)
        }

        asset_info = {
            'total_asset_value': asset_value,
            'insurance_coverage_rate': site_info.get('insurance_coverage_rate', 0.7)
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

    async def start_analysis(self, site_id: UUID, request: StartAnalysisRequest) -> AnalysisJobStatus:
        """Spring Boot API 호환 - 분석 작업 시작"""
        job_id = uuid4()

        if settings.USE_MOCK_DATA:
            return AnalysisJobStatus(
                jobId=str(job_id),
                siteId=site_id,
                status="completed",
                progress=100,
                currentNode="completed",
                startedAt=datetime.now(),
                completedAt=datetime.now(),
            )

        try:
            site_info = {
                'id': str(request.site.id),
                'name': request.site.name,
                'lat': request.site.latitude,
                'lng': request.site.longitude,
            }

            # additional_data 변환 (Pydantic 모델 → dict)
            additional_data_dict = None
            if request.additional_data:
                additional_data_dict = {
                    'raw_text': request.additional_data.raw_text,
                    'metadata': request.additional_data.metadata or {}
                }

            result = await self._run_agent_analysis(site_info, additional_data=additional_data_dict)
            self._analysis_results[site_id] = result

            # State 캐싱 (enhance용) - Node 1~4 결과 포함
            self._cached_states[job_id] = result.copy()

            status = "completed" if result.get('workflow_status') == 'completed' else "failed"

            return AnalysisJobStatus(
                jobId=str(job_id),
                siteId=site_id,
                status=status,
                progress=100 if status == "completed" else 0,
                currentNode="completed" if status == "completed" else "failed",
                startedAt=datetime.now(),
                completedAt=datetime.now() if status == "completed" else None,
                error={"code": "ANALYSIS_FAILED", "message": str(result.get('errors', []))} if result.get('errors') else None,
            )
        except Exception as e:
            return AnalysisJobStatus(
                jobId=str(job_id),
                siteId=site_id,
                status="failed",
                progress=0,
                currentNode="failed",
                startedAt=datetime.now(),
                error={"code": "ANALYSIS_FAILED", "message": str(e)},
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

    async def get_job_status(self, site_id: UUID, job_id: UUID) -> Optional[AnalysisJobStatus]:
        """Spring Boot API 호환 - 작업 상태 조회"""
        if settings.USE_MOCK_DATA:
            return AnalysisJobStatus(
                jobId=str(job_id),
                siteId=site_id,
                status="completed",
                progress=100,
                currentNode="completed",
                startedAt=datetime.now(),
                completedAt=datetime.now(),
            )
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

        return None

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
