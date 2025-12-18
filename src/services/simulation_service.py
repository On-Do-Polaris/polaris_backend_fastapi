import logging
from uuid import UUID, uuid4
from typing import Optional
from fastapi import HTTPException
from typing import List, Dict

from src.core.config import settings
from src.schemas.simulation import (
    RelocationSimulationRequest,
    RelocationSimulationResponse,
    ClimateSimulationRequest,
    ClimateSimulationResponse,
    CandidateResult,
    PhysicalRiskScores,
    AALScores,
    LocationRecommendationResponse,
    LocationRecommendationSite,
    LocationRecommendationCandidate,
)
from src.schemas.common import SSPScenario

# ai_agent 호출
from ai_agent import SKAXPhysicalRiskAnalyzer
from ai_agent.config.settings import load_config
from utils.region_mapper import REGION_COORD_MAP  # {"11010": {"lat": 37.5, "lng": 127.0}}

from ai_agent.utils.database import DatabaseManager

class SimulationService:
    """시뮬레이션 서비스 - ai_agent를 사용하여 시뮬레이션 수행"""

    def __init__(self):
        """서비스 초기화"""
        self._analyzer = None
        self.logger = logging.getLogger("api.services.simulation")

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

    async def get_location_recommendation(
        self, site_id: str
    ) -> LocationRecommendationResponse:
        """
        Spring Boot API 호환 - 위치 추천 (candidate_sites 테이블 기반)

        종합 AAL이 가장 낮은 상위 3개의 후보지를 반환
        """
        try:
            db = DatabaseManager()

            # candidate_sites 테이블에서 상위 3개 조회
            candidates = db.fetch_top_candidates_by_aal(site_id, limit=3)

            # 후보지 변환
            result_candidates = []
            for candidate in candidates:
                # risks와 aal_by_risk는 JSONB로 저장되어 있음
                risks = candidate.get('risks', {}) or {}
                aal_by_risk = candidate.get('aal_by_risk', {}) or {}

                # dict -> int/float 변환
                physical_risk_scores = {}
                aal_scores = {}

                for risk_type in ['extreme_heat', 'extreme_cold', 'river_flood', 'urban_flood',
                                  'drought', 'water_stress', 'sea_level_rise', 'typhoon', 'wildfire']:
                    physical_risk_scores[risk_type] = int(risks.get(risk_type, 0) or 0)
                    aal_scores[risk_type] = float(aal_by_risk.get(risk_type, 0.0) or 0.0)

                # advantages/disadvantages는 text[] 배열
                advantages = candidate.get('advantages', []) or []
                disadvantages = candidate.get('disadvantages', []) or []

                result_candidates.append(
                    LocationRecommendationCandidate(
                        candidateId=candidate['candidate_id'],
                        candidateName=candidate.get('name'),
                        latitude=float(candidate['latitude']),
                        longitude=float(candidate['longitude']),
                        jibunAddress=candidate.get('jibun_address'),
                        roadAddress=candidate.get('road_address'),
                        riskscore=int(candidate.get('risk_score') or 0),
                        aalscore=float(candidate.get('aal') or 0.0),
                        **{
                            "physical-risk-scores": physical_risk_scores,
                            "aal-scores": aal_scores
                        },
                        pros=advantages[0] if advantages else None,
                        cons=disadvantages[0] if disadvantages else None
                    )
                )

            # 3개가 안 되면 None으로 채움
            site_data = LocationRecommendationSite(
                siteId=UUID(site_id),
                candidate1=result_candidates[0] if len(result_candidates) > 0 else None,
                candidate2=result_candidates[1] if len(result_candidates) > 1 else None,
                candidate3=result_candidates[2] if len(result_candidates) > 2 else None
            )

            return LocationRecommendationResponse(site=site_data)

        except Exception as e:
            self.logger.error(f"[RECOMMENDATION] Failed to get recommendations: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Location recommendation failed: {str(e)}")

    async def compare_relocation_with_db(
        self, request: RelocationSimulationRequest
    ) -> RelocationSimulationResponse:
        """
        Spring Boot API 호환 - 이전 시뮬레이션 비교 (DB 기반)

        candidate_sites 테이블에서 좌표로 후보지를 조회하여 반환
        """
        try:
            db = DatabaseManager()

            # 좌표로 후보지 조회 (최근접 좌표, 거리 제한 없음)
            candidate = db.fetch_candidate_by_location(
                request.candidate.latitude,
                request.candidate.longitude
            )

            if not candidate:
                # DB에 없으면 기존 로직 사용 (ai_agent 호출)
                return await self.compare_relocation(request)

            # candidate_sites 데이터로 응답 생성
            risks = candidate.get('risks', {}) or {}
            aal_by_risk = candidate.get('aal_by_risk', {}) or {}

            physical_risk_scores = PhysicalRiskScores(
                extreme_heat=int(risks.get('extreme_heat', 0) or 0),
                extreme_cold=int(risks.get('extreme_cold', 0) or 0),
                river_flood=int(risks.get('river_flood', 0) or 0),
                urban_flood=int(risks.get('urban_flood', 0) or 0),
                drought=int(risks.get('drought', 0) or 0),
                water_stress=int(risks.get('water_stress', 0) or 0),
                sea_level_rise=int(risks.get('sea_level_rise', 0) or 0),
                typhoon=int(risks.get('typhoon', 0) or 0),
                wildfire=int(risks.get('wildfire', 0) or 0)
            )

            aal_scores = AALScores(
                extreme_heat=float(aal_by_risk.get('extreme_heat', 0.0) or 0.0),
                extreme_cold=float(aal_by_risk.get('extreme_cold', 0.0) or 0.0),
                river_flood=float(aal_by_risk.get('river_flood', 0.0) or 0.0),
                urban_flood=float(aal_by_risk.get('urban_flood', 0.0) or 0.0),
                drought=float(aal_by_risk.get('drought', 0.0) or 0.0),
                water_stress=float(aal_by_risk.get('water_stress', 0.0) or 0.0),
                sea_level_rise=float(aal_by_risk.get('sea_level_rise', 0.0) or 0.0),
                typhoon=float(aal_by_risk.get('typhoon', 0.0) or 0.0),
                wildfire=float(aal_by_risk.get('wildfire', 0.0) or 0.0)
            )

            # advantages/disadvantages는 text[] 배열
            advantages = candidate.get('advantages', []) or []
            disadvantages = candidate.get('disadvantages', []) or []

            candidate_result = CandidateResult(
                candidateId=candidate['candidate_id'],
                latitude=float(candidate['latitude']),
                longitude=float(candidate['longitude']),
                jibunAddress=candidate.get('jibun_address'),
                roadAddress=candidate.get('road_address'),
                riskscore=int(candidate.get('risk_score') or 0),
                aalscore=float(candidate.get('aal') or 0.0),
                **{
                    "physical-risk-scores": physical_risk_scores,
                    "aal-scores": aal_scores
                },
                pros=advantages[0] if advantages else "장점 정보 없음",
                cons=disadvantages[0] if disadvantages else "단점 정보 없음"
            )

            return RelocationSimulationResponse(
                siteId=request.site_id,
                candidate=candidate_result
            )

        except Exception as e:
            self.logger.error(f"[COMPARE] Failed to compare relocation: {e}", exc_info=True)
            # DB 조회 실패 시 기존 로직으로 폴백
            return await self.compare_relocation(request)

    async def run_climate_simulation(
            self, request: ClimateSimulationRequest
        ) -> ClimateSimulationResponse:
            """
            [DB 연동] 기후 시뮬레이션 실행
            1. 행정구역별(주요 지점) Hazard 점수 조회 (hazard_results)
            2. 사업장별(Site ID) AAL 조회 (aal_scaled_results)
            """
            self.logger.info(f"[SIMULATION] 시뮬레이션 시작: scenario={request.scenario}, hazard={request.hazard_type}")

            try:
                db = DatabaseManager()
                
                # 1. 시나리오에 따른 동적 컬럼명 결정 (예: ssp585_score_100, ssp585_final_aal)
                # request.scenario가 Enum인 경우 문자열 처리
                scenario_str = str(request.scenario.value) if hasattr(request.scenario, "value") else str(request.scenario)
                # "SSP5-8.5" -> "ssp585" 변환
                prefix = scenario_str.lower().replace("ssp", "ssp").replace("-", "").replace(".", "").replace("_", "")
                if "ssp" not in prefix: prefix = "ssp585" # fallback
                
                score_col = f"{prefix}_score_100"
                aal_col = f"{prefix}_final_aal"

                # =========================================================
                # Step A. 사업장(Site) AAL 조회
                # =========================================================
                site_aals_map = {}
                
                if request.site_ids:
                    # UUID 리스트를 문자열 튜플로 변환
                    site_ids_tuple = tuple(str(sid) for sid in request.site_ids)
                    
                    query_site = f"""
                        SELECT 
                            site_id, 
                            target_year, 
                            {aal_col} as aal_value
                        FROM aal_scaled_results
                        WHERE site_id IN %s
                        AND risk_type = %s
                        AND target_year BETWEEN %s AND %s
                    """
                    
                    # DBManager execute_query 사용
                    site_rows = db.execute_query(query_site, (site_ids_tuple, request.hazard_type, str(request.start_year), str(request.end_year)))
                    
                    for row in site_rows:
                        s_id = str(row['site_id']) # UUID -> str
                        year = str(row['target_year'])
                        val = float(row['aal_value'] or 0.0)

                        if s_id not in site_aals_map:
                            site_aals_map[s_id] = {}
                        site_aals_map[s_id][year] = val

                # =========================================================
                # Step B. 행정구역(Region) 점수 조회 (좌표 기반)
                # =========================================================
                region_scores_map = {}
                
                # 1. 매퍼에서 좌표 리스트 추출
                # (lat, lng) -> region_code 역매핑
                coord_to_code = {}
                coords_list = []
                
                for code, coord in REGION_COORD_MAP.items():
                    lat, lng = coord["lat"], coord["lng"]
                    coord_to_code[(lat, lng)] = code
                    coords_list.append(f"({lat}, {lng})")
                
                if coords_list:
                    # 각 지역(좌표)에 대해 최근접 hazard 값을 조회
                    # UNION ALL을 사용하여 각 좌표별로 최근접 값을 찾음
                    for code, coord in REGION_COORD_MAP.items():
                        target_lat = coord["lat"]
                        target_lng = coord["lng"]

                        # 각 연도별로 최근접 hazard 값 조회
                        query_region = f"""
                            SELECT DISTINCT ON (target_year)
                                target_year,
                                {score_col} as score,
                                latitude,
                                longitude
                            FROM hazard_results
                            WHERE risk_type = %s
                            AND target_year BETWEEN %s AND %s
                            ORDER BY target_year, (
                                POW(latitude - %s, 2) + POW(longitude - %s, 2)
                            ) ASC
                        """

                        try:
                            region_rows = db.execute_query(
                                query_region,
                                (request.hazard_type, str(request.start_year), str(request.end_year), target_lat, target_lng)
                            )

                            # 결과를 region_scores_map에 저장
                            if code not in region_scores_map:
                                region_scores_map[code] = {}

                            for row in region_rows:
                                year = str(row['target_year'])
                                score = float(row['score'] or 0.0)
                                region_scores_map[code][year] = score

                        except Exception as e:
                            self.logger.warning(f"[SIMULATION] 지역 {code} 조회 실패: {e}")
                            continue

                # =========================================================
                # Step C. 응답 반환
                # =========================================================
                return ClimateSimulationResponse(
                    regionScores=region_scores_map,
                    siteAALs=site_aals_map
                )

            except Exception as e:
                self.logger.error(f"[SIMULATION] 시뮬레이션 실패: {e}", exc_info=True)
                # 에러 발생 시 빈 결과라도 반환하거나 HTTPException 발생
                raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")