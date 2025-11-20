from uuid import UUID, uuid4
from typing import Optional
from datetime import datetime

from src.core.config import settings
from src.schemas.analysis import (
    StartAnalysisRequest,
    AnalysisJobStatus,
    AnalysisOverviewResponse,
    PhysicalRiskScoreResponse,
    PastEventsResponse,
    SSPProjectionResponse,
    FinancialImpactResponse,
    VulnerabilityResponse,
    AnalysisTotalResponse,
    PhysicalRiskBarItem,
    PastEventItem,
    PastEventSummary,
    SSPScenarioProjection,
    SSPProjectionPoint,
    FinancialImpactItem,
    VulnerabilityItem,
)
from src.schemas.common import HazardType, TimeScale, RiskLevel, SSPScenario

# ai_agent 호출
from ai_agent import SKAXPhysicalRiskAnalyzer
from ai_agent.config.settings import load_config


class AnalysisService:
    """분석 서비스 - ai_agent를 호출하여 분석 수행"""

    def __init__(self):
        """서비스 초기화"""
        self._analyzer = None
        self._analysis_results = {}  # site_id별 분석 결과 캐시

    def _get_analyzer(self) -> SKAXPhysicalRiskAnalyzer:
        """ai_agent 분석기 인스턴스 반환 (lazy initialization)"""
        if self._analyzer is None:
            config = load_config()
            self._analyzer = SKAXPhysicalRiskAnalyzer(config)
        return self._analyzer

    async def _run_agent_analysis(self, site_info: dict, asset_value: float = 50000000000) -> dict:
        """
        ai_agent 분석 실행

        Args:
            site_info: 사업장 정보 (id, name, lat, lng 등)
            asset_value: 자산 가치 (기본값 500억원)

        Returns:
            분석 결과 딕셔너리
        """
        analyzer = self._get_analyzer()

        # ai_agent 입력 형식에 맞게 변환
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

        # ai_agent 분석 실행
        result = analyzer.analyze(target_location, building_info, asset_info, analysis_params)

        return result

    async def start_analysis(self, request: StartAnalysisRequest) -> AnalysisJobStatus:
        """분석 작업 시작"""
        job_id = uuid4()

        if settings.USE_MOCK_DATA:
            return AnalysisJobStatus(
                jobId=job_id,
                siteId=request.site.id,
                status="completed",
                progress=100,
                startedAt=datetime.now(),
                completedAt=datetime.now(),
            )

        # 실제 ai_agent 호출
        try:
            site_info = {
                'id': str(request.site.id),
                'name': request.site.name,
                'lat': request.site.latitude,
                'lng': request.site.longitude,
            }

            # 분석 실행 (비동기적으로 실행하고 결과 캐시)
            result = await self._run_agent_analysis(site_info)

            # 결과 캐시
            self._analysis_results[request.site.id] = result

            status = "completed" if result.get('workflow_status') == 'completed' else "failed"

            return AnalysisJobStatus(
                jobId=job_id,
                siteId=request.site.id,
                status=status,
                progress=100 if status == "completed" else 0,
                startedAt=datetime.now(),
                completedAt=datetime.now() if status == "completed" else None,
                error={"message": str(result.get('errors', []))} if result.get('errors') else None,
            )
        except Exception as e:
            return AnalysisJobStatus(
                jobId=job_id,
                siteId=request.site.id,
                status="failed",
                progress=0,
                startedAt=datetime.now(),
                error={"message": str(e)},
            )

    async def get_job_status(self, job_id: UUID) -> Optional[AnalysisJobStatus]:
        """작업 상태 조회"""
        if settings.USE_MOCK_DATA:
            return AnalysisJobStatus(
                jobId=job_id,
                siteId=uuid4(),
                status="completed",
                progress=100,
                startedAt=datetime.now(),
                completedAt=datetime.now(),
            )

        # TODO: 실제 작업 상태 조회 (PostgreSQL에서)
        return None

    async def get_overview(self, site_id: UUID) -> Optional[AnalysisOverviewResponse]:
        """분석 개요 조회"""
        if settings.USE_MOCK_DATA:
            return AnalysisOverviewResponse(
                siteId=site_id,
                analyzedAt=datetime.now(),
                mainHazard=HazardType.TYPHOON,
                mainHazardScore=78,
                overallRiskScore=65,
                riskLevel=RiskLevel.MEDIUM,
                aal=0.0625,
                annualExpectedLoss=125000000.0,
                assetValue=2000000000.0,
                recommendations=[
                    "태풍 대비 시설물 보강 필요",
                    "배수 시스템 점검 권장",
                    "비상 대응 계획 수립",
                ],
            )

        # 캐시된 결과에서 조회
        result = self._analysis_results.get(site_id)
        if not result:
            return None

        # ai_agent 결과를 API 응답 형식으로 변환
        physical_risk_scores = result.get('physical_risk_scores', {})

        # 최고 점수 리스크 찾기
        main_hazard = HazardType.TYPHOON
        main_score = 0
        total_score = 0

        for risk_type, risk_data in physical_risk_scores.items():
            score = risk_data.get('physical_risk_score_100', 0)
            total_score += score
            if score > main_score:
                main_score = score
                # risk_type을 HazardType으로 매핑
                hazard_map = {
                    'typhoon': HazardType.TYPHOON,
                    'inland_flood': HazardType.INLAND_FLOOD,
                    'coastal_flood': HazardType.COASTAL_FLOOD,
                    'drought': HazardType.DROUGHT,
                    'wildfire': HazardType.WILDFIRE,
                    'high_temperature': HazardType.HIGH_TEMPERATURE,
                    'cold_wave': HazardType.COLD_WAVE,
                    'water_scarcity': HazardType.WATER_SCARCITY,
                    'urban_flood': HazardType.URBAN_FLOOD,
                }
                main_hazard = hazard_map.get(risk_type, HazardType.TYPHOON)

        avg_score = total_score / len(physical_risk_scores) if physical_risk_scores else 0

        # 리스크 레벨 결정
        if avg_score >= 70:
            risk_level = RiskLevel.HIGH
        elif avg_score >= 40:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        return AnalysisOverviewResponse(
            siteId=site_id,
            analyzedAt=datetime.now(),
            mainHazard=main_hazard,
            mainHazardScore=int(main_score),
            overallRiskScore=int(avg_score),
            riskLevel=risk_level,
            aal=avg_score / 1000,  # 간단한 변환
            annualExpectedLoss=avg_score * 1000000,
            assetValue=50000000000.0,
            recommendations=result.get('response_strategy', {}).get('recommendations', []),
        )

    async def get_physical_risk_scores(
        self, site_id: UUID, hazard_type: Optional[HazardType]
    ) -> Optional[PhysicalRiskScoreResponse]:
        """물리적 리스크 점수 조회"""
        if settings.USE_MOCK_DATA:
            all_scores = [
                PhysicalRiskBarItem(
                    hazardType=HazardType.TYPHOON,
                    score=78,
                    hazardScore=0.8,
                    exposureScore=0.75,
                    vulnerabilityScore=0.7,
                    riskCalculationMethod="H×E×V",
                ),
                PhysicalRiskBarItem(
                    hazardType=HazardType.INLAND_FLOOD,
                    score=55,
                    hazardScore=0.6,
                    exposureScore=0.55,
                    vulnerabilityScore=0.5,
                    riskCalculationMethod="H×E×V",
                ),
                PhysicalRiskBarItem(
                    hazardType=HazardType.DROUGHT,
                    score=25,
                    hazardScore=0.3,
                    exposureScore=0.25,
                    vulnerabilityScore=0.2,
                    riskCalculationMethod="H×E×V",
                ),
            ]

            if hazard_type:
                all_scores = [s for s in all_scores if s.hazard_type == hazard_type]

            return PhysicalRiskScoreResponse(
                siteId=site_id,
                analyzedAt=datetime.now(),
                hazardType=hazard_type,
                physicalRiskScores=all_scores,
            )

        # 캐시된 결과에서 조회
        result = self._analysis_results.get(site_id)
        if not result:
            return None

        physical_risk_scores = result.get('physical_risk_scores', {})
        all_scores = []

        hazard_map = {
            'typhoon': HazardType.TYPHOON,
            'inland_flood': HazardType.INLAND_FLOOD,
            'coastal_flood': HazardType.COASTAL_FLOOD,
            'drought': HazardType.DROUGHT,
            'wildfire': HazardType.WILDFIRE,
            'high_temperature': HazardType.HIGH_TEMPERATURE,
            'cold_wave': HazardType.COLD_WAVE,
            'water_scarcity': HazardType.WATER_SCARCITY,
            'urban_flood': HazardType.URBAN_FLOOD,
        }

        for risk_type, risk_data in physical_risk_scores.items():
            hz_type = hazard_map.get(risk_type)
            if hz_type and (not hazard_type or hz_type == hazard_type):
                all_scores.append(PhysicalRiskBarItem(
                    hazardType=hz_type,
                    score=int(risk_data.get('physical_risk_score_100', 0)),
                    hazardScore=risk_data.get('hazard_score', 0),
                    exposureScore=risk_data.get('exposure_score', 0),
                    vulnerabilityScore=risk_data.get('vulnerability_score', 0),
                    riskCalculationMethod="H×E×V",
                ))

        return PhysicalRiskScoreResponse(
            siteId=site_id,
            analyzedAt=datetime.now(),
            hazardType=hazard_type,
            physicalRiskScores=all_scores,
        )

    async def get_past_events(
        self,
        site_id: UUID,
        hazard_type: Optional[HazardType],
        start_year: Optional[int],
        end_year: Optional[int],
    ) -> Optional[PastEventsResponse]:
        """과거 이벤트 조회"""
        if settings.USE_MOCK_DATA:
            events = [
                PastEventItem(
                    year=2022,
                    month=9,
                    hazardType=HazardType.TYPHOON,
                    warningDays=3,
                    severeDays=2,
                    maxIntensity=0.85,
                    severityLevel="severe",
                    description="태풍 힌남노로 인한 시설물 피해",
                ),
                PastEventItem(
                    year=2020,
                    month=8,
                    hazardType=HazardType.INLAND_FLOOD,
                    warningDays=5,
                    severeDays=3,
                    maxIntensity=0.7,
                    severityLevel="moderate",
                    description="집중호우로 인한 침수 피해",
                ),
            ]

            if hazard_type:
                events = [e for e in events if e.hazard_type == hazard_type]
            if start_year:
                events = [e for e in events if e.year >= start_year]
            if end_year:
                events = [e for e in events if e.year <= end_year]

            summary = PastEventSummary(
                totalEvents=len(events),
                severeEvents=len([e for e in events if e.severity_level == "severe"]),
                avgWarningDays=sum(e.warning_days for e in events) / len(events) if events else 0,
                avgSevereDays=sum(e.severe_days for e in events) / len(events) if events else 0,
                mostFrequentHazard="typhoon",
                yearRange={"start": 2020, "end": 2022},
            )

            return PastEventsResponse(
                siteId=site_id,
                summary=summary,
                events=events,
            )

        # ai_agent는 과거 이벤트 데이터를 직접 제공하지 않음
        # 별도의 데이터 소스 연동 필요
        return None

    async def get_ssp_projection(
        self,
        site_id: UUID,
        hazard_type: Optional[HazardType],
        time_scale: Optional[TimeScale],
    ) -> Optional[SSPProjectionResponse]:
        """SSP 전망 조회"""
        if settings.USE_MOCK_DATA:
            projections = []
            scenarios = [
                (SSPScenario.SSP1_26, "지속가능 발전"),
                (SSPScenario.SSP2_45, "중도 시나리오"),
                (SSPScenario.SSP3_70, "지역 경쟁"),
                (SSPScenario.SSP5_85, "화석연료 의존"),
            ]

            for scenario, description in scenarios:
                points = []
                decades = [("2030s", 2030), ("2050s", 2050), ("2100s", 2100)]

                for decade, year in decades:
                    base_score = 65
                    base_aal = 0.0625

                    # 시나리오와 시간에 따른 변동
                    scenario_factor = {
                        SSPScenario.SSP1_26: 1.0,
                        SSPScenario.SSP2_45: 1.2,
                        SSPScenario.SSP3_70: 1.5,
                        SSPScenario.SSP5_85: 1.8,
                    }[scenario]
                    time_factor = {2030: 1.0, 2050: 1.2, 2100: 1.5}[year]

                    points.append(SSPProjectionPoint(
                        decade=decade,
                        year=year,
                        physicalRiskScore=min(100, round(base_score * scenario_factor * time_factor)),
                        aal=min(1.0, round(base_aal * scenario_factor * time_factor, 4)),
                        annualExpectedLoss=round(125000000 * scenario_factor * time_factor),
                    ))

                projections.append(SSPScenarioProjection(
                    scenario=scenario,
                    scenarioDescription=description,
                    points=points,
                ))

            return SSPProjectionResponse(
                siteId=site_id,
                hazardType=hazard_type or HazardType.TYPHOON,
                timeScale=time_scale or TimeScale.MID,
                projections=projections,
                adaptationActions=[
                    {"action": "시설물 보강", "priority": "high"},
                    {"action": "배수 시스템 개선", "priority": "medium"},
                ],
                confidenceLevel="medium",
            )

        # ai_agent 결과에서 SSP 전망 데이터 추출
        # 현재 ai_agent는 SSP 시나리오별 전망을 직접 제공하지 않음
        return None

    async def get_financial_impacts(
        self, site_id: UUID, hazard_type: Optional[HazardType]
    ) -> Optional[FinancialImpactResponse]:
        """재무 영향 조회"""
        if settings.USE_MOCK_DATA:
            impacts = [
                FinancialImpactItem(
                    hazardType=HazardType.TYPHOON,
                    aal=0.0425,
                    annualExpectedLoss=85000000.0,
                ),
                FinancialImpactItem(
                    hazardType=HazardType.INLAND_FLOOD,
                    aal=0.015,
                    annualExpectedLoss=30000000.0,
                ),
                FinancialImpactItem(
                    hazardType=HazardType.DROUGHT,
                    aal=0.005,
                    annualExpectedLoss=10000000.0,
                ),
            ]

            if hazard_type:
                impacts = [i for i in impacts if i.hazard_type == hazard_type]

            return FinancialImpactResponse(
                siteId=site_id,
                analyzedAt=datetime.now(),
                hazardType=hazard_type,
                assetValue=2000000000.0,
                financialImpacts=impacts,
            )

        # 캐시된 결과에서 조회
        result = self._analysis_results.get(site_id)
        if not result:
            return None

        physical_risk_scores = result.get('physical_risk_scores', {})
        impacts = []

        hazard_map = {
            'typhoon': HazardType.TYPHOON,
            'inland_flood': HazardType.INLAND_FLOOD,
            'coastal_flood': HazardType.COASTAL_FLOOD,
            'drought': HazardType.DROUGHT,
            'wildfire': HazardType.WILDFIRE,
            'high_temperature': HazardType.HIGH_TEMPERATURE,
            'cold_wave': HazardType.COLD_WAVE,
            'water_scarcity': HazardType.WATER_SCARCITY,
            'urban_flood': HazardType.URBAN_FLOOD,
        }

        for risk_type, risk_data in physical_risk_scores.items():
            hz_type = hazard_map.get(risk_type)
            if hz_type and (not hazard_type or hz_type == hazard_type):
                financial_loss = risk_data.get('financial_loss', 0)
                aal = financial_loss / 50000000000 if financial_loss else 0  # AAL 계산

                impacts.append(FinancialImpactItem(
                    hazardType=hz_type,
                    aal=aal,
                    annualExpectedLoss=financial_loss,
                ))

        return FinancialImpactResponse(
            siteId=site_id,
            analyzedAt=datetime.now(),
            hazardType=hazard_type,
            assetValue=50000000000.0,
            financialImpacts=impacts,
        )

    async def get_vulnerability(self, site_id: UUID) -> Optional[VulnerabilityResponse]:
        """취약성 분석 조회"""
        if settings.USE_MOCK_DATA:
            return VulnerabilityResponse(
                siteId=site_id,
                totalScore=65,
                overallLevel=RiskLevel.MEDIUM,
                siteInfo={
                    "buildingAge": 15,
                    "structureType": "RC",
                    "floors": 5,
                },
                details=[
                    VulnerabilityItem(
                        hazardType=HazardType.TYPHOON,
                        score=70,
                        level=RiskLevel.MEDIUM,
                        factors={
                            "structural": 0.7,
                            "location": 0.65,
                            "protection": 0.6,
                        },
                        improvementActions=["내진 보강 공사 검토", "외벽 방수 처리"],
                    ),
                    VulnerabilityItem(
                        hazardType=HazardType.INLAND_FLOOD,
                        score=55,
                        level=RiskLevel.MEDIUM,
                        factors={
                            "elevation": 0.5,
                            "drainage": 0.6,
                            "waterproofing": 0.55,
                        },
                        improvementActions=["배수 시스템 점검"],
                    ),
                ],
                priorityActions=[
                    {"action": "내진 보강", "priority": "high", "cost": 50000000},
                    {"action": "배수 개선", "priority": "medium", "cost": 20000000},
                ],
            )

        # 캐시된 결과에서 조회
        result = self._analysis_results.get(site_id)
        if not result:
            return None

        vulnerability_analysis = result.get('vulnerability_analysis', {})

        return VulnerabilityResponse(
            siteId=site_id,
            totalScore=vulnerability_analysis.get('overall_score', 50),
            overallLevel=RiskLevel.MEDIUM,
            siteInfo=vulnerability_analysis.get('building_info', {}),
            details=[],  # ai_agent 결과에서 상세 정보 추출 필요
            priorityActions=vulnerability_analysis.get('priority_actions', []),
        )

    async def get_total_analysis(
        self,
        site_id: UUID,
        hazard_type: HazardType,
        time_scale: Optional[TimeScale],
    ) -> Optional[AnalysisTotalResponse]:
        """통합 분석 결과 조회"""
        if settings.USE_MOCK_DATA:
            # 각 분석 결과를 조합
            overview = await self.get_overview(site_id)
            past_events = await self.get_past_events(site_id, hazard_type, None, None)
            ssp = await self.get_ssp_projection(site_id, hazard_type, time_scale)
            financial = await self.get_financial_impacts(site_id, hazard_type)
            vulnerability = await self.get_vulnerability(site_id)

            return AnalysisTotalResponse(
                siteId=site_id,
                hazardType=hazard_type,
                overview=overview,
                pastEvents=past_events,
                sspProjection=ssp,
                financialImpact=financial,
                vulnerability=vulnerability,
                executiveSummary="종합 리스크 등급 '중간', AAL 6.25%. 태풍이 주요 리스크 요인으로 시설물 보강이 권장됩니다.",
                generatedAt=datetime.now(),
            )

        # 캐시된 결과에서 통합 조회
        overview = await self.get_overview(site_id)
        past_events = await self.get_past_events(site_id, hazard_type, None, None)
        ssp = await self.get_ssp_projection(site_id, hazard_type, time_scale)
        financial = await self.get_financial_impacts(site_id, hazard_type)
        vulnerability = await self.get_vulnerability(site_id)

        result = self._analysis_results.get(site_id, {})

        return AnalysisTotalResponse(
            siteId=site_id,
            hazardType=hazard_type,
            overview=overview,
            pastEvents=past_events,
            sspProjection=ssp,
            financialImpact=financial,
            vulnerability=vulnerability,
            executiveSummary=result.get('generated_report', {}).get('executive_summary', ''),
            generatedAt=datetime.now(),
        )
