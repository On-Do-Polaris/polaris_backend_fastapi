from uuid import UUID, uuid4
from typing import Optional

from src.core.config import settings
from src.schemas.simulation import (
    RelocationSimulationRequest,
    RelocationSimulationResponse,
    ClimateSimulationRequest,
    ClimateSimulationResponse,
    RiskData,
    LocationData,
    SiteData,
    YearlyData,
)
from src.schemas.common import SSPScenario

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

    async def compare_relocation(
        self, request: RelocationSimulationRequest
    ) -> RelocationSimulationResponse:
        """Spring Boot API 호환 - 이전 시뮬레이션 비교"""
        if settings.USE_MOCK_DATA:
            current_risks = [
                RiskData(riskType="폭염", riskScore=75, aal=0.023),
                RiskData(riskType="태풍", riskScore=65, aal=0.018),
                RiskData(riskType="홍수", riskScore=55, aal=0.012),
                RiskData(riskType="가뭄", riskScore=40, aal=0.008),
            ]

            new_risks = [
                RiskData(riskType="폭염", riskScore=60, aal=0.018),
                RiskData(riskType="태풍", riskScore=45, aal=0.012),
                RiskData(riskType="홍수", riskScore=35, aal=0.008),
                RiskData(riskType="가뭄", riskScore=50, aal=0.010),
            ]

            return RelocationSimulationResponse(
                currentLocation=LocationData(risks=current_risks),
                newLocation=LocationData(risks=new_risks),
            )

        # 실제 ai_agent를 사용한 비교 분석
        try:
            # 현재 위치 분석 (실제로는 DB에서 조회)
            base_result = await self._analyze_location(35.1796, 129.0756, "현재 사업장")

            # 후보지 분석
            candidate_result = await self._analyze_location(
                request.latitude,
                request.longitude,
                "후보지"
            )

            # 결과 변환
            base_scores = base_result.get('physical_risk_scores', {})
            candidate_scores = candidate_result.get('physical_risk_scores', {})

            current_risks = []
            new_risks = []

            hazard_names = {
                'typhoon': '태풍',
                'river_flood': '홍수',
                'drought': '가뭄',
                'extreme_heat': '폭염',
                'extreme_cold': '한파',
                'wildfire': '산불',
            }

            # AAL 분석 결과 가져오기
            base_aal_results = result.get('aal_analysis', {})
            candidate_aal_results = candidate_result.get('aal_analysis', {})

            for risk_type, risk_data in base_scores.items():
                # AAL v11: final_aal_percentage를 0-1 스케일로 변환
                aal_data = base_aal_results.get(risk_type, {})
                aal_percentage = aal_data.get('final_aal_percentage', 0.0)
                aal_rate = aal_percentage / 100.0  # % → 0-1 스케일

                current_risks.append(RiskData(
                    riskType=hazard_names.get(risk_type, risk_type),
                    riskScore=int(risk_data.get('physical_risk_score_100', 0)),
                    aal=aal_rate,
                ))

            for risk_type, risk_data in candidate_scores.items():
                # AAL v11: final_aal_percentage를 0-1 스케일로 변환
                aal_data = candidate_aal_results.get(risk_type, {})
                aal_percentage = aal_data.get('final_aal_percentage', 0.0)
                aal_rate = aal_percentage / 100.0  # % → 0-1 스케일

                new_risks.append(RiskData(
                    riskType=hazard_names.get(risk_type, risk_type),
                    riskScore=int(risk_data.get('physical_risk_score_100', 0)),
                    aal=aal_rate,
                ))

            return RelocationSimulationResponse(
                currentLocation=LocationData(risks=current_risks),
                newLocation=LocationData(risks=new_risks),
            )

        except Exception:
            return None

    async def run_climate_simulation(
        self, request: ClimateSimulationRequest
    ) -> ClimateSimulationResponse:
        """Spring Boot API 호환 - 기후 시뮬레이션"""
        if settings.USE_MOCK_DATA:
            yearly_data = []

            # 시작 연도부터 10년간 데이터 생성
            for year in range(request.start_year, request.start_year + 30, 10):
                sites = []
                for i, site_id in enumerate(request.site_ids):
                    # 시나리오에 따른 점수 증가율
                    scenario_factor = {
                        SSPScenario.SSP1_26: 0.01,
                        SSPScenario.SSP2_45: 0.02,
                        SSPScenario.SSP3_70: 0.03,
                        SSPScenario.SSP5_85: 0.04,
                    }.get(request.scenario, 0.02)

                    years_from_start = year - request.start_year
                    base_score = 65 + (i * 5)  # 사업장별 기본 점수
                    risk_score = min(100, int(base_score * (1 + scenario_factor * years_from_start / 10)))

                    sites.append(SiteData(
                        siteId=site_id,
                        siteName=f"사업장 {i + 1}",
                        riskScore=risk_score,
                        localAverageTemperature=14.5 + (scenario_factor * years_from_start),
                    ))

                # 전국 평균 기온
                national_avg_temp = 14.5 + (scenario_factor * (year - request.start_year))

                yearly_data.append(YearlyData(
                    year=year,
                    nationalAverageTemperature=round(national_avg_temp, 1),
                    sites=sites,
                ))

            return ClimateSimulationResponse(
                scenario=request.scenario,
                riskType=request.hazard_type,
                yearlyData=yearly_data,
            )

        return None
