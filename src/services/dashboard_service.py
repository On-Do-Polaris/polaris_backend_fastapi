import logging
from typing import Optional, List
from uuid import UUID
from collections import Counter

from src.core.config import settings
from src.schemas.dashboard import DashboardSummaryResponse, SiteRiskScore
from ai_agent.utils.database import DatabaseManager

logger = logging.getLogger(__name__)


class DashboardService:
    """대시보드 서비스"""

    def __init__(self):
        """서비스 초기화"""
        if not settings.USE_MOCK_DATA:
            self.db_manager = DatabaseManager()
            logger.info("DatabaseManager initialized for DashboardService")

    async def get_dashboard_summary(self, site_ids: List[UUID]) -> DashboardSummaryResponse:
        """
        대시보드 요약 정보 조회

        Args:
            user_id: 사용자 ID. 이 값이 제공되어야 DB 조회가 가능합니다.

        Returns:
            DashboardSummaryResponse: 대시보드 요약 정보
        """
        logger.info(f"대시보드 요약 정보 조회 시작 (site_ids count={len(site_ids)})")
        if settings.USE_MOCK_DATA:
            return self._get_mock_dashboard_summary()

        if not site_ids:
            logger.warning("Site IDs are required for database query, but none were provided.")
            # 사용자 ID가 없을 경우 빈 목록을 반환하거나 에러를 발생시킬 수 있습니다.
            return DashboardSummaryResponse(main_climate_risk="N/A", sites=[])

        return self._get_db_dashboard_summary(site_ids)

    def _get_db_dashboard_summary(self, site_ids: List[UUID]) -> DashboardSummaryResponse:
        """
        실제 DB에서 대시보드 요약 데이터를 조회하여 반환
        입력받은 site_ids에 대해 2040년 SSP2-4.5 시나리오 기준 리스크 분석
        """
        logger.debug(f"Querying database for dashboard summary for site_ids count={len(site_ids)}")

        if not site_ids:
            return DashboardSummaryResponse(mainClimateRisk="No data", sites=[])

        # 9개 리스크 타입 정의
        RISK_TYPES = [
            'extreme_heat', 'extreme_cold', 'river_flood', 'urban_flood',
            'drought', 'water_stress', 'sea_level_rise', 'typhoon', 'wildfire'
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

        # 분석 기준 설정: 2040년, SSP2-4.5
        TARGET_YEAR = 2040
        
        # 1. 전달받은 site_ids에 해당하는 사업장의 좌표(Lat, Lon) 조회
        # Hazard 데이터는 격자(좌표) 기반이므로 좌표 정보가 필수입니다.
        site_ids_str = tuple(str(sid) for sid in site_ids)
        placeholder = ",".join(["%s"] * len(site_ids_str))
        
        sites_query = f"""
            SELECT site_id, latitude, longitude
            FROM site
            WHERE site_id IN ({placeholder})
        """

        try:
            # 리스트가 1개일 경우 튜플 처리를 위해 분기 혹은 바로 실행
            sites = self.db_manager.execute_query(sites_query, site_ids_str)
        except Exception as e:
            logger.error(f"Database query failed for sites: {e}", exc_info=True)
            return DashboardSummaryResponse(mainClimateRisk="Error", sites=[])

        if not sites:
            return DashboardSummaryResponse(mainClimateRisk="No data", sites=[])

        sites_summary: List[SiteRiskScore] = []
        all_risk_type_scores = {risk_type: [] for risk_type in RISK_TYPES}

        # 2. 각 사업장별로 9개 리스크에 대한 점수 계산
        for site in sites:
            site_id = site['site_id']
            # Decimal 타입을 float로 변환
            latitude = float(site['latitude'])
            longitude = float(site['longitude'])

            risk_scores = []

            for risk_type in RISK_TYPES:
                try:
                    # [Hazard] 격자 기반 조회 (ssp245, 2040년)
                    # Datawarehouse ERD: hazard_results 
                    hazard_query = """
                        SELECT ssp245_score_100
                        FROM hazard_results
                        WHERE latitude = %s AND longitude = %s
                          AND risk_type = %s AND target_year = %s
                        LIMIT 1
                    """
                    hazard_result = self.db_manager.execute_query(
                        hazard_query,
                        (latitude, longitude, risk_type, TARGET_YEAR)
                    )
                    # 데이터가 없으면 0점 처리
                    hazard = float(hazard_result[0]['ssp245_score_100']) if hazard_result else 0.0

                    # [Exposure] 사업장 ID 기반 조회
                    # Datawarehouse ERD: exposure_results 
                    exposure_query = """
                        SELECT exposure_score
                        FROM exposure_results
                        WHERE site_id = %s AND risk_type = %s AND target_year = %s
                        LIMIT 1
                    """
                    exposure_result = self.db_manager.execute_query(
                        exposure_query,
                        (str(site_id), risk_type, TARGET_YEAR)
                    )
                    exposure = float(exposure_result[0]['exposure_score']) if exposure_result else 0.0

                    # [Vulnerability] 사업장 ID 기반 조회
                    # Datawarehouse ERD: vulnerability_results 
                    vulnerability_query = """
                        SELECT vulnerability_score
                        FROM vulnerability_results
                        WHERE site_id = %s AND risk_type = %s AND target_year = %s
                        LIMIT 1
                    """
                    vulnerability_result = self.db_manager.execute_query(
                        vulnerability_query,
                        (str(site_id), risk_type, TARGET_YEAR)
                    )
                    vulnerability = float(vulnerability_result[0]['vulnerability_score']) if vulnerability_result else 0.0

                    # [Physical Risk Calculation]
                    # Formula: (Hazard * Exposure * Vulnerability) / 10000
                    physical_risk_score = (hazard * exposure * vulnerability) / 10000.0
                    
                    risk_scores.append(physical_risk_score)
                    all_risk_type_scores[risk_type].append(physical_risk_score)

                except Exception as e:
                    logger.warning(f"Failed to calculate risk for site {site_id}, risk_type {risk_type}: {e}")
                    risk_scores.append(0.0)
                    all_risk_type_scores[risk_type].append(0.0)

            # 해당 사업장의 통합 점수 (9개 리스크 평균)
            avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0

            sites_summary.append(SiteRiskScore(
                siteId=site_id,
                totalRiskScore=round(avg_risk_score, 2)  # 소수점 2자리 반올림
            ))

        # 3. Main Climate Risk 도출 (전체 사업장에서 가장 평균 점수가 높은 리스크)
        risk_type_averages = {}
        for risk_type, scores in all_risk_type_scores.items():
            if scores:
                risk_type_averages[risk_type] = sum(scores) / len(scores)
            else:
                risk_type_averages[risk_type] = 0.0

        if risk_type_averages:
            main_risk_type = max(risk_type_averages, key=risk_type_averages.get)
            # 점수가 모두 0인 경우 처리
            if risk_type_averages[main_risk_type] == 0:
                main_climate_risk = "분석 데이터 없음"
            else:
                main_climate_risk = RISK_TYPE_KR_MAPPING.get(main_risk_type, main_risk_type)
        else:
            main_climate_risk = "Not available"

        logger.info(f"Dashboard summary completed: {len(sites_summary)} sites, main risk: {main_climate_risk}")

        return DashboardSummaryResponse(
            mainClimateRisk=main_climate_risk,
            sites=sites_summary
        )

    def _get_mock_dashboard_summary(self) -> DashboardSummaryResponse:
        """Mock 대시보드 요약 데이터 반환"""
        logger.debug("Mock 대시보드 데이터 반환")

        sites = [
            SiteSummary(
                siteId=UUID("11111111-1111-1111-1111-111111111111"),
                siteName="서울 본사",
                siteType="본사",
                latitude=37.5665,
                longitude=126.9780,
                jibunAddress="서울특별시 강남구 역삼동 123-45",
                roadAddress="서울특별시 강남구 테헤란로 123",
                totalRiskScore=75
            ),
            SiteSummary(
                siteId=UUID("22222222-2222-2222-2222-222222222222"),
                siteName="부산 공장",
                siteType="공장",
                latitude=35.1796,
                longitude=129.0756,
                jibunAddress="부산광역시 해운대구 우동 456-78",
                roadAddress="부산광역시 해운대구 해운대로 456",
                totalRiskScore=82
            ),
            SiteSummary(
                siteId=UUID("33333333-3333-3333-3333-333333333333"),
                siteName="대전 연구소",
                siteType="연구소",
                latitude=36.3504,
                longitude=127.3845,
                jibunAddress="대전광역시 유성구 궁동 789-12",
                roadAddress="대전광역시 유성구 대학로 789",
                totalRiskScore=65
            ),
            SiteSummary(
                siteId=UUID("44444444-4444-4444-4444-444444444444"),
                siteName="광주 물류센터",
                siteType="물류센터",
                latitude=35.1595,
                longitude=126.8526,
                jibunAddress="광주광역시 북구 문흥동 234-56",
                roadAddress="광주광역시 북구 첨단과기로 234",
                totalRiskScore=70
            )
        ]

        main_climate_risk = "폭염"

        return DashboardSummaryResponse(
            mainClimateRisk=main_climate_risk,
            sites=sites
        )
        """
        실제 DB에서 대시보드 요약 데이터를 조회하여 반환 (성능 최적화 버전)
        - 기존: N(사업장) * 9(리스크) * 3(테이블) = 270+회 쿼리
        - 변경: JOIN을 사용하여 1회 쿼리로 조회
        """
        logger.debug(f"Querying database for dashboard summary for user_id={user_id}")

        # 9개 리스크 타입 정의
        RISK_TYPES = [
            'extreme_heat', 'extreme_cold', 'river_flood', 'urban_flood',
            'drought', 'water_stress', 'sea_level_rise', 'typhoon', 'wildfire'
        ]

        # 영문 → 한글 매핑
        RISK_TYPE_KR_MAPPING = {
            'extreme_heat': '폭염', 'extreme_cold': '한파', 'wildfire': '산불',
            'drought': '가뭄', 'water_stress': '물부족', 'sea_level_rise': '해안침수',
            'river_flood': '내륙침수', 'urban_flood': '도시침수', 'typhoon': '태풍'
        }

        TARGET_YEAR = 2040
        SSP_SCENARIO = 'ssp245' # 컬럼명에 이미 포함됨 (ssp245_score_100)

        # ---------------------------------------------------------
        # [최적화] JOIN을 사용하여 사이트 정보와 리스크 점수를 한 번에 조회
        # ---------------------------------------------------------
        query = """
            SELECT 
                s.site_id,
                s.name,
                s.site_type,
                s.latitude,
                s.longitude,
                s.jibun_address,
                s.road_address,
                e.risk_type,
                COALESCE(h.ssp245_score_100, 0) as h_score,
                COALESCE(e.exposure_score, 0) as e_score,
                COALESCE(v.vulnerability_score, 0) as v_score
            FROM site s
            -- 1. Exposure 테이블 조인 (Site 기준)
            LEFT JOIN exposure_results e ON 
                s.site_id = e.site_id 
                AND e.target_year = %s
                AND e.risk_type = ANY(%s)
            -- 2. Vulnerability 테이블 조인 (Site, Risk 기준)
            LEFT JOIN vulnerability_results v ON 
                e.site_id = v.site_id 
                AND e.risk_type = v.risk_type 
                AND e.target_year = v.target_year
            -- 3. Hazard 테이블 조인 (위경도, Risk 기준)
            LEFT JOIN hazard_results h ON 
                s.latitude = h.latitude 
                AND s.longitude = h.longitude 
                AND e.risk_type = h.risk_type 
                AND e.target_year = h.target_year
            WHERE s.user_id = %s
        """

        try:
            # risk_types 리스트를 SQL 배열 파라미터로 전달
            params = (TARGET_YEAR, RISK_TYPES, str(user_id))
            rows = self.db_manager.execute_query(query, params)
        except Exception as e:
            logger.error(f"Database query failed: {e}", exc_info=True)
            return DashboardSummaryResponse(main_climate_risk="Error", sites=[])

        if not rows:
            return DashboardSummaryResponse(main_climate_risk="No data", sites=[])

        # ---------------------------------------------------------
        # 데이터 가공 (메모리 상에서 그룹화)
        # ---------------------------------------------------------
        
        # site_id를 키로 하여 데이터 그룹화
        sites_data_map = {}
        
        # 전체 통계용 (Main Risk 계산)
        global_risk_scores = {rt: [] for rt in RISK_TYPES}

        for row in rows:
            site_id = row['site_id']
            
            # 사이트 메타데이터 초기화 (최초 1회)
            if site_id not in sites_data_map:
                sites_data_map[site_id] = {
                    'info': {
                        'siteId': site_id,
                        'siteName': row['name'],
                        'siteType': row['site_type'],
                        'latitude': row['latitude'],
                        'longitude': row['longitude'],
                        'jibunAddress': row['jibun_address'],
                        'roadAddress': row['road_address']
                    },
                    'scores': [] # 개별 리스크 점수들 저장
                }

            # 리스크 점수 계산 (risk_type이 있는 경우만)
            risk_type = row.get('risk_type')
            if risk_type:
                h = row['h_score']
                e = row['e_score']
                v = row['v_score']
                
                # Physical Risk Score = H × E × V / 10000
                score = (h * e * v) / 10000.0
                
                sites_data_map[site_id]['scores'].append(score)
                
                if risk_type in global_risk_scores:
                    global_risk_scores[risk_type].append(score)

        # ---------------------------------------------------------
        # 응답 객체 생성
        # ---------------------------------------------------------
        sites_summary: List[SiteSummary] = []

        for site_data in sites_data_map.values():
            scores = site_data['scores']
            
            # [점수 로직] 기존 유지: 평균 (Average)
            # 만약 점수가 너무 낮게 나온다면 max(scores)로 변경 고려
            total_risk_score = int(sum(scores) / len(scores)) if scores else 0
            
            summary = SiteSummary(
                **site_data['info'], # dict unpacking
                totalRiskScore=total_risk_score
            )
            sites_summary.append(summary)

        # Main Climate Risk 계산 (전체 평균 중 최대)
        risk_type_averages = {}
        for risk_type, scores in global_risk_scores.items():
            if scores:
                risk_type_averages[risk_type] = sum(scores) / len(scores)
            else:
                risk_type_averages[risk_type] = 0

        if risk_type_averages and max(risk_type_averages.values()) > 0:
            main_risk_type = max(risk_type_averages, key=risk_type_averages.get)
            main_climate_risk = RISK_TYPE_KR_MAPPING.get(main_risk_type, main_risk_type)
        else:
            main_climate_risk = "분석 불가"

        logger.info(f"Dashboard summary optimized query completed: {len(sites_summary)} sites")

        return DashboardSummaryResponse(
            mainClimateRisk=main_climate_risk,
            sites=sites_summary
        )