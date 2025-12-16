"""
Node 0: Data Preprocessing 테스트 스크립트
목데이터 삽입 + State 로딩 테스트

작성일: 2025-12-15
버전: v01

사용법:
    python -m ai_agent.agents.tcfd_report.test_node_0
"""

import os
import sys
import asyncio
import logging
import uuid
from pathlib import Path
from typing import List, Dict, Any
from decimal import Decimal

import psycopg2
from psycopg2.extras import RealDictCursor, Json
from dotenv import load_dotenv

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# .env 로드
load_dotenv(project_root / ".env")

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_node_0")


# ============================================================
# DB 연결 설정 (skala-test 컨테이너: port 5555)
# ============================================================

def get_app_db_connection():
    """Application DB 연결"""
    return psycopg2.connect(
        host="localhost",
        port="5555",
        dbname="application",
        user="skala",
        password="skala1234"
    )


def get_dw_db_connection():
    """Datawarehouse DB 연결"""
    return psycopg2.connect(
        host="localhost",
        port="5555",
        dbname="datawarehouse",
        user="skala",
        password="skala1234"
    )


# ============================================================
# 테이블 생성 (테스트용)
# ============================================================

def create_test_tables():
    """테스트용 테이블 생성"""
    logger.info("=== 테스트용 테이블 생성 ===")

    # sites 테이블은 application DB에 이미 존재함 - 스킵
    logger.info("  sites 테이블: application DB에 이미 존재 (스킵)")

    # Datawarehouse DB 테이블들
    conn = get_dw_db_connection()
    cursor = conn.cursor()

    # 2. hazard_results
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hazard_results (
            latitude DECIMAL(9,6) NOT NULL,
            longitude DECIMAL(9,6) NOT NULL,
            risk_type VARCHAR(50) NOT NULL,
            target_year VARCHAR(10) NOT NULL,
            ssp126_score_100 REAL,
            ssp245_score_100 REAL,
            ssp370_score_100 REAL,
            ssp585_score_100 REAL,
            PRIMARY KEY (latitude, longitude, risk_type, target_year)
        )
    """)
    logger.info("  hazard_results 테이블 생성 완료")

    # 3. probability_results
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS probability_results (
            latitude DECIMAL(9,6) NOT NULL,
            longitude DECIMAL(9,6) NOT NULL,
            risk_type VARCHAR(50) NOT NULL,
            target_year VARCHAR(10) NOT NULL,
            ssp126_aal REAL,
            ssp245_aal REAL,
            ssp370_aal REAL,
            ssp585_aal REAL,
            damage_rates JSONB,
            ssp126_bin_probs JSONB,
            ssp245_bin_probs JSONB,
            ssp370_bin_probs JSONB,
            ssp585_bin_probs JSONB,
            PRIMARY KEY (latitude, longitude, risk_type, target_year)
        )
    """)
    logger.info("  probability_results 테이블 생성 완료")

    # 4. exposure_results (site_id 포함)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exposure_results (
            site_id UUID NOT NULL,
            latitude DECIMAL(9,6) NOT NULL,
            longitude DECIMAL(9,6) NOT NULL,
            risk_type VARCHAR(50) NOT NULL,
            target_year VARCHAR(10) NOT NULL,
            exposure_score REAL NOT NULL,
            PRIMARY KEY (site_id, risk_type, target_year)
        )
    """)
    logger.info("  exposure_results 테이블 생성 완료")

    # 5. vulnerability_results (site_id 포함)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vulnerability_results (
            site_id UUID NOT NULL,
            latitude DECIMAL(9,6) NOT NULL,
            longitude DECIMAL(9,6) NOT NULL,
            risk_type VARCHAR(50) NOT NULL,
            target_year VARCHAR(10) NOT NULL,
            vulnerability_score REAL NOT NULL,
            PRIMARY KEY (site_id, risk_type, target_year)
        )
    """)
    logger.info("  vulnerability_results 테이블 생성 완료")

    # 6. aal_scaled_results (site_id 포함)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS aal_scaled_results (
            site_id UUID NOT NULL,
            latitude DECIMAL(9,6) NOT NULL,
            longitude DECIMAL(9,6) NOT NULL,
            risk_type VARCHAR(50) NOT NULL,
            target_year VARCHAR(10) NOT NULL,
            ssp126_final_aal REAL,
            ssp245_final_aal REAL,
            ssp370_final_aal REAL,
            ssp585_final_aal REAL,
            PRIMARY KEY (site_id, risk_type, target_year)
        )
    """)
    logger.info("  aal_scaled_results 테이블 생성 완료")

    conn.commit()
    cursor.close()
    conn.close()

    logger.info("테스트용 테이블 생성 완료!")
    return True


# ============================================================
# 목데이터 정의
# ============================================================

# 테스트용 사업장 2개
MOCK_SITES = [
    {
        "id": str(uuid.uuid4()),  # UUID
        "user_id": str(uuid.uuid4()),
        "name": "테스트 서울본사",
        "road_address": "서울특별시 강남구 테헤란로 123",
        "jibun_address": "서울특별시 강남구 역삼동 123-45",
        "latitude": Decimal("37.501200"),
        "longitude": Decimal("127.039600"),
        "type": "office"
    },
    {
        "id": str(uuid.uuid4()),  # UUID
        "user_id": str(uuid.uuid4()),
        "name": "테스트 부산공장",
        "road_address": "부산광역시 강서구 녹산산업중로 456",
        "jibun_address": "부산광역시 강서구 송정동 456-78",
        "latitude": Decimal("35.089400"),
        "longitude": Decimal("128.853900"),
        "type": "factory"
    }
]

# 테스트용 리스크 타입들
RISK_TYPES = [
    "TYPHOON", "INLAND_FLOOD", "COASTAL_FLOOD", "HEAT_WAVE",
    "COLD_WAVE", "HEAVY_SNOW", "DROUGHT", "SEA_LEVEL_RISE", "WILDFIRE"
]

# 테스트용 target_years
TARGET_YEARS = ["2025", "2030", "2030s", "2050s"]


def generate_mock_hazard_results(site: Dict) -> List[Dict]:
    """Hazard 결과 목데이터 생성 (lat/lon 기반)"""
    results = []
    for risk_type in RISK_TYPES:
        for target_year in TARGET_YEARS:
            results.append({
                "latitude": site["latitude"],
                "longitude": site["longitude"],
                "risk_type": risk_type,
                "target_year": target_year,
                "ssp126_score_100": 30.0 + (hash(f"{risk_type}{target_year}") % 20),
                "ssp245_score_100": 35.0 + (hash(f"{risk_type}{target_year}") % 25),
                "ssp370_score_100": 40.0 + (hash(f"{risk_type}{target_year}") % 30),
                "ssp585_score_100": 45.0 + (hash(f"{risk_type}{target_year}") % 35)
            })
    return results


def generate_mock_probability_results(site: Dict) -> List[Dict]:
    """Probability 결과 목데이터 생성 (lat/lon 기반)"""
    results = []
    for risk_type in RISK_TYPES:
        for target_year in TARGET_YEARS:
            results.append({
                "latitude": site["latitude"],
                "longitude": site["longitude"],
                "risk_type": risk_type,
                "target_year": target_year,
                "ssp126_aal": 0.01 + (hash(f"{risk_type}{target_year}1") % 10) / 1000,
                "ssp245_aal": 0.015 + (hash(f"{risk_type}{target_year}2") % 10) / 1000,
                "ssp370_aal": 0.02 + (hash(f"{risk_type}{target_year}3") % 10) / 1000,
                "ssp585_aal": 0.025 + (hash(f"{risk_type}{target_year}5") % 10) / 1000,
                "damage_rates": [0, 0.02, 0.07, 0.15, 0.30],
                "ssp126_bin_probs": [0.65, 0.20, 0.10, 0.04, 0.01],
                "ssp245_bin_probs": [0.60, 0.22, 0.12, 0.05, 0.01],
                "ssp370_bin_probs": [0.55, 0.24, 0.14, 0.05, 0.02],
                "ssp585_bin_probs": [0.50, 0.26, 0.16, 0.06, 0.02]
            })
    return results


def generate_mock_exposure_results(site: Dict) -> List[Dict]:
    """Exposure 결과 목데이터 생성 (site_id 기반)"""
    results = []
    for risk_type in RISK_TYPES:
        for target_year in TARGET_YEARS:
            results.append({
                "site_id": site["id"],
                "latitude": site["latitude"],
                "longitude": site["longitude"],
                "risk_type": risk_type,
                "target_year": target_year,
                "exposure_score": 50.0 + (hash(f"{site['id']}{risk_type}{target_year}") % 40)
            })
    return results


def generate_mock_vulnerability_results(site: Dict) -> List[Dict]:
    """Vulnerability 결과 목데이터 생성 (site_id 기반)"""
    results = []
    for risk_type in RISK_TYPES:
        for target_year in TARGET_YEARS:
            results.append({
                "site_id": site["id"],
                "latitude": site["latitude"],
                "longitude": site["longitude"],
                "risk_type": risk_type,
                "target_year": target_year,
                "vulnerability_score": 40.0 + (hash(f"{site['id']}{risk_type}{target_year}v") % 50)
            })
    return results


def generate_mock_aal_scaled_results(site: Dict) -> List[Dict]:
    """AAL Scaled 결과 목데이터 생성 (site_id 기반)"""
    results = []
    for risk_type in RISK_TYPES:
        for target_year in TARGET_YEARS:
            results.append({
                "site_id": site["id"],
                "latitude": site["latitude"],
                "longitude": site["longitude"],
                "risk_type": risk_type,
                "target_year": target_year,
                "ssp126_final_aal": 0.005 + (hash(f"{site['id']}{risk_type}{target_year}a1") % 10) / 1000,
                "ssp245_final_aal": 0.008 + (hash(f"{site['id']}{risk_type}{target_year}a2") % 10) / 1000,
                "ssp370_final_aal": 0.012 + (hash(f"{site['id']}{risk_type}{target_year}a3") % 10) / 1000,
                "ssp585_final_aal": 0.018 + (hash(f"{site['id']}{risk_type}{target_year}a5") % 10) / 1000
            })
    return results


# ============================================================
# 목데이터 삽입 함수
# ============================================================

def insert_mock_sites():
    """Application DB에 목데이터 사이트 삽입"""
    logger.info("=== Application DB: sites 테이블 목데이터 삽입 ===")

    try:
        conn = get_app_db_connection()
        cursor = conn.cursor()

        for site in MOCK_SITES:
            # 0. 더미 users 먼저 삽입 (FK 제약조건 해결)
            cursor.execute("""
                INSERT INTO users (id, email, name, password)
                VALUES (%s, %s, %s, 'dummy_password')
                ON CONFLICT (id) DO NOTHING
            """, (site["user_id"], f"test_{site['name'].replace(' ', '')}@test.com", "TestUser"))

            # 기존 데이터 삭제 (테스트용)
            cursor.execute(
                "DELETE FROM sites WHERE name = %s",
                (site["name"],)
            )

            # 삽입
            cursor.execute("""
                INSERT INTO sites (id, user_id, name, road_address, jibun_address, latitude, longitude, type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                site["id"], site["user_id"], site["name"],
                site["road_address"], site["jibun_address"],
                site["latitude"], site["longitude"], site["type"]
            ))

            result = cursor.fetchone()
            logger.info(f"  삽입 완료: {site['name']} (id={result[0]})")

        conn.commit()
        cursor.close()
        conn.close()

        logger.info(f"Application DB 삽입 완료: {len(MOCK_SITES)}개 사이트")
        return True

    except Exception as e:
        logger.error(f"Application DB 삽입 실패: {e}")
        return False


