from uuid import UUID, uuid4
from typing import Optional

from src.core.config import settings
from src.schemas.simulation import (
    RelocationSimulationRequest,
    RelocationSimulationResponse,
    ClimateSimulationRequest,
    ClimateSimulationResponse,
    CandidateResult,
    PhysicalRiskScores,
    AALScores,
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
            candidate_result = CandidateResult(
                candidateId=uuid4(),
                latitude=request.candidate.latitude,
                longitude=request.candidate.longitude,
                jibunAddress=request.candidate.jibun_address,
                roadAddress=request.candidate.road_address,
                riskscore=70,
                aalscore=20.0,
                **{
                    "physical-risk-scores": PhysicalRiskScores(
                        extreme_heat=10,
                        extreme_cold=20,
                        river_flood=30,
                        urban_flood=40,
                        drought=50,
                        water_stress=60,
                        sea_level_rise=50,
                        typhoon=70,
                        wildfire=60
                    ),
                    "aal-scores": AALScores(
                        extreme_heat=9.0,
                        extreme_cold=10.0,
                        river_flood=11.0,
                        urban_flood=12.0,
                        drought=13.0,
                        water_stress=14.0,
                        sea_level_rise=15.0,
                        typhoon=17.0,
                        wildfire=16.0
                    )
                },
                pros="홍수 위험 62% 감소한다",
                cons="초기 구축 비용 증가한다"
            )

            return RelocationSimulationResponse(
                siteId=request.site_id,
                candidate=candidate_result
            )

        # 실제 ai_agent를 사용한 비교 분석
        try:
            # 후보지 분석
            result = await self._analyze_location(
                request.candidate.latitude,
                request.candidate.longitude,
                "후보지"
            )

            # 결과 변환
            scores = result.get('physical_risk_scores', {})
            aal_results = result.get('aal_analysis', {})

            # PhysicalRiskScores 객체 생성
            physical_scores = PhysicalRiskScores(
                extreme_heat=int(scores.get('extreme_heat', {}).get('physical_risk_score_100', 0)),
                extreme_cold=int(scores.get('extreme_cold', {}).get('physical_risk_score_100', 0)),
                river_flood=int(scores.get('river_flood', {}).get('physical_risk_score_100', 0)),
                urban_flood=int(scores.get('urban_flood', {}).get('physical_risk_score_100', 0)),
                drought=int(scores.get('drought', {}).get('physical_risk_score_100', 0)),
                water_stress=int(scores.get('water_stress', {}).get('physical_risk_score_100', 0)),
                sea_level_rise=int(scores.get('sea_level_rise', {}).get('physical_risk_score_100', 0)),
                typhoon=int(scores.get('typhoon', {}).get('physical_risk_score_100', 0)),
                wildfire=int(scores.get('wildfire', {}).get('physical_risk_score_100', 0))
            )

            # AALScores 객체 생성
            aal_scores = AALScores(
                extreme_heat=aal_results.get('extreme_heat', {}).get('final_aal_percentage', 0.0),
                extreme_cold=aal_results.get('extreme_cold', {}).get('final_aal_percentage', 0.0),
                river_flood=aal_results.get('river_flood', {}).get('final_aal_percentage', 0.0),
                urban_flood=aal_results.get('urban_flood', {}).get('final_aal_percentage', 0.0),
                drought=aal_results.get('drought', {}).get('final_aal_percentage', 0.0),
                water_stress=aal_results.get('water_stress', {}).get('final_aal_percentage', 0.0),
                sea_level_rise=aal_results.get('sea_level_rise', {}).get('final_aal_percentage', 0.0),
                typhoon=aal_results.get('typhoon', {}).get('final_aal_percentage', 0.0),
                wildfire=aal_results.get('wildfire', {}).get('final_aal_percentage', 0.0)
            )

            # 종합 점수 계산
            all_risk_scores = [
                physical_scores.extreme_heat, physical_scores.extreme_cold,
                physical_scores.river_flood, physical_scores.urban_flood,
                physical_scores.drought, physical_scores.water_stress,
                physical_scores.sea_level_rise, physical_scores.typhoon,
                physical_scores.wildfire
            ]
            avg_risk_score = int(sum(all_risk_scores) / len(all_risk_scores))

            all_aal_scores = [
                aal_scores.extreme_heat, aal_scores.extreme_cold,
                aal_scores.river_flood, aal_scores.urban_flood,
                aal_scores.drought, aal_scores.water_stress,
                aal_scores.sea_level_rise, aal_scores.typhoon,
                aal_scores.wildfire
            ]
            avg_aal_score = sum(all_aal_scores) / len(all_aal_scores)

            # CandidateResult 생성
            candidate = CandidateResult(
                candidateId=uuid4(),
                latitude=request.candidate.latitude,
                longitude=request.candidate.longitude,
                jibunAddress=request.candidate.jibun_address,
                roadAddress=request.candidate.road_address,
                riskscore=avg_risk_score,
                aalscore=avg_aal_score,
                **{
                    "physical-risk-scores": physical_scores,
                    "aal-scores": aal_scores
                },
                pros="AI 분석 결과 기반 장점",
                cons="AI 분석 결과 기반 단점"
            )

            return RelocationSimulationResponse(
                siteId=request.site_id,
                candidate=candidate
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
