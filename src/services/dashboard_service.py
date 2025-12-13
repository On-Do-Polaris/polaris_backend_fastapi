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

        query = """
        WITH LatestRiskScores AS (
            -- 각 사업장의 최신 리스크 점수를 찾습니다.
            SELECT
                prs.site_id,
                prs.total_risk_score,
                ROW_NUMBER() OVER(PARTITION BY prs.site_id ORDER BY prs.created_at DESC) as rn_risk
            FROM physical_risk_summary prs
        ),
        MainSiteHazards AS (
            -- 각 사업장의 가장 점수가 높은 위험 요소를 찾습니다.
            SELECT
                hr.site_id,
                hr.risk_type,
                ROW_NUMBER() OVER(PARTITION BY hr.site_id ORDER BY hr.hazard_score DESC, hr.calculated_at DESC) as rn_hazard
            FROM hazard_results hr
        )
        -- 기본 사업장 정보와 위에서 계산된 리스크/위험 정보를 조합합니다.
        SELECT
            s.site_id,
            s.name AS site_name,
            s.site_type,
            s.latitude,
            s.longitude,
            s.address AS location,
            COALESCE(lrs.total_risk_score, 0) AS total_risk_score,
            msh.risk_type AS main_hazard
        FROM site s
        LEFT JOIN LatestRiskScores lrs ON s.site_id = lrs.site_id AND lrs.rn_risk = 1
        LEFT JOIN MainSiteHazards msh ON s.site_id = msh.site_id AND msh.rn_hazard = 1
        WHERE s.user_id = %s;
        """

        try:
            results = self.db_manager.execute_query(query, (str(user_id),))
        except Exception as e:
            logger.error(f"Database query failed for dashboard summary: {e}", exc_info=True)
            # DB 오류 시 비어있는 응답 반환
            return DashboardSummaryResponse(main_climate_risk="Error", sites=[])

        if not results:
            return DashboardSummaryResponse(main_climate_risk="No data", sites=[])
        
        sites_summary: List[SiteSummary] = []
        main_hazards = []

        for row in results:
            sites_summary.append(SiteSummary(
                siteId=row['site_id'],
                siteName=row['site_name'],
                siteType=row['site_type'],
                latitude=row['latitude'],
                longitude=row['longitude'],
                location=row['location'],
                totalRiskScore=int(row['total_risk_score'])
            ))
            if row['main_hazard']:
                main_hazards.append(row['main_hazard'])

        # 가장 빈번하게 발생한 주요 리스크를 찾습니다.
        if not main_hazards:
            main_climate_risk = "Not available"
        else:
            most_common_hazard = Counter(main_hazards).most_common(1)
            main_climate_risk = most_common_hazard[0][0] if most_common_hazard else "Not available"

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
                location="서울특별시 강남구",
                totalRiskScore=75
            ),
            SiteSummary(
                siteId=UUID("22222222-2222-2222-2222-222222222222"),
                siteName="부산 공장",
                siteType="공장",
                latitude=35.1796,
                longitude=129.0756,
                location="부산광역시 해운대구",
                totalRiskScore=82
            ),
            SiteSummary(
                siteId=UUID("33333333-3333-3333-3333-333333333333"),
                siteName="대전 연구소",
                siteType="연구소",
                latitude=36.3504,
                longitude=127.3845,
                location="대전광역시 유성구",
                totalRiskScore=65
            ),
            SiteSummary(
                siteId=UUID("44444444-4444-4444-4444-444444444444"),
                siteName="광주 물류센터",
                siteType="물류센터",
                latitude=35.1595,
                longitude=126.8526,
                location="광주광역시 북구",
                totalRiskScore=70
            )
        ]

        main_climate_risk = "극심한 고온"

        return DashboardSummaryResponse(
            mainClimateRisk=main_climate_risk,
            sites=sites
        )