def insert_mock_modelops_results():
    """Datawarehouse DB에 5개 result 테이블 목데이터 삽입"""
    logger.info("=== Datawarehouse DB: ModelOps 결과 테이블 목데이터 삽입 ===")

    try:
        conn = get_dw_db_connection()
        cursor = conn.cursor()

        for site in MOCK_SITES:
            logger.info(f"  사이트: {site['name']}")

            # 1. hazard_results
            hazard_data = generate_mock_hazard_results(site)
            for row in hazard_data:
                cursor.execute("""
                    INSERT INTO hazard_results
                    (latitude, longitude, risk_type, target_year,
                     ssp126_score_100, ssp245_score_100, ssp370_score_100, ssp585_score_100)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (latitude, longitude, risk_type, target_year)
                    DO UPDATE SET
                        ssp126_score_100 = EXCLUDED.ssp126_score_100,
                        ssp245_score_100 = EXCLUDED.ssp245_score_100,
                        ssp370_score_100 = EXCLUDED.ssp370_score_100,
                        ssp585_score_100 = EXCLUDED.ssp585_score_100
                """, (
                    row["latitude"], row["longitude"], row["risk_type"], row["target_year"],
                    row["ssp126_score_100"], row["ssp245_score_100"],
                    row["ssp370_score_100"], row["ssp585_score_100"]
                ))
            logger.info(f"    hazard_results: {len(hazard_data)}개")

            # 2. probability_results (damage_rates 컬럼 없음)
            prob_data = generate_mock_probability_results(site)
            for row in prob_data:
                cursor.execute("""
                    INSERT INTO probability_results
                    (latitude, longitude, risk_type, target_year,
                     ssp126_aal, ssp245_aal, ssp370_aal, ssp585_aal,
                     ssp126_bin_probs, ssp245_bin_probs, ssp370_bin_probs, ssp585_bin_probs)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (latitude, longitude, risk_type, target_year)
                    DO UPDATE SET
                        ssp126_aal = EXCLUDED.ssp126_aal,
                        ssp245_aal = EXCLUDED.ssp245_aal,
                        ssp370_aal = EXCLUDED.ssp370_aal,
                        ssp585_aal = EXCLUDED.ssp585_aal
                """, (
                    row["latitude"], row["longitude"], row["risk_type"], row["target_year"],
                    row["ssp126_aal"], row["ssp245_aal"],
                    row["ssp370_aal"], row["ssp585_aal"],
                    Json(row["ssp126_bin_probs"]),
                    Json(row["ssp245_bin_probs"]), Json(row["ssp370_bin_probs"]), Json(row["ssp585_bin_probs"])
                ))
            logger.info(f"    probability_results: {len(prob_data)}개")

            # 3. exposure_results (site_id 포함)
            exp_data = generate_mock_exposure_results(site)
            for row in exp_data:
                cursor.execute("""
                    INSERT INTO exposure_results
                    (site_id, latitude, longitude, risk_type, target_year, exposure_score)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (site_id, risk_type, target_year)
                    DO UPDATE SET exposure_score = EXCLUDED.exposure_score
                """, (
                    row["site_id"], row["latitude"], row["longitude"],
                    row["risk_type"], row["target_year"], row["exposure_score"]
                ))
            logger.info(f"    exposure_results: {len(exp_data)}개")

            # 4. vulnerability_results (site_id 포함)
            vuln_data = generate_mock_vulnerability_results(site)
            for row in vuln_data:
                cursor.execute("""
                    INSERT INTO vulnerability_results
                    (site_id, latitude, longitude, risk_type, target_year, vulnerability_score)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (site_id, risk_type, target_year)
                    DO UPDATE SET vulnerability_score = EXCLUDED.vulnerability_score
                """, (
                    row["site_id"], row["latitude"], row["longitude"],
                    row["risk_type"], row["target_year"], row["vulnerability_score"]
                ))
            logger.info(f"    vulnerability_results: {len(vuln_data)}개")

            # 5. aal_scaled_results (site_id 포함)
            aal_data = generate_mock_aal_scaled_results(site)
            for row in aal_data:
                cursor.execute("""
                    INSERT INTO aal_scaled_results
                    (site_id, latitude, longitude, risk_type, target_year,
                     ssp126_final_aal, ssp245_final_aal, ssp370_final_aal, ssp585_final_aal)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (site_id, risk_type, target_year)
                    DO UPDATE SET
                        ssp126_final_aal = EXCLUDED.ssp126_final_aal,
                        ssp245_final_aal = EXCLUDED.ssp245_final_aal,
                        ssp370_final_aal = EXCLUDED.ssp370_final_aal,
                        ssp585_final_aal = EXCLUDED.ssp585_final_aal
                """, (
                    row["site_id"], row["latitude"], row["longitude"],
                    row["risk_type"], row["target_year"],
                    row["ssp126_final_aal"], row["ssp245_final_aal"],
                    row["ssp370_final_aal"], row["ssp585_final_aal"]
                ))
            logger.info(f"    aal_scaled_results: {len(aal_data)}개")

        conn.commit()
        cursor.close()
        conn.close()

        logger.info("Datawarehouse DB 삽입 완료")
        return True

    except Exception as e:
        logger.error(f"Datawarehouse DB 삽입 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_inserted_site_ids() -> List[str]:
    """삽입된 사이트 ID 조회"""
    try:
        conn = get_app_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT id, name FROM sites
            WHERE name IN ('테스트 서울본사', '테스트 부산공장')
            ORDER BY name
        """)

        results = cursor.fetchall()
        cursor.close()
        conn.close()

        return [str(row['id']) for row in results]

    except Exception as e:
        logger.error(f"사이트 ID 조회 실패: {e}")
        return []


# ============================================================
# Node 0 테스트 실행
# ============================================================

async def test_node_0_execution():
    """Node 0 실행 테스트"""
    logger.info("\n=== Node 0 실행 테스트 ===")

    from .node_0_data_preprocessing import DataPreprocessingNode
    from langchain_openai import ChatOpenAI

    # 실제 테스트 사이트 ID 사용 (판교캠퍼스, SKU타워)
    site_ids = [
        "22222222-2222-2222-2222-222222222222",  # SK 판교캠퍼스
        "44444444-4444-4444-4444-444444444444",  # SK u-타워
    ]

    logger.info(f"테스트 대상 사이트: {site_ids}")

    # DB URL 설정 (skala-test 컨테이너: port 5555)
    app_db_url = "postgresql://skala:skala1234@localhost:5555/application"
    dw_db_url = "postgresql://skala:skala1234@localhost:5555/datawarehouse"

    logger.info(f"Application DB: {app_db_url.split('@')[1]}")
    logger.info(f"Datawarehouse DB: {dw_db_url.split('@')[1]}")

    try:
        # LLM 클라이언트 생성 (BC/AD Agent에서 사용)
        llm_client = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
        logger.info("LLM 클라이언트 생성: gpt-4o-mini")

        # Node 0 초기화 (LLM 포함)
        node = DataPreprocessingNode(
            app_db_url=app_db_url,
            dw_db_url=dw_db_url,
            llm_client=llm_client,  # LLM 전달!
            max_concurrent_sites=5,
            bc_chunk_size=5
        )

        # 실행 (site_ids는 UUID 문자열 리스트)
        state = await node.execute(
            site_ids=site_ids,  # UUID 문자열 리스트 사용
            excel_file=None,
            target_years=["2025", "2030", "2030s", "2050s"]
        )

        return state

    except Exception as e:
        logger.error(f"Node 0 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


def print_state_summary(state):
    """State 요약 출력"""
    if not state:
        logger.error("State가 None입니다")
        return

    logger.info("\n" + "=" * 60)
    logger.info("TCFDReportState 요약")
    logger.info("=" * 60)

    # 1. site_data
    logger.info(f"\n1. site_data: {len(state.get('site_data', []))}개 사이트")
    for site in state.get('site_data', []):
        info = site.get('site_info', {})
        logger.info(f"   - site_id: {site.get('site_id')}")
        logger.info(f"     name: {info.get('name')}")
        logger.info(f"     lat/lon: {info.get('latitude')}, {info.get('longitude')}")

    # 2. 5개 결과 테이블
    logger.info(f"\n2. hazard_results: {len(state.get('hazard_results', []))}개 레코드")
    if state.get('hazard_results'):
        sample = state['hazard_results'][0]
        logger.info(f"   샘플: {sample}")

    logger.info(f"\n3. probability_results: {len(state.get('probability_results', []))}개 레코드")
    if state.get('probability_results'):
        sample = state['probability_results'][0]
        logger.info(f"   샘플: risk_type={sample.get('risk_type')}, target_year={sample.get('target_year')}")

    logger.info(f"\n4. exposure_results: {len(state.get('exposure_results', []))}개 레코드")
    if state.get('exposure_results'):
        sample = state['exposure_results'][0]
        logger.info(f"   샘플: site_id={sample.get('site_id')}, exposure_score={sample.get('exposure_score')}")

    logger.info(f"\n5. vulnerability_results: {len(state.get('vulnerability_results', []))}개 레코드")
    if state.get('vulnerability_results'):
        sample = state['vulnerability_results'][0]
        logger.info(f"   샘플: site_id={sample.get('site_id')}, vulnerability_score={sample.get('vulnerability_score')}")

    logger.info(f"\n6. aal_scaled_results: {len(state.get('aal_scaled_results', []))}개 레코드")
    if state.get('aal_scaled_results'):
        sample = state['aal_scaled_results'][0]
        logger.info(f"   샘플: site_id={sample.get('site_id')}, ssp245_final_aal={sample.get('ssp245_final_aal')}")

    # 3. Agent 결과
    logger.info(f"\n7. building_data: {len(state.get('building_data', {}))}개 사이트")
    logger.info(f"\n8. additional_data: {bool(state.get('additional_data'))}")
    logger.info(f"\n9. use_additional_data: {state.get('use_additional_data', False)}")

    logger.info("\n" + "=" * 60)


# ============================================================
# Main
# ============================================================

def main():
    """메인 실행"""
    import argparse

    parser = argparse.ArgumentParser(description="Node 0 테스트")
    parser.add_argument("--insert", action="store_true", help="목데이터 삽입")
    parser.add_argument("--test", action="store_true", help="Node 0 실행 테스트")
    parser.add_argument("--all", action="store_true", help="전체 실행 (삽입 + 테스트)")

    args = parser.parse_args()

    if args.all or args.insert:
        logger.info("\n" + "=" * 60)
        logger.info("Step 1: 테이블 생성 및 목데이터 삽입")
        logger.info("=" * 60)

        # 테이블 생성
        if not create_test_tables():
            logger.error("테이블 생성 실패")
            return

        # Application DB 삽입
        if not insert_mock_sites():
            logger.error("Application DB 삽입 실패")
            return

        # Datawarehouse DB 삽입
        if not insert_mock_modelops_results():
            logger.error("Datawarehouse DB 삽입 실패")
            return

        logger.info("\n목데이터 삽입 완료!")

    if args.all or args.test:
        logger.info("\n" + "=" * 60)
        logger.info("Step 2: Node 0 실행 테스트")
        logger.info("=" * 60)

        state = asyncio.run(test_node_0_execution())
        print_state_summary(state)

    if not (args.insert or args.test or args.all):
        parser.print_help()
        print("\n예시:")
        print("  python -m ai_agent.agents.tcfd_report.test_node_0 --insert  # 목데이터 삽입")
        print("  python -m ai_agent.agents.tcfd_report.test_node_0 --test    # 테스트 실행")
        print("  python -m ai_agent.agents.tcfd_report.test_node_0 --all     # 전체 실행")


if __name__ == "__main__":
    main()
