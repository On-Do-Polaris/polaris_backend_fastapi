
-- Step 1: 임시 테이블 생성
CREATE TEMP TABLE temp_hazard_results (
  latitude NUMERIC,
  longitude NUMERIC,
  risk_type VARCHAR(50),
  target_year VARCHAR(10),
  ssp126_score_100 NUMERIC,
  ssp245_score_100 NUMERIC,
  ssp370_score_100 NUMERIC,
  ssp585_score_100 NUMERIC
);

-- Step 2: CSV 데이터를 임시 테이블에 로드
\COPY temp_hazard_results FROM 'hazard_results_full_data.csv' DELIMITER ',' CSV HEADER;

-- Step 3: 임시 테이블에서 본 테이블로 UPSERT
INSERT INTO hazard_results (
  latitude,
  longitude,
  risk_type,
  target_year,
  ssp126_score_100,
  ssp245_score_100,
  ssp370_score_100,
  ssp585_score_100
)
SELECT 
  latitude,
  longitude,
  risk_type,
  target_year,
  ssp126_score_100,
  ssp245_score_100,
  ssp370_score_100,
  ssp585_score_100
FROM temp_hazard_results
ON CONFLICT (latitude, longitude, risk_type, target_year) 
DO UPDATE SET
  ssp126_score_100 = EXCLUDED.ssp126_score_100,
  ssp245_score_100 = EXCLUDED.ssp245_score_100,
  ssp370_score_100 = EXCLUDED.ssp370_score_100,
  ssp585_score_100 = EXCLUDED.ssp585_score_100;

-- Step 4: 임시 테이블 삭제 (자동 삭제되지만 명시적으로)
DROP TABLE temp_hazard_results;
