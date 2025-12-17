"""
TCFD Report 전체 파이프라인 테스트
Node 0 ~ Node 6 순차 실행
"""
import os
import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime

# .env 로드
from dotenv import load_dotenv
load_dotenv()

# LLM 설정
from langchain_openai import ChatOpenAI

print("\n" + "=" * 80)
print("🚀 TCFD Report 전체 플로우 테스트 (Real Data)")
print("=" * 80)

# DB URL
app_db_url = os.getenv("APPLICATION_DATABASE_URL")
dw_db_url = os.getenv("DATAWAREHOUSE_DATABASE_URL")
print(f"App DB: {app_db_url[:40]}...")
print(f"DW DB: {dw_db_url[:40]}...")

# LLM 클라이언트
llm_client = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
print("LLM: gpt-4o-mini")

# 테스트 사이트 ID
site_ids = [
    "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",  # SK 판교캠퍼스
    "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",  # 부산 물류센터
]

async def run_pipeline():
    # ========== Node 0 ==========
    print("\n[Step 0] Node 0: Data Preprocessing...")
    from ai_agent.agents.tcfd_report.node_0_data_preprocessing import DataPreprocessingNode

    node_0 = DataPreprocessingNode(
        app_db_url=app_db_url,
        dw_db_url=dw_db_url,
        llm_client=llm_client,
    )

    state = await node_0.execute(
        site_ids=site_ids,
        target_years=["2026", "2030", "2050s"]
    )

    site_data_raw = state.get("sites_data", [])
    building_data = state.get("building_data", {})
    additional_data = state.get("additional_data", {})
    hazard_results = state.get("hazard_results", [])
    aal_results = state.get("aal_scaled_results", [])

    print(f"  ✅ sites: {len(site_data_raw)}")
    print(f"  ✅ building_data: {len(building_data)}")
    print(f"  ✅ hazard: {len(hazard_results)}, aal: {len(aal_results)}")

    # sites_data 변환
    site_data_dict = {}
    if isinstance(site_data_raw, list):
        for info in site_data_raw:
            sid = str(info.get("id") or info.get("site_id", ""))
            site_data_dict[sid] = info

    sites_data = []
    for sid, info in site_data_dict.items():
        site_aal = [r for r in aal_results if str(r.get('site_id')) == str(sid)]
        risk_results = []
        for r in site_aal:
            risk_results.append({
                "risk_type": r.get("risk_type"),
                "target_year": r.get("target_year"),
                "final_aal": float(r.get("ssp245_final_aal", 0) or 0),
                "hazard_score": 50, "exposure_score": 50, "vulnerability_score": 50,
            })
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
    print(f"  ✅ sites_data 변환: {len(sites_data)}개")

    # ========== Node 1 ==========
    print("\n[Step 1] Node 1: Template Loading...")
    from ai_agent.agents.tcfd_report.node_1_template_loading import TemplateLoadingNode

    node_1 = TemplateLoadingNode(llm_client=llm_client)
    result_1 = await node_1.execute(company_name="SK 테스트", past_reports=[], mode="init")
    report_template = result_1.get("report_template_profile", {})
    print(f"  ✅ report_template 생성")

    # ========== Node 2-A ==========
    print("\n[Step 2] Node 2-A: Scenario Analysis...")
    from ai_agent.agents.tcfd_report.node_2a_scenario_analysis import ScenarioAnalysisNode

    node_2a = ScenarioAnalysisNode(llm_client=llm_client)
    result_2a = await node_2a.execute(sites_data=sites_data, report_template=report_template, agent_guideline=None)
    scenario_analysis = result_2a
    print(f"  ✅ scenarios: {list(result_2a.get('scenarios', {}).keys())}")

    # ========== Node 2-B ==========
    print("\n[Step 3] Node 2-B: Impact Analysis...")
    from ai_agent.agents.tcfd_report.node_2b_impact_analysis import ImpactAnalysisNode

    node_2b = ImpactAnalysisNode(llm_client=llm_client)
    result_2b = await node_2b.execute(
        sites_data=sites_data, scenario_analysis=scenario_analysis, report_template=report_template,
        building_data=building_data, additional_data=additional_data, sites_metadata=None
    )
    impact_analyses = result_2b.get("impact_analyses", [])
    impact_blocks = result_2b.get("impact_blocks", [])
    top_5_risks = result_2b.get("top_5_risks", [])
    print(f"  ✅ impact_analyses: {len(impact_analyses)}, blocks: {len(impact_blocks)}")

    # ========== Node 2-C ==========
    print("\n[Step 4] Node 2-C: Mitigation Strategies...")
    from ai_agent.agents.tcfd_report.node_2c_mitigation_strategies import MitigationStrategiesNode

    node_2c = MitigationStrategiesNode(llm_client=llm_client)
    result_2c = await node_2c.execute(
        impact_analyses=impact_analyses, report_template=report_template,
        building_data=building_data, additional_data=additional_data, company_context=None
    )
    mitigation_strategies = result_2c.get("mitigation_strategies", [])
    mitigation_blocks = result_2c.get("mitigation_blocks", [])
    implementation_roadmap = result_2c.get("implementation_roadmap", {})
    print(f"  ✅ mitigation_strategies: {len(mitigation_strategies)}")

    # ========== Node 3 ==========
    print("\n[Step 5] Node 3: Strategy Section...")
    from ai_agent.agents.tcfd_report.node_3_strategy_section import StrategySectionNode

    node_3 = StrategySectionNode(llm_client=llm_client)
    result_3 = await node_3.execute(
        scenario_analysis=scenario_analysis, impact_analyses=impact_analyses,
        mitigation_strategies=mitigation_strategies, sites_data=sites_data,
        impact_blocks=impact_blocks, mitigation_blocks=mitigation_blocks,
        report_template=report_template, implementation_roadmap=implementation_roadmap
    )
    strategy_section = result_3
    print(f"  ✅ strategy_section: {len(result_3.get('blocks', []))}개 블록")

    # ========== Node 4 ==========
    print("\n[Step 6] Node 4: Validator...")
    from ai_agent.agents.tcfd_report.node_4_validator import ValidatorNode

    node_4 = ValidatorNode(llm_client=llm_client)
    result_4 = await node_4.execute(
        strategy_section=strategy_section, report_template=report_template,
        scenario_analysis=scenario_analysis, impact_analyses=impact_analyses
    )
    is_valid = result_4.get("validated", False)
    quality_score = result_4.get("validation_result", {}).get("quality_score", 0)
    print(f"  ✅ validation: {'PASS' if is_valid else 'FAIL'} (score: {quality_score})")

    # ========== Node 5 ==========
    print("\n[Step 7] Node 5: Composer...")
    from ai_agent.agents.tcfd_report.node_5_composer import ComposerNode

    node_5 = ComposerNode(llm_client=llm_client)
    result_5 = await node_5.execute(
        strategy_section=strategy_section, scenarios=scenario_analysis,
        mitigation_strategies=mitigation_strategies, sites_data=sites_data,
        impact_analyses=impact_analyses
    )
    report = result_5.get("report", {})
    sections = report.get("sections", [])
    print(f"  ✅ report: {len(sections)}개 섹션")

    # ========== Node 6 ==========
    print("\n[Step 8] Node 6: Finalizer (DB 저장)...")
    from ai_agent.agents.tcfd_report.node_6_finalizer import FinalizerNode

    node_6 = FinalizerNode(app_db_url=app_db_url)
    test_user_id = "11111111-1111-1111-1111-111111111111"
    result_6 = await node_6.execute(report=report, user_id=test_user_id, site_ids=site_ids)

    success = result_6.get('success', False)
    report_id = result_6.get('report_id', 'N/A')
    print(f"  ✅ Finalizer: {'SUCCESS' if success else 'FAIL'}")
    print(f"  ✅ Report ID: {report_id}")

    # ========== 결과 요약 ==========
    print("\n" + "=" * 80)
    print("📊 전체 플로우 테스트 결과 요약")
    print("=" * 80)
    print(f"  Node 0 → sites: {len(sites_data)}, building: {len(building_data)}, hazard: {len(hazard_results)}")
    print(f"  Node 1 → template: ✅")
    print(f"  Node 2-A → scenarios: {len(scenario_analysis.get('scenarios', {}))}")
    print(f"  Node 2-B → impact: {len(impact_analyses)}")
    print(f"  Node 2-C → mitigation: {len(mitigation_strategies)}")
    print(f"  Node 3 → strategy: {len(strategy_section.get('blocks', []))} blocks")
    print(f"  Node 4 → validation: {'PASS' if is_valid else 'FAIL'}")
    print(f"  Node 5 → report: {len(sections)} sections")
    print(f"  Node 6 → saved: {success}, id: {report_id}")
    print("=" * 80)
    print("✅ 전체 플로우 테스트 완료!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_pipeline())
