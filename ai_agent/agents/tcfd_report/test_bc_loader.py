"""
BC Loader 테스트 스크립트
API로 건축물 데이터 조회 → DB 캐시 저장

SK u-타워와 SK 판교캠퍼스 두 사이트 테스트

작성일: 2025-12-16
"""

import os
import sys
import logging
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_bc_loader")

# SK 사이트 정보
SK_SITES = [
    {
        "site_id": "22222222-2222-2222-2222-222222222222",
        "name": "SK 판교캠퍼스",
        "address": "경기도 성남시 분당구 판교로 255번길 38 SK판교 캠퍼스",
        "lat": 37.405879,
        "lon": 127.099877
    },
    {
        "site_id": "44444444-4444-4444-4444-444444444444",
        "name": "SK u-타워",
        "address": "경기도 성남시 분당구 성남대로 343번길 9 에스케이유타워",
        "lat": 37.3825,
        "lon": 127.1220
    }
]


def test_bc_loader():
    """BC Loader 테스트: API → DB 캐시"""
    logger.info("=== BC Loader 테스트 시작 ===")

    # Datawarehouse DB URL
    dw_db_url = "postgresql://skala:skala1234@localhost:5555/datawarehouse"

    try:
        from ai_agent.agents.primary_data.building_characteristics_loader import BuildingDataLoader

        loader = BuildingDataLoader(db_url=dw_db_url)

        results = {}
        for site in SK_SITES:
            logger.info(f"\n--- {site['name']} ---")
            logger.info(f"주소: {site['address']}")
            logger.info(f"좌표: lat={site['lat']}, lon={site['lon']}")

            # API 호출 → DB 캐시
            data = loader.load_and_cache(
                lat=site['lat'],
                lon=site['lon'],
                address=site['address']
            )

            if data:
                logger.info(f"✅ 데이터 조회 성공!")
                logger.info(f"  - building_count: {data.get('building_count', 'N/A')}")
                logger.info(f"  - total_floor_area: {data.get('total_floor_area_sqm', 'N/A')}")
                logger.info(f"  - structure_types: {data.get('structure_types', 'N/A')}")
                logger.info(f"  - purpose_types: {data.get('purpose_types', 'N/A')}")
                logger.info(f"  - oldest_building_age: {data.get('oldest_building_age_years', 'N/A')}")
                logger.info(f"  - seismic: with={data.get('buildings_with_seismic', 'N/A')}, without={data.get('buildings_without_seismic', 'N/A')}")
                results[site['site_id']] = data
            else:
                logger.warning(f"❌ 데이터 조회 실패")
                results[site['site_id']] = {}

        logger.info(f"\n=== BC Loader 테스트 완료: {len([v for v in results.values() if v])}개 성공 ===")
        return results

    except ImportError as e:
        logger.error(f"BC Loader 임포트 실패: {e}")
        return {}
    except Exception as e:
        logger.error(f"BC Loader 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return {}


def test_bc_loader_db_only():
    """BC Loader DB 조회만 테스트 (API 호출 X)"""
    logger.info("=== BC Loader DB 조회만 테스트 ===")

    dw_db_url = "postgresql://skala:skala1234@localhost:5555/datawarehouse"

    try:
        from ai_agent.agents.primary_data.building_characteristics_loader import BuildingDataLoader

        loader = BuildingDataLoader(db_url=dw_db_url)

        for site in SK_SITES:
            logger.info(f"\n--- {site['name']} (DB 조회) ---")

            # DB 조회만
            data = loader.fetch_from_db_only(road_address=site['address'])

            if data:
                logger.info(f"✅ DB 캐시에서 데이터 발견!")
                logger.info(f"  - building_count: {data.get('building_count', 'N/A')}")
            else:
                logger.info(f"⚠️ DB 캐시에 데이터 없음")

    except Exception as e:
        logger.error(f"테스트 실패: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="BC Loader 테스트")
    parser.add_argument("--api", action="store_true", help="API 호출 + DB 캐시 저장")
    parser.add_argument("--db", action="store_true", help="DB 조회만")
    parser.add_argument("--all", action="store_true", help="전체 테스트")

    args = parser.parse_args()

    if args.all or args.api:
        test_bc_loader()

    if args.all or args.db:
        test_bc_loader_db_only()

    if not (args.api or args.db or args.all):
        parser.print_help()
        print("\n예시:")
        print("  python -m ai_agent.agents.tcfd_report.test_bc_loader --api  # API 호출 + DB 저장")
        print("  python -m ai_agent.agents.tcfd_report.test_bc_loader --db   # DB 조회만")
        print("  python -m ai_agent.agents.tcfd_report.test_bc_loader --all  # 전체")
