"""
Loader 테스트 스크립트
1. BuildingCharacteristicsLoader: 사업장 주소 → API 호출 → DB 적재
2. AdditionalDataLoader: Excel 파일 → 파싱 → (추후 DB 적재)

사용법:
    python -m ai_agent.agents.primary_data.test_loaders

작성일: 2025-12-16
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

# 경로 설정
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(override=True)


# SK 사업장 정보 (03.1_load_buildings_example.py 참고)
SK_SITES = [
    {"name": "SK u-타워", "lat": 37.3825, "lon": 127.1220, "address": "경기도 성남시 분당구 정자일로 95"},
    {"name": "판교 캠퍼스", "lat": 37.405879, "lon": 127.099877, "address": "경기도 성남시 분당구 판교역로 235"},
    {"name": "서린 사옥", "lat": 37.570708, "lon": 126.983577, "address": "서울특별시 종로구 서린동 99"},
]

# 테스트용 Excel 파일 경로
EXCEL_FILES = [
    Path(__file__).parent / "refer_data" / "판교캠퍼스_에너지 사용량_요금(실납부월 기준_24년_25년)_251016.xlsx의 사본.xlsx",
    Path(__file__).parent / "refer_data" / "판교dc 전력 사용량_2301-2510_수정.xlsx의 사본.xlsx",
]


def test_building_loader():
    """BuildingCharacteristicsLoader 테스트"""
    print("\n" + "=" * 60)
    print("1. BuildingCharacteristicsLoader 테스트")
    print("=" * 60)

    try:
        from ai_agent.agents.primary_data.building_characteristics_loader import BuildingDataLoader
    except ImportError as e:
        print(f"❌ BuildingDataLoader import 실패: {e}")
        return False

    # DB URL 확인
    db_url = os.getenv('DATABASE_URL') or os.getenv('DATAWAREHOUSE_DATABASE_URL')
    if not db_url:
        print("⚠️ DATABASE_URL이 설정되지 않음 - DB 캐시 비활성화")

    loader = BuildingDataLoader(db_url=db_url)

    success_count = 0
    results = []

    for site in SK_SITES[:2]:  # 처음 2개만 테스트
        print(f"\n처리 중: {site['name']}")
        print(f"   좌표: ({site['lat']}, {site['lon']})")
        print(f"   주소: {site['address']}")

        try:
            data = loader.load_and_cache(
                lat=site['lat'],
                lon=site['lon'],
                address=site['address']
            )

            if data:
                meta = data.get('meta', {})
                physical_specs = data.get('physical_specs', {})

                print(f"   ✅ 성공!")
                print(f"      - 지번주소: {meta.get('jibun_address', 'N/A')}")
                print(f"      - 도로명주소: {meta.get('road_address', 'N/A')}")
                print(f"      - 구조: {physical_specs.get('structure', 'N/A')}")
                print(f"      - 경과년수: {physical_specs.get('age', {}).get('years', 'N/A')}년")
                print(f"      - 주소코드: {meta.get('sigungu_cd', '')}-{meta.get('bjdong_cd', '')}-{meta.get('bun', '')}-{meta.get('ji', '')}")

                success_count += 1
                results.append({
                    'name': site['name'],
                    'success': True,
                    'data': data
                })
            else:
                print(f"   ❌ 데이터 없음")
                results.append({'name': site['name'], 'success': False, 'data': None})

        except Exception as e:
            print(f"   ❌ 오류: {e}")
            results.append({'name': site['name'], 'success': False, 'error': str(e)})

    print(f"\n결과: {success_count}/{len(SK_SITES[:2])} 성공")
    return success_count > 0, results


def test_additional_loader():
    """AdditionalDataLoader 테스트"""
    print("\n" + "=" * 60)
    print("2. AdditionalDataLoader 테스트")
    print("=" * 60)

    try:
        from ai_agent.agents.primary_data.additional_data_loader import AdditionalDataLoader
    except ImportError as e:
        print(f"❌ AdditionalDataLoader import 실패: {e}")
        return False

    loader = AdditionalDataLoader()

    success_count = 0
    results = []

    for excel_file in EXCEL_FILES:
        if not excel_file.exists():
            print(f"\n⚠️ 파일 없음: {excel_file.name}")
            continue

        print(f"\n처리 중: {excel_file.name}")

        try:
            # 파일 정보 조회
            file_info = loader.get_file_info(str(excel_file))

            if 'error' not in file_info:
                print(f"   ✅ 파일 읽기 성공!")
                print(f"      - 행 수: {file_info['row_count']}")
                print(f"      - 열 수: {file_info['column_count']}")
                print(f"      - 컬럼: {file_info['columns'][:5]}...")
                print(f"      - site_id 컬럼: {'있음' if file_info['has_site_id'] else '없음'}")

                # 데이터 로드 테스트 (site_ids 없이)
                site_data = loader.load_excel_data(str(excel_file), site_ids=[1, 2])
                print(f"      - 로드된 사이트: {list(site_data.keys())}")

                success_count += 1
                results.append({
                    'file': excel_file.name,
                    'success': True,
                    'info': file_info
                })
            else:
                print(f"   ❌ 오류: {file_info['error']}")
                results.append({'file': excel_file.name, 'success': False, 'error': file_info['error']})

        except Exception as e:
            print(f"   ❌ 오류: {e}")
            results.append({'file': excel_file.name, 'success': False, 'error': str(e)})

    print(f"\n결과: {success_count}/{len(EXCEL_FILES)} 성공")
    return success_count > 0, results


def test_db_cache():
    """DB 캐시 조회 테스트"""
    print("\n" + "=" * 60)
    print("3. DB 캐시 조회 테스트")
    print("=" * 60)

    try:
        from ai_agent.utils.database import DatabaseManager
    except ImportError as e:
        print(f"❌ DatabaseManager import 실패: {e}")
        return False

    db_url = os.getenv('DATABASE_URL') or os.getenv('DATAWAREHOUSE_DATABASE_URL')
    if not db_url:
        print("⚠️ DATABASE_URL이 설정되지 않음")
        return False

    try:
        db = DatabaseManager(db_url)

        # building_aggregate_cache 테이블 확인
        query = """
            SELECT COUNT(*) as count,
                   MIN(cached_at) as oldest,
                   MAX(cached_at) as newest
            FROM building_aggregate_cache
        """
        results = db.execute_query(query)

        if results:
            print(f"   building_aggregate_cache 테이블:")
            print(f"      - 총 레코드: {results[0]['count']}개")
            print(f"      - 가장 오래된: {results[0]['oldest']}")
            print(f"      - 가장 최신: {results[0]['newest']}")

            # 최근 5개 조회
            recent_query = """
                SELECT sigungu_cd, bjdong_cd, bun, ji, road_address, building_count
                FROM building_aggregate_cache
                ORDER BY cached_at DESC
                LIMIT 5
            """
            recent = db.execute_query(recent_query)
            if recent:
                print(f"\n   최근 캐시된 데이터:")
                for r in recent:
                    print(f"      - {r['road_address'] or 'N/A'} ({r['building_count']}개 건물)")

            return True
        else:
            print("   ⚠️ 데이터 없음")
            return False

    except Exception as e:
        print(f"❌ DB 조회 오류: {e}")
        return False


def main():
    """전체 테스트 실행"""
    print("\n" + "=" * 80)
    print("🚀 Loader 테스트 시작")
    print("=" * 80)

    # 1. Building Loader 테스트
    bc_success, bc_results = test_building_loader()

    # 2. Additional Loader 테스트
    ad_success, ad_results = test_additional_loader()

    # 3. DB 캐시 조회 테스트
    db_success = test_db_cache()

    # 결과 요약
    print("\n" + "=" * 80)
    print("📊 테스트 결과 요약")
    print("=" * 80)
    print(f"   1. BuildingCharacteristicsLoader: {'✅ 성공' if bc_success else '❌ 실패'}")
    print(f"   2. AdditionalDataLoader: {'✅ 성공' if ad_success else '❌ 실패'}")
    print(f"   3. DB 캐시 조회: {'✅ 성공' if db_success else '❌ 실패'}")
    print("=" * 80)


if __name__ == "__main__":
    main()
