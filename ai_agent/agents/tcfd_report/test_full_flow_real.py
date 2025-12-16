"""
TCFD Report 전체 플로우 테스트 (Real Data)
Node 0 실제 데이터 → Node 1~6 순차 실행

작성일: 2025-12-16
버전: v01

사용법:
    python -m ai_agent.agents.tcfd_report.test_full_flow_real
"""

import asyncio
import logging
import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_full_flow_real")


async def run_full_flow_with_real_data():
    """Node 0 실제 데이터로 전체 플로우 테스트"""

    print("\n" + "=" * 80)
    print("🚀 TCFD Report 전체 플로우 테스트 (Real Data)")
    print("=" * 80)

    # ========== Step 0: Node 0 실행 (실제 데이터) ==========
    print("\n[Step 0] Node 0: Data Preprocessing 실행 (Real DB Data)...")

    from langchain_openai import ChatOpenAI
    from .node_0_data_preprocessing import DataPreprocessingNode

    # 실제 테스트 사이트 ID
    site_ids = [
        "22222222-2222-2222-2222-222222222222",  # SK 판교캠퍼스
        "44444444-4444-4444-4444-444444444444",  # SK u-타워
    ]

    # DB URL
    app_db_url = "postgresql://skala:skala1234@localhost:5555/application"
    dw_db_url = "postgresql://skala:skala1234@localhost:5555/datawarehouse"

    # LLM 클라이언트 (모든 노드에서 공유)
    llm_client = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    print("  📌 LLM: gpt-4o-mini (Real API)")

    # Node 0 실행
    node_0 = DataPreprocessingNode(
        app_db_url=app_db_url,
        dw_db_url=dw_db_url,
        llm_client=llm_client,
    )

    state = await node_0.execute(
        site_ids=site_ids,
        target_years=["2025", "2030", "2050s"]
    )

    # State에서 데이터 추출
    site_data_raw = state.get("site_data", [])
    building_data = state.get("building_data", {})
    additional_data = state.get("additional_data", {})
    hazard_results = state.get("hazard_results", [])
    aal_results = state.get("aal_scaled_results", [])

    print(f"  ✅ site_data: {len(site_data_raw)}개 사업장")
    print(f"  ✅ building_data: {len(building_data)}개 사업장")
    print(f"  ✅ additional_data: {additional_data.get('status', 'N/A') if isinstance(additional_data, dict) else 'N/A'}")
    print(f"  ✅ hazard_results: {len(hazard_results)}개 레코드")
    print(f"  ✅ aal_results: {len(aal_results)}개 레코드")

    # site_data를 dict로 변환 (site_id를 키로)
    site_data_dict = {}
    if isinstance(site_data_raw, list):
        for info in site_data_raw:
            sid = str(info.get("id") or info.get("site_id", ""))
            site_data_dict[sid] = info
    elif isinstance(site_data_raw, dict):
        site_data_dict = site_data_raw

    # sites_data 형식 변환 (Node 1~6에서 사용하는 형식으로)
    sites_data = []
    for sid, info in site_data_dict.items():
        # AAL 결과에서 해당 사이트의 리스크 데이터 추출
        site_aal = [r for r in aal_results if str(r.get('site_id')) == str(sid)]

        risk_results = []
        for r in site_aal:
            risk_results.append({
                "risk_type": r.get("risk_type"),
                "target_year": r.get("target_year"),
                "final_aal": float(r.get("ssp245_final_aal", 0) or 0),
                "hazard_score": float(r.get("ssp245_score_100", 0) or 0) if "ssp245_score_100" in r else 50,
                "exposure_score": 50,  # 기본값
                "vulnerability_score": 50,  # 기본값
            })

        # site_info가 중첩 구조인 경우 처리
        site_info_data = info.get("site_info", info)
        site_name = site_info_data.get("name", "Unknown")

        sites_data.append({
            "site_id": sid,
            "site_name": site_name,
            "site_info": {
                "name": site_name,
                "latitude": float(site_info_data.get("latitude", 0) or 0),
                "longitude": float(site_info_data.get("longitude", 0) or 0),
                "address": site_info_data.get("address") or site_info_data.get("road_address", ""),
                "type": site_info_data.get("type", "office")
            },
            "risk_results": risk_results
        })

    print(f"  ✅ sites_data 변환 완료: {len(sites_data)}개")

    # ========== Step 1: Node 1 - Template Loading ==========
    print("\n[Step 1] Node 1: Template Loading 실행...")

    from .node_1_template_loading_v2 import TemplateLoadingNode

    node_1 = TemplateLoadingNode(llm_client=llm_client)

    result_1 = await node_1.execute(
        company_name="SK 테스트",
        past_reports=[],
        mode="init"
    )

    report_template = result_1.get("report_template", {})
    print(f"  ✅ report_template 생성 완료")

    # ========== Step 2: Node 2-A - Scenario Analysis ==========
    print("\n[Step 2] Node 2-A: Scenario Analysis 실행...")

    from .node_2a_scenario_analysis_v2 import ScenarioAnalysisNode

    node_2a = ScenarioAnalysisNode(llm_client=llm_client)

    result_2a = await node_2a.execute(
        sites_data=sites_data,
        report_template=report_template,
        agent_guideline=None
    )

    scenario_analysis = result_2a
    print(f"  ✅ scenario_analysis 생성 완료: {list(result_2a.get('scenarios', {}).keys())}")

    # ========== Step 3: Node 2-B - Impact Analysis ==========
    print("\n[Step 3] Node 2-B: Impact Analysis 실행...")

    from .node_2b_impact_analysis_v2 import ImpactAnalysisNode

    node_2b = ImpactAnalysisNode(llm_client=llm_client)

    result_2b = await node_2b.execute(
        sites_data=sites_data,
        scenario_analysis=scenario_analysis,
        report_template=report_template,
        building_data=building_data,
        additional_data=additional_data,
        sites_metadata=None
    )

    impact_analyses = result_2b.get("impact_analyses", [])
    impact_blocks = result_2b.get("impact_blocks", [])
    top_5_risks = result_2b.get("top_5_risks", [])

    print(f"  ✅ impact_analyses: {len(impact_analyses)}개")
    print(f"  ✅ impact_blocks: {len(impact_blocks)}개")
    print(f"  ✅ Top 5 리스크:")
    for i, risk in enumerate(top_5_risks[:5], 1):
        print(f"     P{i}. {risk.get('risk_type')}: AAL {risk.get('total_aal', 0):.2f}")

    # ========== Step 4: Node 2-C - Mitigation Strategies ==========
    print("\n[Step 4] Node 2-C: Mitigation Strategies 실행...")

    from .node_2c_mitigation_strategies_v2 import MitigationStrategiesNode

    node_2c = MitigationStrategiesNode(llm_client=llm_client)

    result_2c = await node_2c.execute(
        impact_analyses=impact_analyses,
        report_template=report_template,
        building_data=building_data,
        additional_data=additional_data,
        company_context=None
    )

    mitigation_strategies = result_2c.get("mitigation_strategies", [])
    mitigation_blocks = result_2c.get("mitigation_blocks", [])
    implementation_roadmap = result_2c.get("implementation_roadmap", {})

    print(f"  ✅ mitigation_strategies: {len(mitigation_strategies)}개")
    print(f"  ✅ mitigation_blocks: {len(mitigation_blocks)}개")

    # ========== Step 5: Node 3 - Strategy Section ==========
    print("\n[Step 5] Node 3: Strategy Section 실행...")

    from .node_3_strategy_section_v2 import StrategySectionNode

    node_3 = StrategySectionNode(llm_client=llm_client)

    result_3 = await node_3.execute(
        scenario_analysis=scenario_analysis,
        impact_analyses=impact_analyses,
        mitigation_strategies=mitigation_strategies,
        sites_data=sites_data,
        impact_blocks=impact_blocks,
        mitigation_blocks=mitigation_blocks,
        report_template=report_template,
        implementation_roadmap=implementation_roadmap
    )

    strategy_section = result_3
    heatmap_table_block = result_3.get("heatmap_table_block", {})

    print(f"  ✅ strategy_section: {len(result_3.get('blocks', []))}개 블록")
    print(f"  ✅ heatmap_table_block: {'생성됨' if heatmap_table_block else '없음'}")

    # ========== Step 6: Node 4 - Validator ==========
    print("\n[Step 6] Node 4: Validator 실행...")

    from .node_4_validator_v2 import ValidatorNode

    node_4 = ValidatorNode(llm_client=llm_client)

    result_4 = await node_4.execute(
        strategy_section=strategy_section,
        report_template=report_template,
        scenario_analysis=scenario_analysis,
        impact_analyses=impact_analyses
    )

    validation_result = result_4.get("validation_result", {})
    is_valid = result_4.get("validated", False)
    quality_score = validation_result.get("quality_score", 0)

    print(f"  ✅ 검증: {'PASS' if is_valid else 'FAIL'} (점수: {quality_score})")

    # ========== Step 7: Node 5 - Composer ==========
    print("\n[Step 7] Node 5: Composer 실행...")

    from .node_5_composer_v2 import ComposerNode

    node_5 = ComposerNode(llm_client=llm_client)

    result_5 = await node_5.execute(
        strategy_section=strategy_section,
        scenarios=scenario_analysis,
        mitigation_strategies=mitigation_strategies,
        sites_data=sites_data,
        impact_analyses=impact_analyses
    )

    report = result_5.get("report", {})
    sections = report.get("sections", [])

    print(f"  ✅ report sections: {len(sections)}개")

    # ========== Step 8: Node 6 - Finalizer (Mock) ==========
    print("\n[Step 8] Node 6: Finalizer 실행 (DB 저장 생략)...")

    from .node_6_finalizer_v2 import FinalizerNode

    node_6 = FinalizerNode(db_session=None)

    result_6 = await node_6.execute(
        report=report,
        user_id=1,
        site_ids=[1, 2]
    )

    print(f"  ✅ Finalizer 완료: success={result_6.get('success', False)}")

    # ========== 결과 요약 ==========
    print("\n" + "=" * 80)
    print("📊 전체 플로우 테스트 결과 요약 (Real Data)")
    print("=" * 80)

    print("\n[Node 0 - Real DB Data]")
    print(f"  sites: {[s['site_name'] for s in sites_data]}")
    print(f"  building_data: {list(building_data.keys())[:2]}...")
    print(f"  additional_data status: {additional_data.get('status', 'N/A')}")

    print("\n[Node 1~6 실행 결과]")
    print(f"  Node 1 → report_template: ✅")
    print(f"  Node 2-A → scenarios: {len(result_2a.get('scenarios', {}))}개")
    print(f"  Node 2-B → impact_analyses: {len(impact_analyses)}개")
    print(f"  Node 2-C → mitigation_strategies: {len(mitigation_strategies)}개")
    print(f"  Node 3 → strategy_section: {len(result_3.get('blocks', []))}개 블록")
    print(f"  Node 4 → validation: {'✅ PASS' if is_valid else '❌ FAIL'}")
    print(f"  Node 5 → report: {len(sections)}개 섹션")
    print(f"  Node 6 → saved: {result_6.get('success', False)}")

    print("\n[building_data / additional_data 활용]")
    print(f"  building_data 전달: {'✅' if building_data else '❌'}")
    print(f"  additional_data 전달: {'✅' if additional_data else '❌'}")

    # 판교캠퍼스 building_data 샘플
    pangyo_id = "22222222-2222-2222-2222-222222222222"
    if pangyo_id in building_data:
        bd = building_data[pangyo_id]
        print(f"\n[판교캠퍼스 building_data 샘플]")
        print(f"  structural_grade: {bd.get('structural_grade', 'N/A')}")
        if 'agent_guidelines' in bd:
            ag = bd['agent_guidelines']
            print(f"  agent_guidelines keys: {list(ag.keys())[:3]}...")

    # 판교캠퍼스 additional_data 샘플
    if additional_data and 'site_specific_guidelines' in additional_data:
        ssg = additional_data['site_specific_guidelines']
        if pangyo_id in ssg:
            ad = ssg[pangyo_id]
            print(f"\n[판교캠퍼스 additional_data 샘플]")
            print(f"  guideline 길이: {len(ad.get('guideline', ''))} chars")
            print(f"  key_insights: {len(ad.get('key_insights', []))}개")

    print("\n" + "=" * 80)
    print("✅ 전체 플로우 테스트 완료! (Node 0 Real Data → Node 1~6)")
    print("=" * 80)

    return {
        "state": state,
        "sites_data": sites_data,
        "building_data": building_data,
        "additional_data": additional_data,
        "report_template": report_template,
        "scenario_analysis": scenario_analysis,
        "impact_analyses": impact_analyses,
        "mitigation_strategies": mitigation_strategies,
        "strategy_section": strategy_section,
        "validation_result": validation_result,
        "report": report,
    }


def main():
    """메인 실행"""
    result = asyncio.run(run_full_flow_with_real_data())

    # 결과 저장
    output_path = Path(__file__).parent / "test_output_real.json"
    with open(output_path, "w", encoding="utf-8") as f:
        # Decimal, datetime 등 직렬화 처리
        def json_serializer(obj):
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            if hasattr(obj, '__float__'):
                return float(obj)
            return str(obj)

        json.dump(result, f, ensure_ascii=False, indent=2, default=json_serializer)
    print(f"\n📁 결과 저장: {output_path}")


if __name__ == "__main__":
    main()
