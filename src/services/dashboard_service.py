import logging
from typing import Optional, List
from uuid import UUID
from collections import Counter

from src.core.config import settings
from src.schemas.dashboard import DashboardSummaryResponse, SiteSummary
from ai_agent.utils.database import DatabaseManager

logger = logging.getLogger(__name__)


class DashboardService:
    """대시보드 서비스"""

    def __init__(self):
        """서비스 초기화"""
        if not settings.USE_MOCK_DATA:
            self.db_manager = DatabaseManager()
            logger.info("DatabaseManager initialized for DashboardService")

    async def get_dashboard_summary(self, user_id: Optional[UUID] = None) -> DashboardSummaryResponse:
        """
        대시보드 요약 정보 조회

        Args:
            user_id: 사용자 ID. 이 값이 제공되어야 DB 조회가 가능합니다.

        Returns:
            DashboardSummaryResponse: 대시보드 요약 정보
        """
        logger.info(f"대시보드 요약 정보 조회 시작 (user_id={user_id})")

        if settings.USE_MOCK_DATA:
            return self._get_mock_dashboard_summary()

        if not user_id:
            logger.warning("User ID is required for database query, but none was provided.")
            # 사용자 ID가 없을 경우 빈 목록을 반환하거나 에러를 발생시킬 수 있습니다.
            return DashboardSummaryResponse(main_climate_risk="N/A", sites=[])

        return self._get_db_dashboard_summary(user_id)

    def _get_db_dashboard_summary(self, user_id: UUID) -> DashboardSummaryResponse:
        """실제 DB에서 대시보드 요약 데이터를 조회하여 반환"""
        logger.debug(f"Querying database for dashboard summary for user_id={user_id}")

        # 9개 리스크 타입
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

        # 2040년, SSP2 시나리오 기준
        TARGET_YEAR = 2040
        SSP_SCENARIO = 'ssp245'

        # 사용자의 모든 사업장 조회
        sites_query = """
        SELECT
            site_id,
            name,
            site_type,
            latitude,
            longitude,
            jibun_address,
            road_address
        FROM site
        WHERE user_id = %s
        """

        try:
            sites = self.db_manager.execute_query(sites_query, (str(user_id),))
        except Exception as e:
            logger.error(f"Database query failed for sites: {e}", exc_info=True)
            return DashboardSummaryResponse(main_climate_risk="Error", sites=[])

        if not sites:
            return DashboardSummaryResponse(main_climate_risk="No data", sites=[])

        sites_summary: List[SiteSummary] = []
        all_risk_type_scores = {risk_type: [] for risk_type in RISK_TYPES}

        # 각 사업장별로 물리 리스크 점수 계산
        for site in sites:
            site_id = site['site_id']
            latitude = site['latitude']
            longitude = site['longitude']

            # 각 재해 유형별 H, E, V 점수 조회 및 물리 리스크 계산
            risk_scores = []

            for risk_type in RISK_TYPES:
                try:
                    # Hazard 조회 (격자 기반)
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
                    hazard = hazard_result[0]['ssp245_score_100'] if hazard_result else 0

                    # Exposure 조회 (사업장 기반)
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
                    exposure = exposure_result[0]['exposure_score'] if exposure_result else 0

                    # Vulnerability 조회 (사업장 기반)
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
                    vulnerability = vulnerability_result[0]['vulnerability_score'] if vulnerability_result else 0

                    # 물리 리스크 점수 계산: (H × E × V) / 10000
                    physical_risk_score = (hazard * exposure * vulnerability) / 10000.0
                    risk_scores.append(physical_risk_score)

                    # 전체 사업장의 재해 유형별 점수 저장 (mainClimateRisk 계산용)
                    all_risk_type_scores[risk_type].append(physical_risk_score)

                except Exception as e:
                    logger.warning(f"Failed to calculate risk for site {site_id}, risk_type {risk_type}: {e}")
                    risk_scores.append(0)
                    all_risk_type_scores[risk_type].append(0)

            # 해당 사업장의 totalRiskScore = 9개 재해 유형의 평균
            total_risk_score = int(sum(risk_scores) / len(risk_scores)) if risk_scores else 0

            sites_summary.append(SiteSummary(
                siteId=site['site_id'],
                siteName=site['name'],
                siteType=site['site_type'],
                latitude=site['latitude'],
                longitude=site['longitude'],
                jibunAddress=site.get('jibun_address'),
                roadAddress=site.get('road_address'),
                totalRiskScore=total_risk_score
            ))

        # mainClimateRisk: 모든 사업장의 재해 유형별 평균 중 가장 높은 유형
        risk_type_averages = {}
        for risk_type, scores in all_risk_type_scores.items():
            if scores:
                risk_type_averages[risk_type] = sum(scores) / len(scores)
            else:
                risk_type_averages[risk_type] = 0

        if risk_type_averages:
            main_risk_type = max(risk_type_averages, key=risk_type_averages.get)
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
