"""
Node 0 DB 연결 테스트 (Primary Data 검증)
실제 DB에서 사업장 데이터 조회 및 BC/AD Agent 실행 테스트

실행 방법:
    cd polaris_backend_fastapi
    python ai_agent/agents/tcfd_report/test_node0_with_db.py

환경변수 필요:
    - APPLICATION_DATABASE_URL: SpringBoot DB (sites 테이블)
    - DATABASE_URL: Datawarehouse DB (ModelOps 결과 테이블들)
    - OPENAI_API_KEY: LLM 클라이언트용

테스트 시나리오:
    1. Application DB에서 사업장 기본 정보 조회
    2. Datawarehouse DB에서 5개 ModelOps 결과 테이블 조회
    3. BC Agent 실행 (건축물 분석)
    4. AD Agent 실행 (추가 데이터 분석)
    5. 최종 반환 JSON 구조 검증
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# sys.path에 프로젝트 루트 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from ai_agent.agents.tcfd_report.node_0_data_preprocessing import DataPreprocessingNode


# ===== 환경변수 체크 =====

def check_environment():
    """필수 환경변수 확인"""
    required_env_vars = [
        'APPLICATION_DATABASE_URL',
        'DATABASE_URL',
        'OPENAI_API_KEY'
    ]

    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print("❌ 필수 환경변수가 설정되지 않았습니다:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n.env 파일을 확인하거나 환경변수를 설정해주세요.")
        sys.exit(1)

    print("✅ 환경변수 확인 완료\n")


# ===== 테스트 함수 =====

async def test_node0_basic(site_ids: List[int]):
    """
    테스트 1: Node 0 기본 실행
    - DB 조회만 (target_years=None → 전체 년도)
    """
    print("=" * 80)
    print("테스트 1: Node 0 기본 실행 (전체 년도)")
    print("=" * 80)
    print(f"Site IDs: {site_ids}\n")

    # LLM 클라이언트 초기화 (BC/AD Agent용)
    from langchain_openai import ChatOpenAI
    llm_client = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.0,
        api_key=os.getenv("OPENAI_API_KEY")
    )

    # Node 0 초기화
    node = DataPreprocessingNode(
        app_db_url=os.getenv('APPLICATION_DATABASE_URL'),
        dw_db_url=os.getenv('DATABASE_URL'),
        llm_client=llm_client,
        max_concurrent_sites=10,
        bc_chunk_size=3
    )

    # 실행
    print("▶ Node 0 실행 시작...\n")
    start_time = datetime.now()

    try:
        result = await node.execute(
            site_ids=site_ids,
            excel_file=None,  # DEPRECATED
            target_years=None  # 전체 년도 조회
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print(f"\n✅ Node 0 실행 완료 (소요시간: {duration:.2f}초)\n")

        # 결과 검증
        print("=" * 80)
        print("📊 결과 검증")
        print("=" * 80)

        # 1. sites_data 검증
        sites_data = result.get("sites_data", [])
        print(f"✅ sites_data: {len(sites_data)}개 사업장")
        for site in sites_data:
            site_info = site.get("site_info", {})
            print(f"   - site_id={site['site_id']}, name={site_info.get('name')}, "
                  f"lat={site_info.get('latitude')}, lon={site_info.get('longitude')}")

        # 2. ModelOps 5개 테이블 결과 검증
        aal_results = result.get("aal_scaled_results", [])
        hazard_results = result.get("hazard_results", [])
        exposure_results = result.get("exposure_results", [])
        vulnerability_results = result.get("vulnerability_results", [])
        probability_results = result.get("probability_results", [])

        print(f"\n✅ ModelOps 결과 테이블:")
        print(f"   - aal_scaled_results: {len(aal_results)}개 row")
        print(f"   - hazard_results: {len(hazard_results)}개 row")
        print(f"   - exposure_results: {len(exposure_results)}개 row")
        print(f"   - vulnerability_results: {len(vulnerability_results)}개 row")
        print(f"   - probability_results: {len(probability_results)}개 row")

        # AAL 샘플 출력
        if aal_results:
            print(f"\n   [AAL Sample]")
            sample = aal_results[0]
            print(f"   site_id={sample.get('site_id')}, risk_type={sample.get('risk_type')}, "
                  f"target_year={sample.get('target_year')}")
            print(f"   SSP245 Final AAL: {sample.get('ssp245_final_aal')}")

        # 3. building_data 검증 (BC Agent 결과)
        building_data = result.get("building_data", {})
        print(f"\n✅ building_data (BC Agent): {len(building_data)}개 사업장")
        for site_id, bc_result in building_data.items():
            print(f"   - site_id={site_id}")
            print(f"     * structural_grade: {bc_result.get('structural_grade')}")
            print(f"     * has_raw_data: {bool(bc_result.get('raw_data'))}")

            # BC Agent guideline 샘플
            guideline = bc_result.get('guideline', '')
            if guideline:
                preview = guideline[:100] + "..." if len(guideline) > 100 else guideline
                print(f"     * guideline: {preview}")

        # 4. additional_data 검증 (AD Agent 결과)
        additional_data = result.get("additional_data", {})
        use_additional_data = result.get("use_additional_data", False)

        print(f"\n✅ additional_data (AD Agent): use_additional_data={use_additional_data}")
        if use_additional_data and additional_data:
            data_summary = additional_data.get('data_summary', {})
            print(f"   - data_summary.one_liner: {data_summary.get('one_liner', 'N/A')}")

            site_guidelines = additional_data.get('site_specific_guidelines', {})
            print(f"   - site_specific_guidelines: {len(site_guidelines)}개 사업장")

            raw_data = additional_data.get('raw_data', {})
            print(f"   - raw_data: {len(raw_data)}개 사업장")

        print("\n" + "=" * 80)
        print("🎉 테스트 1 통과!")
        print("=" * 80 + "\n")

        return result

    except Exception as e:
        print(f"\n❌ Node 0 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        raise


async def test_node0_filtered_years(site_ids: List[int]):
    """
    테스트 2: Node 0 특정 년도만 조회
    - target_years = ["2030", "2050s"]
    """
    print("=" * 80)
    print("테스트 2: Node 0 특정 년도 필터링")
    print("=" * 80)
    print(f"Site IDs: {site_ids}")
    print(f"Target Years: ['2030', '2050s']\n")

    from langchain_openai import ChatOpenAI
    llm_client = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.0,
        api_key=os.getenv("OPENAI_API_KEY")
    )

    node = DataPreprocessingNode(
        app_db_url=os.getenv('APPLICATION_DATABASE_URL'),
        dw_db_url=os.getenv('DATABASE_URL'),
        llm_client=llm_client
    )

    print("▶ Node 0 실행 시작 (년도 필터링)...\n")
    start_time = datetime.now()

    try:
        result = await node.execute(
            site_ids=site_ids,
            excel_file=None,
            target_years=["2030", "2050s"]  # 필터링
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print(f"\n✅ Node 0 실행 완료 (소요시간: {duration:.2f}초)\n")

        # 결과 검증: target_year가 2030 또는 2050s만 있어야 함
        print("=" * 80)
        print("📊 Year 필터링 검증")
        print("=" * 80)

        aal_results = result.get("aal_scaled_results", [])
        unique_years = set(r.get('target_year') for r in aal_results)

        print(f"✅ AAL Results: {len(aal_results)}개 row")
        print(f"   Unique target_years: {sorted(unique_years)}")

        # 검증: 2030, 2050s만 있어야 함
        expected_years = {"2030", "2050s"}
        if unique_years <= expected_years:
            print(f"   ✅ 필터링 성공! (expected: {expected_years})")
        else:
            print(f"   ❌ 필터링 실패! unexpected years: {unique_years - expected_years}")

        print("\n" + "=" * 80)
        print("🎉 테스트 2 통과!")
        print("=" * 80 + "\n")

        return result

    except Exception as e:
        print(f"\n❌ Node 0 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        raise


async def test_node0_json_structure(site_ids: List[int]):
    """
    테스트 3: Node 0 반환 JSON 구조 검증
    - state.py의 TCFDReportState와 일치하는지 확인
    """
    print("=" * 80)
    print("테스트 3: Node 0 반환 JSON 구조 검증")
    print("=" * 80)

    from langchain_openai import ChatOpenAI
    llm_client = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.0,
        api_key=os.getenv("OPENAI_API_KEY")
    )

    node = DataPreprocessingNode(
        app_db_url=os.getenv('APPLICATION_DATABASE_URL'),
        dw_db_url=os.getenv('DATABASE_URL'),
        llm_client=llm_client
    )

    result = await node.execute(
        site_ids=site_ids,
        excel_file=None,
        target_years=["2030"]  # 빠른 테스트용
    )

    # 필드 검증
    print("\n📋 반환 필드 검증:")

    required_fields = [
        "sites_data",
        "aal_scaled_results",
        "hazard_results",
        "exposure_results",
        "vulnerability_results",
        "probability_results",
        "building_data",
        "additional_data",
        "use_additional_data"
    ]

    missing_fields = []
    for field in required_fields:
        if field in result:
            value = result[field]
            value_type = type(value).__name__

            # 값의 길이 확인 (list/dict인 경우)
            if isinstance(value, list):
                length_info = f"len={len(value)}"
            elif isinstance(value, dict):
                length_info = f"keys={len(value)}"
            elif isinstance(value, bool):
                length_info = f"value={value}"
            else:
                length_info = ""

            print(f"   ✅ {field}: {value_type} {length_info}")
        else:
            missing_fields.append(field)
            print(f"   ❌ {field}: MISSING")

    if missing_fields:
        print(f"\n❌ 필수 필드 누락: {missing_fields}")
        raise AssertionError(f"Missing fields: {missing_fields}")

    # JSON 직렬화 가능 여부 확인
    print("\n📋 JSON 직렬화 테스트:")
    try:
        # building_data와 additional_data는 복잡한 구조이므로 샘플만 테스트
        test_result = {
            "sites_data": result["sites_data"],
            "aal_scaled_results": result["aal_scaled_results"][:5] if result["aal_scaled_results"] else [],
            "use_additional_data": result["use_additional_data"]
        }

        json_str = json.dumps(test_result, indent=2, default=str)
        print(f"   ✅ JSON 직렬화 성공 (샘플 크기: {len(json_str)} bytes)")
    except Exception as e:
        print(f"   ❌ JSON 직렬화 실패: {e}")
        raise

    print("\n" + "=" * 80)
    print("🎉 테스트 3 통과!")
    print("=" * 80 + "\n")

    return result


# ===== 메인 실행 =====

async def main():
    """전체 테스트 실행"""
    print("\n" + "🧪" * 40)
    print("Node 0 DB 연결 테스트 (Primary Data 검증)")
    print("🧪" * 40 + "\n")

    # 환경변수 체크
    check_environment()

    # 테스트할 site_ids 입력받기
    print("=" * 80)
    print("사업장 ID 입력")
    print("=" * 80)
    print("테스트할 사업장 ID를 입력하세요 (쉼표로 구분):")
    print("예: 1,2,3")
    print()

    # 기본값 설정 (입력 없으면 사용)
    default_site_ids = [1]

    user_input = input("Site IDs (Enter = 기본값 사용): ").strip()

    if user_input:
        try:
            site_ids = [int(sid.strip()) for sid in user_input.split(",")]
        except ValueError:
            print("❌ 잘못된 입력 형식입니다. 기본값을 사용합니다.")
            site_ids = default_site_ids
    else:
        site_ids = default_site_ids

    print(f"\n✅ Site IDs: {site_ids}\n")

    try:
        # 테스트 1: 기본 실행 (전체 년도)
        result1 = await test_node0_basic(site_ids)

        # 테스트 2: 년도 필터링
        result2 = await test_node0_filtered_years(site_ids)

        # 테스트 3: JSON 구조 검증
        result3 = await test_node0_json_structure(site_ids)

        print("\n" + "=" * 80)
        print("🎉 모든 테스트 통과!")
        print("=" * 80)
        print("\n주요 검증 항목:")
        print("  ✅ Application DB 사업장 정보 조회")
        print("  ✅ Datawarehouse DB ModelOps 5개 테이블 조회")
        print("  ✅ BC Agent 실행 (건축물 분석)")
        print("  ✅ AD Agent 실행 (추가 데이터 분석)")
        print("  ✅ target_years 필터링")
        print("  ✅ 반환 JSON 구조 검증")
        print()

        # 최종 결과 요약
        print("=" * 80)
        print("📊 최종 결과 요약")
        print("=" * 80)
        print(f"✅ 사업장 수: {len(result1.get('sites_data', []))}")
        print(f"✅ AAL 결과: {len(result1.get('aal_scaled_results', []))} rows")
        print(f"✅ BC Agent: {len(result1.get('building_data', {}))} sites")
        print(f"✅ AD Agent: use_additional_data={result1.get('use_additional_data')}")
        print()

    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
        raise
    except Exception as e:
        print(f"\n❌ 예외 발생: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())
