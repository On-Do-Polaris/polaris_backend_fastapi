from uuid import UUID
from datetime import datetime
from typing import List, Optional

from src.core.config import settings
from src.schemas.disaster_history import (
    DisasterHistoryRecord,
    DisasterHistoryListResponse,
    DisasterHistoryFilter,
    DisasterStatistics,
    DisasterSeverity,
)
from src.schemas.common import HazardType


class DisasterHistoryService:
    """재해이력 서비스 - DB에서 재해이력 조회"""

    def __init__(self):
        """서비스 초기화"""
        # TODO: DB connection pool 초기화
        self._db_connection = None

    async def get_disaster_history(
        self, filters: DisasterHistoryFilter
    ) -> DisasterHistoryListResponse:
        """
        재해이력 목록 조회

        Args:
            filters: 필터 조건 (site_id, disaster_type, severity, date_range, pagination)

        Returns:
            DisasterHistoryListResponse: 재해이력 목록과 전체 개수
        """
        if settings.USE_MOCK_DATA:
            return self._get_mock_disaster_history(filters)

        # TODO: 실제 DB 쿼리 구현
        # query = """
        #     SELECT
        #         id, site_id, disaster_type, occurred_at, severity,
        #         damage_amount, casualties, description, recovery_duration,
        #         location, weather_condition, created_at, updated_at
        #     FROM disaster_history
        #     WHERE 1=1
        #         AND ($1::uuid IS NULL OR site_id = $1)
        #         AND ($2::text IS NULL OR disaster_type = $2)
        #         AND ($3::text IS NULL OR severity = $3)
        #         AND ($4::timestamp IS NULL OR occurred_at >= $4)
        #         AND ($5::timestamp IS NULL OR occurred_at <= $5)
        #     ORDER BY occurred_at DESC
        #     LIMIT $6 OFFSET $7
        # """
        # async with self._db_connection.cursor() as cursor:
        #     await cursor.execute(query, (
        #         filters.site_id,
        #         filters.disaster_type.value if filters.disaster_type else None,
        #         filters.severity.value if filters.severity else None,
        #         filters.start_date,
        #         filters.end_date,
        #         filters.limit,
        #         filters.offset
        #     ))
        #     rows = await cursor.fetchall()
        #     total = await self._get_total_count(filters)
        #
        # records = [DisasterHistoryRecord(**row) for row in rows]
        # return DisasterHistoryListResponse(total=total, data=records)

        raise NotImplementedError("DB connection not implemented yet")

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
        """Mock 데이터 반환"""
        from uuid import uuid4

        mock_records = [
            DisasterHistoryRecord(
                id=uuid4(),
                site_id=filters.site_id or uuid4(),
                disaster_type=HazardType.TYPHOON,
                occurred_at=datetime(2023, 8, 15, 10, 30),
                severity=DisasterSeverity.SEVERE,
                damage_amount=500000000,  # 5억원
                casualties=0,
                description="태풍 카눈으로 인한 지붕 파손 및 침수 피해",
                recovery_duration=14,
                location="건물 1동",
                weather_condition="강풍 및 폭우",
            ),
            DisasterHistoryRecord(
                id=uuid4(),
                site_id=filters.site_id or uuid4(),
                disaster_type=HazardType.INLAND_FLOOD,
                occurred_at=datetime(2023, 7, 10, 14, 0),
                severity=DisasterSeverity.MODERATE,
                damage_amount=150000000,  # 1.5억원
                casualties=0,
                description="집중호우로 인한 지하주차장 침수",
                recovery_duration=7,
                location="지하 1층 주차장",
                weather_condition="시간당 80mm 집중호우",
            ),
            DisasterHistoryRecord(
                id=uuid4(),
                site_id=filters.site_id or uuid4(),
                disaster_type=HazardType.HIGH_TEMPERATURE,
                occurred_at=datetime(2023, 8, 1, 15, 0),
                severity=DisasterSeverity.MINOR,
                damage_amount=5000000,  # 500만원
                casualties=2,  # 온열질환자
                description="폭염으로 인한 옥외 작업자 온열질환 발생",
                recovery_duration=1,
                location="야외 작업장",
                weather_condition="기온 38도, 체감온도 42도",
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
        if filters.start_date:
            filtered_records = [
                r for r in filtered_records if r.occurred_at >= filters.start_date
            ]
        if filters.end_date:
            filtered_records = [
                r for r in filtered_records if r.occurred_at <= filters.end_date
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
            most_common_type=HazardType.TYPHOON,
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
