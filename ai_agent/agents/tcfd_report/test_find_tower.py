"""
법정동 전체 데이터에서 '타워' 건물 찾기
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

# u-타워 법정동 코드로 조회
floor_params = {
    "sigunguCd": "41135",
    "bjdongCd": "10300"
}

print("=== 법정동 10300 전체 층별개요 조회 ===")
floors_raw = fetcher._fetch_api("getBrFlrOulnInfo", floor_params, fetch_all_pages=True) or []
print(f"총 {len(floors_raw)}건 조회됨")

# 도로명 주소 수집
road_addresses = set()
tower_buildings = []

for f in floors_raw:
    addr = f.get('newPlatPlc', '')
    bldg_nm = f.get('bldNm', '')

    if addr:
        road_addresses.add(addr)

    # 타워 관련 검색
    if '타워' in addr or '타워' in bldg_nm or 'tower' in addr.lower() or 'tower' in bldg_nm.lower():
        tower_buildings.append({
            'addr': addr,
            'bldNm': bldg_nm,
            'flrNo': f.get('flrNo'),
            'flrNoNm': f.get('flrNoNm')
        })

print(f"\n=== 도로명 주소 목록 ({len(road_addresses)}개 고유 주소) ===")
for addr in sorted(road_addresses):
    print(f"  - {addr}")

print(f"\n=== '타워' 포함 건물 ({len(tower_buildings)}건) ===")
for t in tower_buildings[:20]:
    print(f"  - {t['addr']} / {t['bldNm']} / {t['flrNoNm']}")

# 성남대로 관련 주소 찾기
print("\n=== '성남대로' 포함 주소 ===")
for addr in sorted(road_addresses):
    if '성남대로' in addr:
        print(f"  - {addr}")

# 343번길 찾기
print("\n=== '343' 포함 주소 ===")
for addr in sorted(road_addresses):
    if '343' in addr:
        print(f"  - {addr}")
