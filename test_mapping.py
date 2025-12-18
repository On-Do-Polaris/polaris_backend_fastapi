# -*- coding: utf-8 -*-
"""
기후 리스크 매핑 테스트
"""

# 영문 → 한글 매핑
RISK_TYPE_KR_MAPPING = {
    'extreme_heat': '폭염',
    'extreme_cold': '한파',
    'wildfire': '산불',
    'drought': '가뭄',
    'water_stress': '물부족',
    'sea_level_rise': '해안침수',
    'river_flood': '내륙침수',
    'urban_flood': '도시침수',
    'typhoon': '태풍'
}

# 역매핑: 한글 → 영어 (프론트엔드 요청 처리용)
RISK_TYPE_EN_MAPPING = {v: k for k, v in RISK_TYPE_KR_MAPPING.items()}

# 추가 한글 별칭 매핑 (프론트엔드 호환성)
RISK_TYPE_ALIAS_MAPPING = {
    '극심한 고온': 'extreme_heat',
    '극심한 저온': 'extreme_cold',
    '극한 고온': 'extreme_heat',
    '극한 저온': 'extreme_cold',
    '고온': 'extreme_heat',
    '저온': 'extreme_cold',
    '하천 홍수': 'river_flood',
    '내륙 홍수': 'river_flood',
    '도시 홍수': 'urban_flood',
    '해수면 상승': 'sea_level_rise',
    '해안 침수': 'sea_level_rise',
    '물 부족': 'water_stress',
}

# RISK_TYPE_EN_MAPPING에 별칭 추가
RISK_TYPE_EN_MAPPING.update(RISK_TYPE_ALIAS_MAPPING)

# 테스트
print("=== 기후 리스크 매핑 테스트 ===\n")

test_cases = [
    '하천 홍수',
    '내륙침수',
    '도시침수',
    '도시 홍수',
    '해수면 상승',
    '해안침수',
    '물부족',
    '물 부족',
    '폭염',
    '극심한 고온',
    '산불',
    '가뭄',
    '한파',
    '태풍',
]

print("Success - Mapped risks:")
for hazard_type in test_cases:
    mapped = RISK_TYPE_EN_MAPPING.get(hazard_type)
    if mapped:
        print(f"  '{hazard_type}' -> '{mapped}'")
    else:
        print(f"  ERROR: '{hazard_type}' -> No mapping!")

print(f"\nTotal mappings: {len(RISK_TYPE_EN_MAPPING)}")
print("\nAll mappings:")
for kr, en in sorted(RISK_TYPE_EN_MAPPING.items()):
    print(f"  '{kr}' -> '{en}'")
