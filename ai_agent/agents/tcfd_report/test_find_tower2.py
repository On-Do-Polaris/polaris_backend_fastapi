"""
성남대로 343번길 9 주소 검색 및 실제 법정동 확인
"""
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from ai_agent.utils.building_data_fetcher import BuildingDataFetcher

fetcher = BuildingDataFetcher()

# 1. 주소 검색 API로 정확한 정보 확인
print("=== 주소 검색 API 결과 ===")
addr_info = fetcher.search_address("경기도 성남시 분당구 성남대로 343번길 9 에스케이유타워")
if addr_info:
    for k, v in addr_info.items():
        print(f"  {k}: {v}")
else:
    print("  주소 검색 실패")

# 2. 실제 법정동 코드로 다시 조회
if addr_info:
    print(f"\n=== 법정동 {addr_info.get('bjdong_cd')} 전체 조회 ===")
    floor_params = {
        "sigunguCd": addr_info.get('sigungu_cd'),
        "bjdongCd": addr_info.get('bjdong_cd')
    }
    floors = fetcher._fetch_api("getBrFlrOulnInfo", floor_params, fetch_all_pages=True) or []
    print(f"총 {len(floors)}건")

    # 고유 주소 확인
    addresses = set(f.get('newPlatPlc', '') for f in floors)
    print(f"\n고유 주소 ({len(addresses)}개):")
    for addr in sorted(addresses):
        if '343' in addr or '타워' in addr:
            print(f"  ★ {addr}")
        elif '성남대로' in addr:
            print(f"  - {addr}")

# 3. 다른 법정동들도 확인 (분당구 주요 법정동)
print("\n=== 분당구 주요 법정동에서 '343번길' 또는 '타워' 검색 ===")
bjdong_codes = ['10100', '10200', '10300', '10400', '10500', '10600', '10700', '10800', '10900', '11000']

for bjdong in bjdong_codes:
    params = {"sigunguCd": "41135", "bjdongCd": bjdong}
    floors = fetcher._fetch_api("getBrFlrOulnInfo", params, fetch_all_pages=True) or []

    # 343번길 또는 타워 검색
    found = []
    for f in floors:
        addr = f.get('newPlatPlc', '')
        bldNm = f.get('bldNm', '')
        if '343' in addr or '타워' in bldNm or '타워' in addr:
            found.append(f"{addr} ({bldNm})")

    if found:
        print(f"\n법정동 {bjdong}: {len(floors)}건 중 {len(set(found))}개 매칭")
        for f in sorted(set(found))[:10]:
            print(f"  ★ {f}")
    else:
        print(f"법정동 {bjdong}: {len(floors)}건 - 매칭 없음")
