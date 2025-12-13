-- financial-impacts 엔드포인트 테스트용 데이터 삽입
-- 테이블: site_risk_results
-- 엔드포인트: GET /api/analysis/financial-impacts?siteId={UUID}

-- 테스트용 site_id (실제 사용할 UUID로 변경하세요)
-- 예시: '12345678-1234-1234-1234-123456789012'

-- 9개 위험 유형에 대한 AAL 데이터 삽입
-- risk_type은 영문 표준명 사용 (Spring Boot 통일안)
-- aal_percentage: 0.0~100.0 범위 (백분율)

INSERT INTO site_risk_results (
    site_id,
    risk_type,
    hazard_score,
    exposure_score,
    vulnerability_score,
    physical_risk_score,
    physical_risk_score_100,
    aal_percentage,
    vulnerability_scale,
    insurance_rate,
    combined_score,
    risk_level,
    aal_level,
    calculated_at
) VALUES
-- 1. 극심한 고온 (extreme_heat)
(
    '12345678-1234-1234-1234-123456789012'::uuid,
    'extreme_heat',
    0.75,           -- hazard_score (H)
    0.80,           -- exposure_score (E)
    0.70,           -- vulnerability_score (V)
    0.42,           -- physical_risk_score (H×E×V = 0.75×0.80×0.70)
    42.0,           -- physical_risk_score_100 (0~100 스케일)
    2.5,            -- aal_percentage (2.5%)
    1.1,            -- vulnerability_scale (F_vuln: 0.7~1.3)
    0.0,            -- insurance_rate (보험 보전율)
    21.25,          -- combined_score ((42×0.5) + (2.5×10×0.5))
    'High',         -- risk_level
    'Moderate',     -- aal_level
    NOW()
),

-- 2. 극심한 한파 (extreme_cold)
(
    '12345678-1234-1234-1234-123456789012'::uuid,
    'extreme_cold',
    0.65,
    0.70,
    0.75,
    0.34,
    34.0,
    1.8,
    1.05,
    0.0,
    17.9,
    'Medium',
    'Low',
    NOW()
),

-- 3. 산불 (wildfire)
(
    '12345678-1234-1234-1234-123456789012'::uuid,
    'wildfire',
    0.55,
    0.60,
    0.65,
    0.21,
    21.0,
    1.2,
    0.95,
    0.0,
    10.5,
    'Medium',
    'Low',
    NOW()
),

-- 4. 가뭄 (drought)
(
    '12345678-1234-1234-1234-123456789012'::uuid,
    'drought',
    0.70,
    0.75,
    0.68,
    0.36,
    36.0,
    2.0,
    1.0,
    0.0,
    18.0,
    'Medium',
    'Moderate',
    NOW()
),

-- 5. 물부족 (water_stress)
(
    '12345678-1234-1234-1234-123456789012'::uuid,
    'water_stress',
    0.60,
    0.65,
    0.70,
    0.27,
    27.0,
    1.5,
    1.05,
    0.0,
    13.5,
    'Medium',
    'Low',
    NOW()
),

-- 6. 해수면 상승 (sea_level_rise)
(
    '12345678-1234-1234-1234-123456789012'::uuid,
    'sea_level_rise',
    0.50,
    0.55,
    0.60,
    0.17,
    17.0,
    0.8,
    0.90,
    0.0,
    8.5,
    'Low',
    'Minimal',
    NOW()
),

-- 7. 하천 홍수 (river_flood)
(
    '12345678-1234-1234-1234-123456789012'::uuid,
    'river_flood',
    0.80,
    0.85,
    0.78,
    0.53,
    53.0,
    3.5,
    1.15,
    0.0,
    26.5,
    'High',
    'High',
    NOW()
),

-- 8. 도시 홍수 (urban_flood)
(
    '12345678-1234-1234-1234-123456789012'::uuid,
    'urban_flood',
    0.78,
    0.82,
    0.75,
    0.48,
    48.0,
    3.0,
    1.12,
    0.0,
    24.0,
    'High',
    'Moderate',
    NOW()
),

-- 9. 태풍 (typhoon)
(
    '12345678-1234-1234-1234-123456789012'::uuid,
    'typhoon',
    0.85,
    0.90,
    0.80,
    0.61,
    61.0,
    4.2,
    1.20,
    0.0,
    30.5,
    'Very High',
    'High',
    NOW()
);

-- 데이터 확인 쿼리
SELECT
    site_id,
    risk_type,
    physical_risk_score_100,
    aal_percentage,
    risk_level,
    aal_level
FROM site_risk_results
WHERE site_id = '12345678-1234-1234-1234-123456789012'::uuid
ORDER BY risk_type;

-- 참고: API 응답 예시
-- GET /api/analysis/financial-impacts?siteId=12345678-1234-1234-1234-123456789012
--
-- 각 risk_type의 aal_percentage 값을 기준으로 4개 SSP 시나리오 생성:
-- - SSP1-2.6: base_aal × 0.8  (낙관적)
-- - SSP2-4.5: base_aal × 1.0  (중간)
-- - SSP3-7.0: base_aal × 1.3  (비관적)
-- - SSP5-8.5: base_aal × 1.5  (최악)
--
-- 총 36개 시나리오 (9개 risk_type × 4개 SSP scenario)
