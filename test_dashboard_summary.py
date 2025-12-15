"""Dashboard Summary 기능 테스트"""
import asyncio
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.services.dashboard_service import DashboardService
from src.core.config import settings


async def test_mock_dashboard():
    """Mock 데이터로 Dashboard Summary 테스트"""
    print("=" * 80)
    print("Dashboard Summary Mock 데이터 테스트")
    print("=" * 80)

    # Mock 모드 활성화
    settings.USE_MOCK_DATA = True

    service = DashboardService()
    result = await service.get_dashboard_summary()

    print(f"\n주요 기후 리스크: {result.mainClimateRisk}")
    print(f"\n총 사업장 수: {len(result.sites)}")
    print("\n사업장 목록:")
    print("-" * 80)

    for i, site in enumerate(result.sites, 1):
        print(f"\n{i}. {site.siteName}")
        print(f"   - 사업장 ID: {site.siteId}")
        print(f"   - 사업장 유형: {site.siteType}")
        print(f"   - 위도/경도: {site.latitude}, {site.longitude}")
        print(f"   - 지번 주소: {site.jibunAddress}")
        print(f"   - 도로명 주소: {site.roadAddress}")
        print(f"   - 통합 리스크 점수: {site.totalRiskScore}/100")

    print("\n" + "=" * 80)
    print("테스트 완료!")
    print("=" * 80)

    # JSON 형식으로도 출력
    print("\nJSON 출력 예시:")
    import json
    result_dict = result.model_dump(by_alias=True)
    print(json.dumps(result_dict, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(test_mock_dashboard())
