import sys
import os
from uuid import UUID
from datetime import datetime
from typing import List, Optional

# ai_agent 모듈 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ai_agent.utils.database import DatabaseManager
from src.core.config import settings
from src.schemas.disaster_history import (
    DisasterHistoryRecord,
    DisasterHistoryListResponse,
    DisasterHistoryFilter,
    DisasterStatistics,
)


class DisasterHistoryService:
    """재해이력 서비스 - DB에서 api_emergency_messages 조회"""

    def __init__(self):
        """서비스 초기화"""
        self.db = DatabaseManager(database_url=settings.DATABASE_URL)

    async def get_disaster_history(
        self, filters: DisasterHistoryFilter
    ) -> DisasterHistoryListResponse:
        """
        재해이력 목록 조회 (api_emergency_messages 테이블)

        Args:
            filters: 필터 조건 (disaster_type, severity, region, date_range, pagination)

        Returns:
            DisasterHistoryListResponse: 재해이력 목록과 전체 개수
        """
        if settings.USE_MOCK_DATA:
            return self._get_mock_disaster_history(filters)

        # WHERE 조건 구성
        where_conditions = []
        params = []

        if filters.disaster_type:
            where_conditions.append("disaster_type = %s")
            params.append(filters.disaster_type)

        if filters.severity:
            where_conditions.append("severity = %s")
            params.append(filters.severity)

        if filters.region:
            where_conditions.append("region LIKE %s")
            params.append(f"%{filters.region}%")

        if filters.start_date:
            where_conditions.append("alert_date >= %s")
            params.append(filters.start_date.date() if hasattr(filters.start_date, 'date') else filters.start_date)

        if filters.end_date:
            where_conditions.append("alert_date <= %s")
            params.append(filters.end_date.date() if hasattr(filters.end_date, 'date') else filters.end_date)

        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        # 전체 개수 조회
        count_query = f"""
            SELECT COUNT(*) as total
            FROM api_emergency_messages
            WHERE {where_clause}
        """
        count_result = self.db.execute_query(count_query, tuple(params) if params else None)
        total = count_result[0]['total'] if count_result else 0

        # 데이터 조회
        data_query = f"""
            SELECT
                id,
                alert_date,
                disaster_type,
                severity,
                region,
                created_at,
                updated_at
            FROM api_emergency_messages
            WHERE {where_clause}
            ORDER BY alert_date DESC, id DESC
            LIMIT %s OFFSET %s
        """
        params.extend([filters.limit, filters.offset])

        rows = self.db.execute_query(data_query, tuple(params))

        # DisasterHistoryRecord 객체로 변환
        records = [
            DisasterHistoryRecord(
                id=row['id'],
                alert_date=row['alert_date'],
                disaster_type=row['disaster_type'],
                severity=row['severity'],
                region=row['region'],
                created_at=row.get('created_at'),
                updated_at=row.get('updated_at')
            )
            for row in rows
        ]

        return DisasterHistoryListResponse(total=total, data=records)

    async def get_disaster_by_id(self, disaster_id: UUID) -> Optional[DisasterHistoryRecord]:
        """
        특정 재해이력 조회

        Args:
            disaster_id: 재해이력 ID

        Returns:
            DisasterHistoryRecord or None
        """
        if settings.USE_MOCK_DATA:
            mock_data = self._get_mock_disaster_history(DisasterHistoryFilter())
            for record in mock_data.data:
                if record.id == disaster_id:
                    return record
            return None

        # TODO: 실제 DB 쿼리 구현
        # query = "SELECT * FROM disaster_history WHERE id = $1"
        # async with self._db_connection.cursor() as cursor:
        #     await cursor.execute(query, (disaster_id,))
        #     row = await cursor.fetchone()
        #     if row:
        #         return DisasterHistoryRecord(**row)
        #     return None

        raise NotImplementedError("DB connection not implemented yet")

    async def get_disaster_statistics(
        self, site_id: Optional[UUID] = None
    ) -> DisasterStatistics:
        """
        재해 통계 조회

        Args:
            site_id: 사업장 ID (None이면 전체 통계)

        Returns:
            DisasterStatistics: 재해 통계
        """
        if settings.USE_MOCK_DATA:
            return self._get_mock_statistics(site_id)

        # TODO: 실제 DB 쿼리 구현
        # query = """
        #     SELECT
        #         COUNT(*) as total_disasters,
        #         COALESCE(SUM(damage_amount), 0) as total_damage,
        #         COALESCE(SUM(casualties), 0) as total_casualties,
        #         MODE() WITHIN GROUP (ORDER BY disaster_type) as most_common_type
        #     FROM disaster_history
        #     WHERE ($1::uuid IS NULL OR site_id = $1)
        # """
        # ...

        raise NotImplementedError("DB connection not implemented yet")

    def _get_mock_disaster_history(
        self, filters: DisasterHistoryFilter
    ) -> DisasterHistoryListResponse:
        """Mock 데이터 반환 (api_emergency_messages 테이블 형식)"""
        mock_records = [
            DisasterHistoryRecord(
                id=1,
                alert_date=datetime(2023, 8, 15, 10, 30),
                disaster_type="태풍",
                severity="경보",
                region="서울특별시, 경기도",
                created_at=datetime(2023, 8, 15, 10, 30),
                updated_at=None,
            ),
            DisasterHistoryRecord(
                id=2,
                alert_date=datetime(2023, 7, 10, 14, 0),
                disaster_type="호우",
                severity="주의보",
                region="부산광역시",
                created_at=datetime(2023, 7, 10, 14, 0),
                updated_at=None,
            ),
            DisasterHistoryRecord(
                id=3,
                alert_date=datetime(2023, 8, 1, 15, 0),
                disaster_type="폭염",
                severity="경보",
                region="대구광역시, 경상북도",
                created_at=datetime(2023, 8, 1, 15, 0),
                updated_at=None,
            ),
        ]

        # 필터 적용
        filtered_records = mock_records
        if filters.disaster_type:
            filtered_records = [
                r for r in filtered_records if r.disaster_type == filters.disaster_type
            ]
        if filters.severity:
            filtered_records = [
                r for r in filtered_records if r.severity == filters.severity
            ]
        if filters.region:
            filtered_records = [
                r for r in filtered_records if filters.region in r.region
            ]
        if filters.start_date:
            filtered_records = [
                r for r in filtered_records if r.alert_date >= filters.start_date
            ]
        if filters.end_date:
            filtered_records = [
                r for r in filtered_records if r.alert_date <= filters.end_date
            ]

        # Pagination
        total = len(filtered_records)
        paginated_records = filtered_records[filters.offset : filters.offset + filters.limit]

        return DisasterHistoryListResponse(total=total, data=paginated_records)

    def _get_mock_statistics(self, site_id: Optional[UUID] = None) -> DisasterStatistics:
        """Mock 통계 데이터 반환"""
        return DisasterStatistics(
            total_disasters=3,
            total_damage=655000000,  # 6.55억원
            total_casualties=2,
            most_common_type="태풍",
            by_type={
                "태풍": {"count": 1, "damage": 500000000},
                "내륙침수": {"count": 1, "damage": 150000000},
                "폭염": {"count": 1, "damage": 5000000},
            },
            by_severity={
                "심각": {"count": 1, "damage": 500000000},
                "보통": {"count": 1, "damage": 150000000},
                "경미": {"count": 1, "damage": 5000000},
            },
        )
