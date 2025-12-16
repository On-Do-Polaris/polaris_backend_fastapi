"""
전체 플로우 테스트 스크립트
primary_data 에이전트 → tcfd_report Node 0 테스트

실행: uv run python test_full_flow.py
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from decimal import Decimal

import psycopg2
from psycopg2.extras import RealDictCursor, Json
from dotenv import load_dotenv

# 프로젝트 루트
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

load_dotenv(project_root / ".env")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_full_flow")


# ============================================================
# DB 설정
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "port": "5555",
    "dbname": "postgres",
    "user": "skala",
    "password": "skala1234"
}


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


# ============================================================
# 목데이터 정의
# ============================================================

MOCK_SITES = [
    {
        "id": "11111111-1111-1111-1111-111111111111",
        "user_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "name": "테스트 서울본사",
        "road_address": "서울특별시 강남구 테헤란로 123",
        "jibun_address": "서울특별시 강남구 역삼동 123-45",
        "latitude": Decimal("37.501200"),
        "longitude": Decimal("127.039600"),
        "type": "office"
    },
    {
        "id": "22222222-2222-2222-2222-222222222222",
        "user_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "name": "테스트 부산공장",
        "road_address": "부산광역시 강서구 녹산산업중로 456",
        "jibun_address": "부산광역시 강서구 송정동 456-78",
        "latitude": Decimal("35.089400"),
        "longitude": Decimal("128.853900"),
        "type": "factory"
    }
]

RISK_TYPES = ["TYPHOON", "INLAND_FLOOD", "HEAT_WAVE", "DROUGHT"]
TARGET_YEARS = ["2030", "2050s"]


def insert_mock_data():
    """목데이터 삽입 (테이블 생성 X)"""
    logger.info("=== 목데이터 삽입 ===")

    conn = get_db_connection()
    cursor = conn.cursor()

    for site in MOCK_SITES:
        # 기존 데이터 삭제
        cursor.execute("DELETE FROM sites WHERE id = %s", (site["id"],))
        cursor.execute("DELETE FROM aal_scaled_results WHERE site_id = %s", (site["id"],))
        cursor.execute("DELETE FROM exposure_results WHERE site_id = %s", (site["id"],))
        cursor.execute("DELETE FROM vulnerability_results WHERE site_id = %s", (site["id"],))
        cursor.execute(
            "DELETE FROM hazard_results WHERE latitude = %s AND longitude = %s",
            (site["latitude"], site["longitude"])
        )
        cursor.execute(
            "DELETE FROM probability_results WHERE latitude = %s AND longitude = %s",
            (site["latitude"], site["longitude"])
        )

        # sites 삽입
        cursor.execute("""
            INSERT INTO sites (id, user_id, name, road_address, jibun_address, latitude, longitude, type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            site["id"], site["user_id"], site["name"],
            site["road_address"], site["jibun_address"],
            site["latitude"], site["longitude"], site["type"]
        ))
        logger.info(f"  sites 삽입: {site['name']}")

        # 5개 결과 테이블 삽입
        for risk_type in RISK_TYPES:
            for target_year in TARGET_YEARS:
                # hazard_results
                cursor.execute("""
                    INSERT INTO hazard_results
                    (latitude, longitude, risk_type, target_year,
                     ssp126_score_100, ssp245_score_100, ssp370_score_100, ssp585_score_100)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    site["latitude"], site["longitude"], risk_type, target_year,
                    30.0, 40.0, 50.0, 60.0
                ))

                # probability_results
                cursor.execute("""
                    INSERT INTO probability_results
                    (latitude, longitude, risk_type, target_year,
                     ssp126_aal, ssp245_aal, ssp370_aal, ssp585_aal,
                     damage_rates, ssp126_bin_probs, ssp245_bin_probs, ssp370_bin_probs, ssp585_bin_probs)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    site["latitude"], site["longitude"], risk_type, target_year,
                    0.01, 0.02, 0.03, 0.04,
                    Json([0, 0.02, 0.07, 0.15, 0.30]),
                    Json([0.65, 0.20, 0.10, 0.04, 0.01]),
                    Json([0.60, 0.22, 0.12, 0.05, 0.01]),
                    Json([0.55, 0.24, 0.14, 0.05, 0.02]),
                    Json([0.50, 0.26, 0.16, 0.06, 0.02])
                ))

                # exposure_results
                cursor.execute("""
                    INSERT INTO exposure_results
                    (site_id, latitude, longitude, risk_type, target_year, exposure_score)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    site["id"], site["latitude"], site["longitude"],
                    risk_type, target_year, 55.0
                ))

                # vulnerability_results
                cursor.execute("""
                    INSERT INTO vulnerability_results
                    (site_id, latitude, longitude, risk_type, target_year, vulnerability_score)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    site["id"], site["latitude"], site["longitude"],
                    risk_type, target_year, 45.0
                ))

                # aal_scaled_results
                cursor.execute("""
                    INSERT INTO aal_scaled_results
                    (site_id, latitude, longitude, risk_type, target_year,
                     ssp126_final_aal, ssp245_final_aal, ssp370_final_aal, ssp585_final_aal)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    site["id"], site["latitude"], site["longitude"],
                    risk_type, target_year,
                    0.005, 0.008, 0.012, 0.018
                ))

    conn.commit()
    cursor.close()
    conn.close()

    logger.info("목데이터 삽입 완료!")
    return [site["id"] for site in MOCK_SITES]


# ============================================================
# 테스트 함수들
# ============================================================

async def test_primary_data_agents():
    """Step 1: Primary Data 에이전트 테스트"""
    logger.info("\n" + "=" * 60)
    logger.info("Step 1: Primary Data 에이전트 테스트")
    logger.info("=" * 60)

    # 직접 import (tcfd_report __init__.py 우회)
    from ai_agent.agents.primary_data.building_characteristics_agent import BuildingCharacteristicsAgent

    bc_agent = BuildingCharacteristicsAgent(llm_client=None)

    test_site = {
        "site_id": 1,
        "site_info": {
            "latitude": 37.501200,
            "longitude": 127.039600,
            "address": "서울특별시 강남구 테헤란로 123"
        },
        "risk_results": [
            {"risk_type": "TYPHOON", "final_aal": 0.008, "physical_risk_score": 40.0},
        ]
    }

    logger.info("BuildingCharacteristicsAgent 배치 분석 시작...")
    bc_results = await bc_agent.analyze_batch([test_site])

    for site_id, result in bc_results.items():
        logger.info(f"  사업장 {site_id}:")
        logger.info(f"    - 구조 등급: {result.get('structural_grade', 'Unknown')}")
        logger.info(f"    - 취약점 수: {len(result.get('vulnerabilities', []))}")
        logger.info(f"    - 회복력 요인 수: {len(result.get('resilience', []))}")

    logger.info("✅ Primary Data 에이전트 테스트 완료!")
    return bc_results


async def test_node_0(site_ids):
    """Step 2: Node 0 (Data Preprocessing) 테스트"""
    logger.info("\n" + "=" * 60)
    logger.info("Step 2: Node 0 (Data Preprocessing) 테스트")
    logger.info("=" * 60)

    # 직접 import
    from ai_agent.agents.tcfd_report.node_0_data_preprocessing import DataPreprocessingNode
    from langchain_openai import ChatOpenAI

    # LLM 클라이언트 초기화
    openai_api_key = os.getenv("OPENAI_API_KEY")
    llm_client = None
    if openai_api_key:
        try:
            llm_client = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.3,
                api_key=openai_api_key
            )
            logger.info("✅ LLM 클라이언트 초기화 성공 (gpt-4o-mini)")
        except Exception as e:
            logger.warning(f"⚠️ LLM 클라이언트 초기화 실패: {e}")
    else:
        logger.warning("⚠️ OPENAI_API_KEY 없음 - LLM 분석 건너뜀")

    # application DB: sites 테이블이 있는 postgres DB
    # datawarehouse DB: building_aggregate_cache 등 결과 테이블이 있는 datawarehouse DB
    app_db_url = "postgresql://skala:skala1234@localhost:5555/postgres"
    dw_db_url = "postgresql://skala:skala1234@localhost:5555/datawarehouse"

    node = DataPreprocessingNode(
        app_db_url=app_db_url,
        dw_db_url=dw_db_url,
        llm_client=llm_client,
        max_concurrent_sites=5,
        bc_chunk_size=5
    )

    logger.info(f"Node 0 실행 시작... (site_ids: {site_ids})")

    try:
        state = await node.execute(
            site_ids=site_ids,
            excel_file=None,
            target_years=["2030", "2050s"]
        )

        logger.info("\n=== Node 0 결과 요약 ===")
        logger.info(f"site_data: {len(state.get('site_data', []))}개 사업장")
        logger.info(f"hazard_results: {len(state.get('hazard_results', []))}개 레코드")
        logger.info(f"exposure_results: {len(state.get('exposure_results', []))}개 레코드")
        logger.info(f"vulnerability_results: {len(state.get('vulnerability_results', []))}개 레코드")
        logger.info(f"aal_scaled_results: {len(state.get('aal_scaled_results', []))}개 레코드")
        logger.info(f"probability_results: {len(state.get('probability_results', []))}개 레코드")
        logger.info(f"building_data: {len(state.get('building_data', {}))}개 사업장")
        logger.info(f"use_additional_data: {state.get('use_additional_data', False)}")

        # building_data 상세 내용 출력 (primary_data 에이전트 결과 확인)
        logger.info("\n=== Primary Data 에이전트 결과 상세 ===")
        building_data = state.get('building_data', {})
        for site_id, bd in building_data.items():
            logger.info(f"\n📍 사업장: {site_id}")
            logger.info(f"  - 구조 등급: {bd.get('structural_grade', 'N/A')}")
            logger.info(f"  - 취약점 수: {len(bd.get('vulnerabilities', []))}")
            for v in bd.get('vulnerabilities', [])[:3]:  # 최대 3개만
                logger.info(f"    • {v.get('factor', 'N/A')}: {v.get('severity', 'N/A')}")
            logger.info(f"  - 회복력 요인 수: {len(bd.get('resilience', []))}")
            for r in bd.get('resilience', [])[:3]:
                logger.info(f"    • {r.get('factor', 'N/A')}: {r.get('strength', 'N/A')}")
            # agent_guidelines 확인 (LLM 분석 결과)
            guidelines = bd.get('agent_guidelines', {})
            if guidelines:
                if isinstance(guidelines, str):
                    logger.info(f"  - LLM 가이드라인: {len(guidelines)}자 텍스트")
                    logger.info(f"    • {guidelines[:200]}...")
                elif isinstance(guidelines, dict):
                    logger.info(f"  - LLM 가이드라인: {len(guidelines)}개 항목")
                    for key in list(guidelines.keys())[:3]:
                        val = guidelines[key]
                        if isinstance(val, str) and len(val) > 100:
                            val = val[:100] + "..."
                        logger.info(f"    • {key}: {val}")
            else:
                logger.info(f"  - LLM 가이드라인: 없음 (LLM 클라이언트 미설정)")

        logger.info("✅ Node 0 테스트 완료!")
        return state

    except Exception as e:
        logger.error(f"❌ Node 0 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """메인 실행"""
    logger.info("\n" + "=" * 60)
    logger.info("전체 플로우 테스트 시작")
    logger.info("플로우: primary_data 에이전트 → tcfd_report Node 0")
    logger.info("=" * 60)

    # 1. 목데이터 삽입
    site_ids = insert_mock_data()

    # 2. Primary Data 에이전트 테스트
    await test_primary_data_agents()

    # 3. Node 0 테스트 (primary_data 에이전트 포함)
    state = await test_node_0(site_ids)

    logger.info("\n" + "=" * 60)
    if state and state.get('site_data'):
        logger.info("✅ 전체 플로우 테스트 성공!")
    else:
        logger.info("❌ 전체 플로우 테스트 실패!")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
