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
        [Query Optimization Applied]
        기존: Site별 Loop -> Risk Type별 Loop -> H, E, V 개별 조회 (N * 9 * 3 쿼리)
        변경: 모든 Site와 연관된 H, E, V 데이터를 단일 쿼리로 조인하여 조회 (1 쿼리)
        """
        logger.debug(f"Querying database for dashboard summary for site_ids count={len(site_ids)}")

        if not site_ids:
            return DashboardSummaryResponse(mainClimateRisk="No data", sites=[])

        # 1. 상수 정의
        RISK_TYPES = [
            'extreme_heat', 'extreme_cold', 'river_flood', 'urban_flood',
            'drought', 'water_stress', 'sea_level_rise', 'typhoon', 'wildfire'
        ]
        
        RISK_TYPE_KR_MAPPING = {
            'extreme_heat': '폭염', 'extreme_cold': '한파', 'wildfire': '산불',
            'drought': '가뭄', 'water_stress': '물부족', 'sea_level_rise': '해안침수',
            'river_flood': '내륙침수', 'urban_flood': '도시침수', 'typhoon': '태풍'
        }

        TARGET_YEAR = 2040

        # 2. 쿼리 파라미터 준비
        # site_ids를 튜플 문자열로 변환
        site_ids_tuple = tuple(str(sid) for sid in site_ids)
        risk_types_tuple = tuple(RISK_TYPES)
        
        # 3. 최적화된 단일 쿼리 작성 (JOIN 활용)
        # Site를 기준으로 Hazard(위치 기반), Exposure/Vulnerability(ID 기반) 테이블을 LEFT JOIN
        query = """
            SELECT 
                s.site_id,
                h.risk_type,
                COALESCE(h.ssp245_score_100, 0) as hazard,
                COALESCE(e.exposure_score, 0) as exposure,
                COALESCE(v.vulnerability_score, 0) as vulnerability
            FROM site s
            -- 1. Hazard Results Join (위치 기반: lat, lon)
            LEFT JOIN hazard_results h 
                ON s.latitude = h.latitude 
                AND s.longitude = h.longitude 
                AND h.target_year = %s
            -- 2. Exposure Results Join (사이트 ID 및 리스크 타입 매칭)
            LEFT JOIN exposure_results e 
                ON s.site_id = e.site_id 
                AND h.risk_type = e.risk_type 
                AND e.target_year = h.target_year
            -- 3. Vulnerability Results Join (사이트 ID 및 리스크 타입 매칭)
            LEFT JOIN vulnerability_results v 
                ON s.site_id = v.site_id 
                AND h.risk_type = v.risk_type 
                AND v.target_year = h.target_year
            WHERE s.site_id IN %s
              AND h.risk_type IN %s
        """

        try:
            # execute_query가 튜플 파라미터를 처리하는 방식에 따라 분기 (여기선 일반적인 방식 가정)
            rows = self.db_manager.execute_query(query, (TARGET_YEAR, site_ids_tuple, risk_types_tuple))
        except Exception as e:
            logger.error(f"Optimized dashboard query failed: {e}", exc_info=True)
            return DashboardSummaryResponse(mainClimateRisk="Error", sites=[])

        if not rows:
             return DashboardSummaryResponse(mainClimateRisk="No data", sites=[])

        # 4. 데이터 집계 처리 (Python 메모리 연산)
        # 구조: site_scores[site_id] = [score1, score2, ...]
        site_scores = {str(sid): [] for sid in site_ids}
        
        # 구조: risk_type_sums[risk_type] = [score_sum, count]
        risk_type_agg = {rt: {'sum': 0.0, 'count': 0} for rt in RISK_TYPES}

        for row in rows:
            sid = str(row['site_id'])
            rtype = row['risk_type']
            
            # 리스크 점수 계산: (H * E * V) / 10000
            # DB에서 가져온 값은 Decimal일 수 있으므로 float 변환
            h = float(row['hazard'])
            e = float(row['exposure'])
            v = float(row['vulnerability'])
            
            physical_risk_score = (h * e * v) / 10000.0
            
            # 사이트별 점수 목록에 추가
            if sid in site_scores:
                site_scores[sid].append(physical_risk_score)
            
            # 리스크 타입별 합계 집계
            if rtype in risk_type_agg:
                risk_type_agg[rtype]['sum'] += physical_risk_score
                risk_type_agg[rtype]['count'] += 1

        # 5. 결과 객체 생성
        final_site_summaries = []
        
        # 각 사업장별 평균 점수 계산 (totalRiskScore)
        for sid in site_ids:
            sid_str = str(sid)
            scores = site_scores.get(sid_str, [])
            
            # 데이터가 하나도 없으면 0점
            avg_score = sum(scores) / len(scores) if scores else 0.0
            
            final_site_summaries.append(SiteRiskScore(
                siteId=sid,
                totalRiskScore=round(avg_score, 2)
            ))

        # 6. Main Climate Risk 도출
        # 전체 사업장에서 평균 점수가 가장 높은 리스크 타입 선정
        max_avg_score = -1.0
        main_risk_key = None

        for rtype, agg in risk_type_agg.items():
            if agg['count'] > 0:
                current_avg = agg['sum'] / agg['count']
                if current_avg > max_avg_score:
                    max_avg_score = current_avg
                    main_risk_key = rtype
        
        if main_risk_key and max_avg_score > 0:
            main_climate_risk = RISK_TYPE_KR_MAPPING.get(main_risk_key, main_risk_key)
        else:
            main_climate_risk = "분석 데이터 없음" if not rows else "Safe" # 혹은 다른 기본값

        logger.info(f"Dashboard summary completed: {len(final_site_summaries)} sites processed via optimized query.")

        return DashboardSummaryResponse(
            mainClimateRisk=main_climate_risk,
            sites=final_site_summaries
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