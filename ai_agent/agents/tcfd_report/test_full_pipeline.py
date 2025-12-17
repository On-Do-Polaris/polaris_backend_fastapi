"""
TCFD 전체 파이프라인 테스트 (Mock Data + 실제 LLM)
작성일: 2025-12-17

테스트 플로우:
1. Mock 데이터 생성 (Node 0 출력 시뮬레이션)
2. Mock 템플릿 생성 (Node 1 출력 시뮬레이션)
3. Node 2-A: Scenario Analysis (LLM 실행)
4. Node 2-B: Impact Analysis (LLM 실행)
5. Node 2-C: Mitigation Strategies (LLM 실행)
6. Node 3: Strategy Section (LLM 실행)
7. Node 5: Composer (조립)
8. 결과를 프론트엔드 JSON 형식으로 변환
9. test_output 폴더에 저장
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

# 경로 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from dotenv import load_dotenv
load_dotenv()

# LLM 클라이언트 설정
from langchain_openai import ChatOpenAI


# ============================================================
# Mock Data 생성 (Node 0 출력 시뮬레이션)
# ============================================================

RISK_TYPES = [
    "river_flood", "urban_flood", "typhoon",
    "extreme_heat", "extreme_cold", "drought",
    "water_stress", "wildfire", "sea_level_rise"
]

SITES = [
    {"id": 1, "name": "SK 판교캠퍼스", "lat": 37.4025, "lon": 127.1024, "address": "경기도 성남시 분당구 판교로 255번길 38"},
    {"id": 2, "name": "부산 물류센터", "lat": 35.1796, "lon": 129.0756, "address": "부산광역시 해운대구 APEC로 55"},
    {"id": 3, "name": "대전 R&D센터", "lat": 36.3504, "lon": 127.3845, "address": "대전광역시 유성구 테크노중앙로 123"},
    {"id": 4, "name": "인천 공장", "lat": 37.4563, "lon": 126.7052, "address": "인천광역시 남동구 논현동 123-45"},
    {"id": 5, "name": "광주 지점", "lat": 35.1595, "lon": 126.8526, "address": "광주광역시 서구 치평동 456-78"},
    {"id": 6, "name": "울산 공장", "lat": 35.5384, "lon": 129.3114, "address": "울산광역시 남구 산업로 789"},
    {"id": 7, "name": "대구 물류", "lat": 35.8714, "lon": 128.6014, "address": "대구광역시 달서구 월배로 321"},
    {"id": 8, "name": "제주 지점", "lat": 33.4996, "lon": 126.5312, "address": "제주특별자치도 제주시 연동 111-22"}
]


def generate_mock_sites_data() -> List[Dict]:
    """Mock sites_data 생성 (Node 0 출력)"""
    sites_data = []

    for site in SITES:
        risk_results = []
        for risk_type in RISK_TYPES:
            # 결정적인 AAL 생성
            seed_val = hash(f"{site['id']}{risk_type}") % 100
            aal = 5.0 + (seed_val / 10)  # 5% ~ 15% 범위

            risk_results.append({
                "risk_type": risk_type,
                "final_aal": round(aal, 2),
                "ssp126_final_aal": round(aal * 0.8, 2),
                "ssp245_final_aal": round(aal, 2),
                "ssp370_final_aal": round(aal * 1.2, 2),
                "ssp585_final_aal": round(aal * 1.5, 2),
            })

        sites_data.append({
            "site_id": site["id"],
            "site_name": site["name"],
            "site_info": {
                "name": site["name"],
                "latitude": site["lat"],
                "longitude": site["lon"],
                "address": site["address"]
            },
            "risk_results": risk_results
        })

    return sites_data


def generate_mock_building_data() -> Dict[int, Dict]:
    """Mock building_data 생성 (BC Agent 결과)"""
    building_data = {}

    for site in SITES:
        building_data[site["id"]] = {
            "agent_guidelines": {
                "data_summary": f"{site['name']}은 철근콘크리트 구조의 22층 건물입니다.",
                "report_guidelines": {
                    "financial_impact": "연간 유지보수비 약 5억원 예상",
                    "operational_impact": "지하 기계실 침수 시 운영 중단 가능",
                    "asset_impact": "내진설계 적용으로 지진 리스크 낮음"
                }
            },
            "building_summary": {
                "road_address": site["address"],
                "building_count": 1,
                "structure_types": ["철근콘크리트구조"],
                "purpose_types": ["업무시설", "교육연구시설"],
                "max_ground_floors": 22,
                "max_underground_floors": 3,
                "buildings_with_seismic": 1,
                "oldest_building_age_years": 15,
                "total_floor_area_sqm": 85000.0,
                "floor_range": "B3~22F",
                "detected_facilities": {
                    "저수조": True,
                    "비상발전": True,
                    "방재시설": True,
                    "기계실": True,
                    "전산실": True
                }
            }
        }

    return building_data


def generate_mock_report_template() -> Dict:
    """Mock report_template 생성 (Node 1 출력)"""
    return {
        "template_id": "tcfd_template_v2",
        "document_structure": {
            "title": "TCFD 기후 리스크 보고서",
            "sections": ["governance", "strategy", "risk_management", "metrics_targets", "appendix"]
        },
        "tone_and_style": {
            "formality": "formal",
            "technical_level": "professional",
            "language": "Korean"
        },
        "hazard_template_blocks": {
            "description": "각 리스크별 영향 분석 및 대응 전략을 포함",
            "structure": ["리스크 개요", "재무적 영향", "운영적 영향", "자산 영향", "대응 전략"]
        },
        "scenario_templates": {
            "ssp1_2.6": "지속가능 발전 시나리오 (1.5°C 목표)",
            "ssp2_4.5": "중간 경로 시나리오 (2.0-2.5°C)",
            "ssp3_7.0": "지역 경쟁 시나리오 (3.0-3.5°C)",
            "ssp5_8.5": "화석연료 집약 시나리오 (4.0°C+)"
        },
        "reusable_paragraphs": [
            "우리는 기후 변화가 사업에 미치는 잠재적 영향을 인식하고 있습니다.",
            "TCFD 권고안에 따라 기후 관련 재무 정보를 공개합니다.",
            "지속적인 모니터링과 적응을 통해 기후 리스크에 대응합니다."
        ]
    }


def convert_to_frontend_format(report: Dict) -> Dict:
    """
    Node 5 출력을 프론트엔드 JSON 형식으로 변환

    변환 내용:
    1. table 블록의 headers/items 형식 변환
    2. line_chart → table로 변환 (필요시)
    """
    frontend_report = {
        "report_id": report.get("report_id", f"tcfd_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
        "meta": {
            "title": report.get("meta", {}).get("title", "TCFD 기후 리스크 보고서"),
            "generated_at": report.get("meta", {}).get("generated_at", datetime.now().isoformat()),
            "site_count": report.get("meta", {}).get("site_count", 8),
            "total_aal": report.get("meta", {}).get("total_aal", 52.9)
        },
        "sections": []
    }

    for section in report.get("sections", []):
        frontend_section = {
            "section_id": section.get("section_id"),
            "title": section.get("title"),
            "blocks": []
        }

        for block in section.get("blocks", []):
            block_type = block.get("type")

            if block_type == "text":
                frontend_section["blocks"].append({
                    "type": "text",
                    "subheading": block.get("subheading"),
                    "content": block.get("content")
                })

            elif block_type == "table" or block_type == "heatmap_table":
                # 테이블 형식 변환
                headers = block.get("headers", [])
                rows = block.get("rows", []) or block.get("items", [])

                # headers 변환
                if headers and isinstance(headers[0], str):
                    headers = [{"text": h, "value": h.lower().replace(" ", "_")} for h in headers]

                frontend_section["blocks"].append({
                    "type": "table",
                    "title": block.get("title"),
                    "subheading": block.get("subheading"),
                    "headers": headers,
                    "items": rows,
                    "legend": block.get("legend")
                })

            elif block_type == "line_chart":
                # 차트를 테이블로 변환
                data = block.get("data", {})
                x_categories = data.get("x_axis", {}).get("categories", [])
                series = data.get("series", [])

                headers = [{"text": "시나리오", "value": "scenario"}]
                headers.extend([{"text": str(year), "value": f"year_{year}"} for year in x_categories])

                items = []
                for s in series:
                    item = {"scenario": s.get("name")}
                    for i, year in enumerate(x_categories):
                        if i < len(s.get("data", [])):
                            item[f"year_{year}"] = f"{s['data'][i]:.1f}%"
                    items.append(item)

                frontend_section["blocks"].append({
                    "type": "table",
                    "title": block.get("title"),
                    "subheading": "AAL 추이",
                    "headers": headers,
                    "items": items
                })

        frontend_report["sections"].append(frontend_section)

    return frontend_report


async def run_test():
    """전체 파이프라인 테스트 실행"""
    print("="*80)
    print("TCFD 전체 파이프라인 테스트 시작 (Node 2-A ~ Node 5)")
    print("="*80)

    # LLM 클라이언트 초기화
    print("\n[1/9] LLM 클라이언트 초기화...")
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3
    )
    print("  ✅ LLM 클라이언트 초기화 완료")

    # Mock 데이터 생성 (Node 0 출력)
    print("\n[2/9] Mock 데이터 생성 (Node 0 출력 시뮬레이션)...")
    sites_data = generate_mock_sites_data()
    building_data = generate_mock_building_data()
    print(f"  ✅ {len(sites_data)}개 사업장, {len(RISK_TYPES)}개 리스크 데이터 생성")

    # Mock 템플릿 생성 (Node 1 출력)
    print("\n[3/9] Mock 템플릿 생성 (Node 1 출력 시뮬레이션)...")
    report_template = generate_mock_report_template()
    print("  ✅ 보고서 템플릿 생성 완료")

    # Node 2-A: Scenario Analysis (LLM 실행)
    print("\n[4/9] Node 2-A: Scenario Analysis 실행...")
    from ai_agent.agents.tcfd_report.node_2a_scenario_analysis import ScenarioAnalysisNode

    node_2a = ScenarioAnalysisNode(llm_client=llm)
    result_2a = await node_2a.execute(
        sites_data=sites_data,
        report_template=report_template
    )
    scenarios = result_2a.get("scenarios", {})
    print(f"  ✅ Node 2-A 완료: {len(scenarios)}개 시나리오 분석")

    # Node 2-B: Impact Analysis (LLM 실행)
    print("\n[5/9] Node 2-B: Impact Analysis 실행...")
    from ai_agent.agents.tcfd_report.node_2b_impact_analysis import ImpactAnalysisNode

    node_2b = ImpactAnalysisNode(llm_client=llm)
    result_2b = await node_2b.execute(
        sites_data=sites_data,
        scenario_analysis=result_2a,
        report_template=report_template,
        building_data=building_data
    )
    impact_analyses = result_2b.get("impact_analyses", [])
    impact_blocks = result_2b.get("impact_blocks", [])
    print(f"  ✅ Node 2-B 완료: {len(impact_analyses)}개 리스크 영향 분석")

    # Node 2-C: Mitigation Strategies (LLM 실행)
    print("\n[6/9] Node 2-C: Mitigation Strategies 실행...")
    from ai_agent.agents.tcfd_report.node_2c_mitigation_strategies import MitigationStrategiesNode

    node_2c = MitigationStrategiesNode(llm_client=llm)
    result_2c = await node_2c.execute(
        impact_analyses=impact_analyses,
        report_template=report_template,
        building_data=building_data
    )
    mitigation_strategies = result_2c.get("mitigation_strategies", [])
    mitigation_blocks = result_2c.get("mitigation_blocks", [])
    implementation_roadmap = result_2c.get("implementation_roadmap", {})
    print(f"  ✅ Node 2-C 완료: {len(mitigation_strategies)}개 대응 전략 생성")

    # Node 3: Strategy Section (LLM 실행)
    print("\n[7/9] Node 3: Strategy Section 실행...")
    from ai_agent.agents.tcfd_report.node_3_strategy_section import StrategySectionNode

    node_3 = StrategySectionNode(llm_client=llm)
    result_3 = await node_3.execute(
        scenario_analysis=result_2a,
        impact_analyses=impact_analyses,
        mitigation_strategies=mitigation_strategies,
        sites_data=sites_data,
        impact_blocks=impact_blocks,
        mitigation_blocks=mitigation_blocks,
        report_template=report_template,
        implementation_roadmap=implementation_roadmap
    )
    strategy_section = result_3
    print(f"  ✅ Node 3 완료: Strategy 섹션 생성")

    # Node 5: Composer 실행
    print("\n[8/9] Node 5: Composer 실행...")
    from ai_agent.agents.tcfd_report.node_5_composer import ComposerNode

    composer = ComposerNode(llm_client=llm)
    result = await composer.execute(
        strategy_section=strategy_section,
        scenarios=scenarios,
        mitigation_strategies=mitigation_strategies,
        sites_data=sites_data,
        impact_analyses=impact_analyses
    )

    report = result.get("report", {})
    print(f"  ✅ 보고서 생성 완료: {len(report.get('sections', []))}개 섹션")

    # 프론트엔드 형식으로 변환
    print("\n[9/9] 프론트엔드 JSON 형식으로 변환...")
    frontend_report = convert_to_frontend_format(report)
    print(f"  ✅ 변환 완료: {len(frontend_report.get('sections', []))}개 섹션")

    # 결과 저장
    print("\n" + "="*80)
    print("결과 저장 중...")
    print("="*80)
    output_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'test_output')
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # 원본 보고서 저장
    raw_output_path = os.path.join(output_dir, f'tcfd_report_raw_{timestamp}.json')
    with open(raw_output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"  ✅ 원본 보고서 저장: {raw_output_path}")

    # 프론트엔드 형식 저장
    frontend_output_path = os.path.join(output_dir, f'tcfd_report_frontend_{timestamp}.json')
    with open(frontend_output_path, 'w', encoding='utf-8') as f:
        json.dump(frontend_report, f, ensure_ascii=False, indent=2)
    print(f"  ✅ 프론트엔드 보고서 저장: {frontend_output_path}")

    # 검증
    print("\n" + "="*80)
    print("결과 검증")
    print("="*80)
    print(f"  - report_id: {frontend_report.get('report_id')}")
    print(f"  - 섹션 수: {len(frontend_report.get('sections', []))}")
    for section in frontend_report.get("sections", []):
        block_count = len(section.get('blocks', []))
        print(f"    - {section.get('title')}: {block_count}개 블록")

    # 샘플 출력 (Strategy 섹션 일부)
    print("\n" + "="*80)
    print("Strategy 섹션 샘플 (LLM 생성 결과)")
    print("="*80)
    strategy_section_output = next(
        (s for s in frontend_report.get("sections", []) if s.get("section_id") == "strategy"),
        None
    )
    if strategy_section_output:
        for block in strategy_section_output.get("blocks", [])[:3]:
            if block.get("type") == "text":
                print(f"\n[{block.get('subheading', 'N/A')}]")
                content = block.get("content", "")
                # 처음 500자만 출력
                if len(content) > 500:
                    print(content[:500] + "...")
                else:
                    print(content)
                print("-" * 40)

    print("\n" + "="*80)
    print("✅ 전체 파이프라인 테스트 완료!")
    print(f"   출력 파일: {frontend_output_path}")
    print("="*80)

    return frontend_report


if __name__ == "__main__":
    asyncio.run(run_test())
