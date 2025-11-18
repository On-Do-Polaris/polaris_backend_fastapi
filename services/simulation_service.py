from uuid import UUID, uuid4
from typing import Optional

from core.config import settings
from schemas.simulation import (
    RelocationCandidatesRequest,
    RelocationCandidatesResponse,
    RelocationSimulationRequest,
    RelocationSimulationResult,
    ClimateSimulationRequest,
    ClimateSimulationResponse,
    RelocationCandidate,
    SiteComparison,
    ClimateSimulationSeries,
    ClimateSimulationPoint,
)
from schemas.common import RiskLevel, SSPScenario

# ai_agent 호출
from ai_agent import SKAXPhysicalRiskAnalyzer
from ai_agent.config.settings import load_config


class SimulationService:
    """시뮬레이션 서비스 - ai_agent를 사용하여 시뮬레이션 수행"""

    def __init__(self):
        """서비스 초기화"""
        self._analyzer = None

    def _get_analyzer(self) -> SKAXPhysicalRiskAnalyzer:
        """ai_agent 분석기 인스턴스 반환 (lazy initialization)"""
        if self._analyzer is None:
            config = load_config()
            self._analyzer = SKAXPhysicalRiskAnalyzer(config)
        return self._analyzer

    async def _analyze_location(self, lat: float, lng: float, name: str) -> dict:
        """특정 위치에 대한 ai_agent 분석 실행"""
        analyzer = self._get_analyzer()

        target_location = {
            'latitude': lat,
            'longitude': lng,
            'name': name
        }

        building_info = {
            'building_age': 20,
            'has_seismic_design': True,
            'fire_access': True
        }

        asset_info = {
            'total_asset_value': 50000000000,
            'insurance_coverage_rate': 0.7
        }

        analysis_params = {
            'time_horizon': '2050',
            'analysis_period': '2025-2050'
        }

        return analyzer.analyze(target_location, building_info, asset_info, analysis_params)

    async def get_relocation_candidates(
        self, request: RelocationCandidatesRequest
    ) -> RelocationCandidatesResponse:
        """이전 후보지 추천"""
        if settings.USE_MOCK_DATA:
            return RelocationCandidatesResponse(
                baseSite={
                    "id": str(request.base_site_id),
                    "name": "현재 사업장",
                    "city": "부산",
                    "latitude": 35.1796,
                    "longitude": 129.0756,
                    "riskScore": 65,
                    "riskLevel": "medium",
                },
                candidates=[
                    RelocationCandidate(
                        id=uuid4(),
                        name="마곡 산업단지",
                        city="서울",
                        latitude=37.5665,
                        longitude=126.8298,
                        locationSummary="서울 강서구 마곡동 위치",
                        riskScore=42,
                        riskLevel=RiskLevel.LOW,
                        aal=0.0225,
                        distance=325.5,
                        estimatedCost=150000000.0,
                        advantages=["태풍 리스크 낮음", "배수 시설 양호"],
                        disadvantages=["이전 비용 높음", "기존 거래처와 거리"],
                    ),
                    RelocationCandidate(
                        id=uuid4(),
                        name="판교 테크노밸리",
                        city="성남",
                        latitude=37.3825,
                        longitude=127.1195,
                        locationSummary="경기도 성남시 분당구 위치",
                        riskScore=48,
                        riskLevel=RiskLevel.LOW,
                        aal=0.026,
                        distance=298.0,
                        estimatedCost=120000000.0,
                        advantages=["내륙 지역", "교통 편리"],
                        disadvantages=["부지 확보 어려움"],
                    ),
                    RelocationCandidate(
                        id=uuid4(),
                        name="송도 국제도시",
                        city="인천",
                        latitude=37.3809,
                        longitude=126.6569,
                        locationSummary="인천 연수구 송도동 위치",
                        riskScore=55,
                        riskLevel=RiskLevel.MEDIUM,
                        aal=0.034,
                        distance=340.0,
                        estimatedCost=100000000.0,
                        advantages=["최신 인프라", "물류 접근성"],
                        disadvantages=["해안가 인접"],
                    ),
                ],
            )

        # 실제 ai_agent를 사용한 후보지 분석
        # 현재 ai_agent는 후보지 추천 기능을 직접 제공하지 않음
        # 여러 위치에 대한 분석을 실행하여 비교 가능
        return None

    async def compare_relocation(
        self, request: RelocationSimulationRequest
    ) -> RelocationSimulationResult:
        """이전 시뮬레이션 비교"""
        if settings.USE_MOCK_DATA:
            return RelocationSimulationResult(
                baseSite={
                    "id": str(request.base_site_id),
                    "name": "현재 사업장",
                    "city": "부산",
                    "latitude": 35.1796,
                    "longitude": 129.0756,
                    "riskScore": 65,
                    "riskLevel": "medium",
                    "aal": 0.0625,
                    "annualExpectedLoss": 125000000,
                },
                candidateSite={
                    "name": request.candidate_name or "후보지",
                    "latitude": request.candidate_latitude,
                    "longitude": request.candidate_longitude,
                    "riskScore": 45,
                    "riskLevel": "low",
                    "aal": 0.0275,
                    "annualExpectedLoss": 55000000,
                },
                comparison=SiteComparison(
                    riskScoreDiff=-20,
                    riskScoreDiffPercent=-30.8,
                    aalDiff=-0.035,
                    annualExpectedLossDiff=-70000000.0,
                ),
                climateFactorComparison={
                    "typhoon": {"base": 78, "candidate": 35, "diff": -43},
                    "inland_flood": {"base": 55, "candidate": 30, "diff": -25},
                    "drought": {"base": 25, "candidate": 45, "diff": 20},
                },
                pros=[
                    "태풍 리스크 55% 감소",
                    "홍수 리스크 45% 감소",
                    "연간 예상 손실 70백만원 절감",
                ],
                cons=[
                    "가뭄 리스크 80% 증가",
                    "이전 비용 발생",
                ],
                recommendation="후보지로 이전 시 태풍 리스크가 크게 감소하며, "
                              "연간 예상 손실이 70백만원 감소할 것으로 예상됩니다. "
                              "다만, 가뭄 리스크에 대한 대비가 필요합니다.",
                financialAnalysis={
                    "relocationCost": 100000000,
                    "annualSavings": 70000000,
                    "paybackPeriod": 1.43,
                    "npv10Year": 500000000,
                },
            )

        # 실제 ai_agent를 사용한 비교 분석
        try:
            # 현재 위치 분석 (실제로는 DB에서 조회)
            base_result = await self._analyze_location(35.1796, 129.0756, "현재 사업장")

            # 후보지 분석
            candidate_result = await self._analyze_location(
                request.candidate_latitude,
                request.candidate_longitude,
                request.candidate_name or "후보지"
            )

            # 결과 비교
            base_scores = base_result.get('physical_risk_scores', {})
            candidate_scores = candidate_result.get('physical_risk_scores', {})

            # 평균 점수 계산
            base_avg = sum(d.get('physical_risk_score_100', 0) for d in base_scores.values()) / len(base_scores) if base_scores else 0
            candidate_avg = sum(d.get('physical_risk_score_100', 0) for d in candidate_scores.values()) / len(candidate_scores) if candidate_scores else 0

            # 총 재무 손실 계산
            base_loss = sum(d.get('financial_loss', 0) for d in base_scores.values())
            candidate_loss = sum(d.get('financial_loss', 0) for d in candidate_scores.values())

            score_diff = candidate_avg - base_avg
            loss_diff = candidate_loss - base_loss

            return RelocationSimulationResult(
                baseSite={
                    "id": str(request.base_site_id),
                    "name": "현재 사업장",
                    "latitude": 35.1796,
                    "longitude": 129.0756,
                    "riskScore": int(base_avg),
                    "riskLevel": "medium" if 40 <= base_avg < 70 else ("high" if base_avg >= 70 else "low"),
                    "aal": base_loss / 50000000000,
                    "annualExpectedLoss": base_loss,
                },
                candidateSite={
                    "name": request.candidate_name or "후보지",
                    "latitude": request.candidate_latitude,
                    "longitude": request.candidate_longitude,
                    "riskScore": int(candidate_avg),
                    "riskLevel": "medium" if 40 <= candidate_avg < 70 else ("high" if candidate_avg >= 70 else "low"),
                    "aal": candidate_loss / 50000000000,
                    "annualExpectedLoss": candidate_loss,
                },
                comparison=SiteComparison(
                    riskScoreDiff=int(score_diff),
                    riskScoreDiffPercent=round((score_diff / base_avg * 100) if base_avg else 0, 1),
                    aalDiff=round((candidate_loss - base_loss) / 50000000000, 4),
                    annualExpectedLossDiff=loss_diff,
                ),
                climateFactorComparison={},
                pros=[],
                cons=[],
                recommendation=candidate_result.get('response_strategy', {}).get('recommendations', ['분석 결과를 확인하세요'])[0] if candidate_result.get('response_strategy') else '',
                financialAnalysis={},
            )

        except Exception as e:
            return None

    async def simulate_climate(
        self, request: ClimateSimulationRequest
    ) -> ClimateSimulationResponse:
        """기후 시뮬레이션"""
        if settings.USE_MOCK_DATA:
            series = []

            for site in request.sites:
                points = []
                base_risk = 65

                for year in range(request.start_year, request.end_year + 1, request.time_step):
                    # 시나리오에 따른 리스크 증가율 계산
                    years_from_start = year - request.start_year
                    scenario_factor = {
                        SSPScenario.SSP1_26: 0.002,
                        SSPScenario.SSP2_45: 0.005,
                        SSPScenario.SSP3_70: 0.008,
                        SSPScenario.SSP5_85: 0.012,
                    }.get(request.scenario, 0.005)

                    risk_score = min(100, round(base_risk * (1 + scenario_factor * years_from_start)))

                    points.append(ClimateSimulationPoint(
                        year=year,
                        metric=round(15 + scenario_factor * years_from_start * 10, 1),  # 예: 온도
                        riskScore=risk_score,
                    ))

                series.append(ClimateSimulationSeries(
                    siteId=site.id,
                    siteName=site.name,
                    metricName="평균 기온",
                    metricUnit="°C",
                    points=points,
                ))

            scenario_descriptions = {
                SSPScenario.SSP1_26: "지속가능 발전 시나리오",
                SSPScenario.SSP2_45: "중도 시나리오",
                SSPScenario.SSP3_70: "지역 경쟁 시나리오",
                SSPScenario.SSP5_85: "화석연료 의존 시나리오",
            }

            return ClimateSimulationResponse(
                scenario=request.scenario,
                scenarioDescription=scenario_descriptions.get(request.scenario, ""),
                hazardType=request.hazard_type,
                series=series,
                timelineActions=[
                    {"year": 2030, "action": "배수 시스템 업그레이드", "priority": "high"},
                    {"year": 2040, "action": "건물 내열 보강", "priority": "medium"},
                    {"year": 2050, "action": "대체 수자원 확보", "priority": "high"},
                ],
                summary=f"{request.scenario.value} 시나리오 기준 {request.end_year}년까지 "
                        f"기후변화로 인한 리스크 증가가 예상됩니다.",
            )

        # 실제 ai_agent를 사용한 기후 시뮬레이션
        # 현재 ai_agent는 SSP 시나리오별 시계열 시뮬레이션을 직접 제공하지 않음
        return None
