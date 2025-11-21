from typing import Optional
from datetime import datetime

from src.schemas.meta import HazardTypeInfo, HealthCheckResponse


class MetaService:
    """메타 서비스"""

    async def get_hazards(self, category: Optional[str]) -> list[HazardTypeInfo]:
        """위험요인 목록 조회"""
        hazards = [
            HazardTypeInfo(
                code="extreme_heat",
                name="폭염",
                nameEn="Extreme Heat",
                category="temperature",
                description="일 최고기온 33도 이상이 2일 이상 지속되는 현상",
                availableMetrics=["온도", "빈도", "지속시간"],
            ),
            HazardTypeInfo(
                code="extreme_cold",
                name="한파",
                nameEn="Cold Wave",
                category="temperature",
                description="일 최저기온이 영하 12도 이하가 2일 이상 지속",
                availableMetrics=["온도", "빈도", "지속시간"],
            ),
            HazardTypeInfo(
                code="typhoon",
                name="태풍",
                nameEn="Typhoon",
                category="wind",
                description="열대성 저기압으로 인한 강풍 및 폭우",
                availableMetrics=["풍속", "강수량", "빈도"],
            ),
            HazardTypeInfo(
                code="flood",
                name="홍수",
                nameEn="Flood",
                category="water",
                description="하천 범람으로 인한 침수",
                availableMetrics=["강수량", "수위", "빈도"],
            ),
            HazardTypeInfo(
                code="drought",
                name="가뭄",
                nameEn="Drought",
                category="water",
                description="장기간 강수량 부족으로 인한 물 부족",
                availableMetrics=["강수량", "지속시간"],
            ),
            HazardTypeInfo(
                code="wildfire",
                name="산불",
                nameEn="Wildfire",
                category="other",
                description="산림 지역의 화재",
                availableMetrics=["건조도", "풍속", "빈도"],
            ),
            HazardTypeInfo(
                code="sea_level_rise",
                name="해안침수",
                nameEn="Coastal Flood",
                category="water",
                description="해수면 상승 및 폭풍해일로 인한 침수",
                availableMetrics=["해수면", "빈도"],
            ),
            HazardTypeInfo(
                code="urban_flood",
                name="도시침수",
                nameEn="Urban Flood",
                category="water",
                description="도시 지역 배수 용량 초과로 인한 침수",
                availableMetrics=["강수량", "빈도"],
            ),
            HazardTypeInfo(
                code="water_stress",
                name="물부족",
                nameEn="Water Scarcity",
                category="water",
                description="용수 공급 부족",
                availableMetrics=["가용량", "수요량"],
            ),
        ]

        if category:
            hazards = [h for h in hazards if h.category == category]

        return hazards

    async def health_check(self) -> HealthCheckResponse:
        """헬스체크"""
        # TODO: ai_agent 상태 확인
        return HealthCheckResponse(
            status="healthy",
            version="1.0.0",
            agentStatus="ready",
            activeJobs=0,
            timestamp=datetime.now(),
        )
