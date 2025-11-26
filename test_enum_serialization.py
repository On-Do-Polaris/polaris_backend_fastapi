#!/usr/bin/env python
"""Enum 직렬화 테스트"""
import sys
sys.path.insert(0, '.')

from src.schemas.common import HazardType
from src.schemas.analysis import PhysicalRiskBarItem
import json

# 1. Enum value vs name
print("=" * 60)
print("HazardType Enum 값 확인")
print("=" * 60)
print(f"Enum name: {HazardType.HIGH_TEMPERATURE.name}")
print(f"Enum value: {HazardType.HIGH_TEMPERATURE.value}")

# 2. Pydantic 직렬화 테스트
print("\n" + "=" * 60)
print("Pydantic JSON 직렬화 테스트")
print("=" * 60)

item = PhysicalRiskBarItem(
    riskType=HazardType.HIGH_TEMPERATURE,
    riskScore=75,
    financialLossRate=0.023
)

# by_alias=True로 camelCase 확인
json_data = item.model_dump(by_alias=True)
print("JSON (by_alias=True):")
print(json.dumps(json_data, indent=2, ensure_ascii=False))

# by_alias=False로 snake_case 확인
json_data_snake = item.model_dump(by_alias=False)
print("\nJSON (by_alias=False):")
print(json.dumps(json_data_snake, indent=2, ensure_ascii=False))
