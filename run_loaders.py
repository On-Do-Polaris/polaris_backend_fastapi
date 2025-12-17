"""
Loader 실행 스크립트
1. AdditionalDataLoader - scratch 폴더 → DB
2. BuildingDataLoader - API → DB
"""
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

print("=" * 60)
print("1. AdditionalDataLoader 실행")
print("=" * 60)

from ai_agent.agents.primary_data.additional_data_loader import AdditionalDataLoader

ad_loader = AdditionalDataLoader()
result = ad_loader.load_from_scratch_folder("./scratch")
print(f"  총: {result['total_files']}, 성공: {result['success_count']}, 실패: {result['failed_count']}")

print("\n" + "=" * 60)
print("2. BuildingDataLoader 실행")
print("=" * 60)

from ai_agent.agents.primary_data.building_characteristics_loader import BuildingDataLoader

bc_loader = BuildingDataLoader()

sites = [
    {"site_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "lat": 37.405879, "lon": 127.099877, "address": "경기도 성남시 분당구 판교로 255번길 38"},
    {"site_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", "lat": 37.3825, "lon": 127.1220, "address": "경기도 성남시 분당구 성남대로 343번길 9"},
]

async def load_buildings():
    return await bc_loader.load_batch(sites)

bc_result = asyncio.run(load_buildings())
print(f"  로드 완료: {len(bc_result)}개 사업장")

print("\n" + "=" * 60)
print("✅ 로더 실행 완료!")
print("=" * 60)
