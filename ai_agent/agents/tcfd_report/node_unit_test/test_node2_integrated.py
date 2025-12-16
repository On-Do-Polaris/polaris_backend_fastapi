"""
Node 2 통합 테스트 (2-A → 2-B → 2-C)

실행 방법:
    cd c:/Users/SKAX/Documents/POLARIS/polaris_backend_fastapi-develop
    python -m ai_agent.agents.tcfd_report.test_node2_integrated

환경변수 설정 (실제 LLM 사용 시):
    set OPENAI_API_KEY=your_key_here
    set USE_REAL_LLM=true
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime


def create_sample_sites_data():
    """테스트용 샘플 사업장 데이터 생성 (8개 사업장)"""
    return [
        {
            "site_id": "site_001",
            "site_name": "서울 본사",
            "risk_results": [
                {
                    "risk_type": "river_flood",
                    "final_aal": 7.2,
                    "scenarios": {
                        "ssp1_2.6": {"2025": 7.2, "2030": 7.0, "2040": 6.5, "2050": 6.0, "2100": 5.5},
                        "ssp2_4.5": {"2025": 7.2, "2030": 7.5, "2040": 8.2, "2050": 9.0, "2100": 10.1},
                        "ssp3_7.0": {"2025": 7.2, "2030": 8.0, "2040": 9.5, "2050": 11.0, "2100": 12.5},
                        "ssp5_8.5": {"2025": 7.2, "2030": 8.5, "2040": 10.5, "2050": 13.0, "2100": 15.2}
                    }
                },
                {
                    "risk_type": "urban_flood",
                    "final_aal": 5.1,
                    "scenarios": {
                        "ssp1_2.6": {"2025": 5.1, "2030": 5.0, "2040": 4.8, "2050": 4.5, "2100": 4.2},
                        "ssp2_4.5": {"2025": 5.1, "2030": 5.3, "2040": 5.8, "2050": 6.2, "2100": 6.8},
                        "ssp3_7.0": {"2025": 5.1, "2030": 5.8, "2040": 6.8, "2050": 7.5, "2100": 8.5},
                        "ssp5_8.5": {"2025": 5.1, "2030": 6.2, "2040": 7.8, "2050": 9.2, "2100": 11.0}
                    }
                }
            ]
        },
        {
            "site_id": "site_002",
            "site_name": "판교 데이터센터",
            "risk_results": [
                {
                    "risk_type": "river_flood",
                    "final_aal": 11.0,
                    "scenarios": {
                        "ssp1_2.6": {"2025": 11.0, "2030": 10.5, "2040": 10.0, "2050": 9.5, "2100": 9.0},
                        "ssp2_4.5": {"2025": 11.0, "2030": 11.5, "2040": 12.5, "2050": 13.5, "2100": 14.8},
                        "ssp3_7.0": {"2025": 11.0, "2030": 12.0, "2040": 14.0, "2050": 16.0, "2100": 18.0},
                        "ssp5_8.5": {"2025": 11.0, "2030": 13.0, "2040": 16.0, "2050": 19.0, "2100": 22.5}
                    }
                },
                {
                    "risk_type": "extreme_heat",
                    "final_aal": 5.5,
                    "scenarios": {
                        "ssp1_2.6": {"2025": 5.5, "2030": 5.3, "2040": 5.0, "2050": 4.8, "2100": 4.5},
                        "ssp2_4.5": {"2025": 5.5, "2030": 6.0, "2040": 7.0, "2050": 8.0, "2100": 9.2},
                        "ssp3_7.0": {"2025": 5.5, "2030": 6.5, "2040": 8.0, "2050": 10.0, "2100": 12.0},
                        "ssp5_8.5": {"2025": 5.5, "2030": 7.0, "2040": 9.5, "2050": 12.0, "2100": 15.0}
                    }
                }
            ]
        },
        {
            "site_id": "site_003",
            "site_name": "부산 사업장",
            "risk_results": [
                {
                    "risk_type": "typhoon",
                    "final_aal": 9.3,
                    "scenarios": {
                        "ssp1_2.6": {"2025": 9.3, "2030": 9.0, "2040": 8.5, "2050": 8.0, "2100": 7.5},
                        "ssp2_4.5": {"2025": 9.3, "2030": 9.8, "2040": 10.8, "2050": 11.5, "2100": 12.5},
                        "ssp3_7.0": {"2025": 9.3, "2030": 10.5, "2040": 12.5, "2050": 14.0, "2100": 15.8},
                        "ssp5_8.5": {"2025": 9.3, "2030": 11.5, "2040": 14.5, "2050": 17.0, "2100": 20.0}
                    }
                },
                {
                    "risk_type": "sea_level_rise",
                    "final_aal": 6.2,
                    "scenarios": {
                        "ssp1_2.6": {"2025": 6.2, "2030": 6.0, "2040": 5.8, "2050": 5.5, "2100": 5.2},
                        "ssp2_4.5": {"2025": 6.2, "2030": 6.5, "2040": 7.2, "2050": 8.0, "2100": 9.0},
                        "ssp3_7.0": {"2025": 6.2, "2030": 7.0, "2040": 8.5, "2050": 10.0, "2100": 12.0},
                        "ssp5_8.5": {"2025": 6.2, "2030": 7.8, "2040": 10.2, "2050": 13.0, "2100": 16.5}
                    }
                }
            ]
        }
    ]


def create_sample_report_template():
    """테스트용 Node 1 템플릿 생성"""
    return {
        "tone": {
            "formality": "formal",
            "audience": "institutional investors and stakeholders",
            "voice": "data-driven, professional, transparent"
        },
        "scenario_templates": {
            "SSP1-2.6": {"name": "지속가능 발전", "temp_rise": "1.5°C", "style": "낙관적"},
            "SSP2-4.5": {"name": "중간 경로", "temp_rise": "2.0-2.5°C", "style": "중립적"},
            "SSP5-8.5": {"name": "화석연료 집약", "temp_rise": "4.0°C+", "style": "경고적"}
        },
        "hazard_template_blocks": {
            "river_flood": {
                "kr_name": "하천 범람",
                "description_pattern": "[리스크명] 리스크는 [사업장]에 [영향]을 미칩니다."
            },
            "typhoon": {
                "kr_name": "태풍",
                "description_pattern": "강풍 및 폭우로 인한 [자산] 피해"
            }
        },
        "formatting_rules": {
            "headings": "숫자. 제목",
            "emphasis": "**굵은 글씨**"
        },
        "reusable_paragraphs": [
            "우리는 TCFD 권고안에 따라 기후변화 리스크를 체계적으로 평가했습니다.",
            "시나리오 분석을 통해 물리적 리스크의 재무적 영향을 정량화했습니다.",
            "단기/중기/장기 대응 전략을 수립하여 기후 회복력을 강화하고 있습니다."
        ]
    }


class MockLLM:
    """Mock LLM (테스트용)"""
    def __init__(self):
        self.call_count = 0

    async def ainvoke(self, prompt):
        self.call_count += 1
        print(f"\n{'='*60}")
        print(f"🤖 Mock LLM 호출 #{self.call_count}")
        print(f"{'='*60}")
        print(f"프롬프트 길이: {len(prompt):,} 글자")

        # 키워드 기반 응답 분기
        if "scenario" in prompt.lower() or "시나리오" in prompt:
            print("✅ 응답 타입: 시나리오 분석")
            return self._mock_scenario_response()
        elif "impact" in prompt.lower() or "영향" in prompt:
            print("✅ 응답 타입: 영향 분석")
            return self._mock_impact_response()
        elif "mitigation" in prompt.lower() or "대응" in prompt or "전략" in prompt:
            print("✅ 응답 타입: 대응 전략")
            return self._mock_mitigation_response()
        else:
            print("⚠️  응답 타입: 일반")
            return "Mock response"

    def _mock_scenario_response(self):
        return """
## Executive Summary
포트폴리오 전체의 기후 리스크는 4가지 SSP 시나리오에 따라 크게 달라집니다.
SSP1-2.6에서는 AAL이 감소하지만, SSP5-8.5에서는 크게 증가할 전망입니다.

## Scenario-by-Scenario Analysis

### SSP1-2.6 (지속가능 발전)
AAL은 2025년에서 2100년까지 점진적으로 감소합니다.

### SSP5-8.5 (화석연료 집약)
AAL은 2025년에서 2100년까지 급격히 증가합니다.

## Strategic Recommendations
단기적으로는 모든 시나리오 대비 기본 회복력 구축이 필요합니다.
"""

    def _mock_impact_response(self):
        return json.dumps({
            "financial_impact": "재무적 영향은 연간 30-50억원으로 추정됩니다.",
            "operational_impact": "주요 사업장의 운영 중단 위험이 있습니다.",
            "asset_impact": "물리적 자산 손상 위험이 있습니다.",
            "summary": "즉각적인 대응이 필요한 리스크입니다."
        }, ensure_ascii=False)

    def _mock_mitigation_response(self):
        return json.dumps({
            "short_term": [
                "비상 대응 매뉴얼 수립",
                "취약 지점 긴급 점검",
                "모니터링 시스템 구축"
            ],
            "mid_term": [
                "물리적 방어 시설 설치",
                "설비 보강 공사"
            ],
            "long_term": [
                "장기적 리스크 저감 계획",
                "사업장 재배치 검토"
            ],
            "priority": "높음",
            "priority_justification": "Top 리스크로 우선 대응이 필요합니다.",
            "estimated_cost": "총 100억원",
            "expected_benefit": "AAL 3%p 감소 예상",
            "implementation_considerations": "예산 확보 필요"
        }, ensure_ascii=False)


class RealLLM:
    """실제 OpenAI LLM"""
    def __init__(self):
        from openai import AsyncOpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY 환경변수를 설정해주세요")
        self.client = AsyncOpenAI(api_key=api_key)

    async def ainvoke(self, prompt):
        print(f"\n🚀 OpenAI API 호출 중...")
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an ELITE ESG/TCFD analyst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        result = response.choices[0].message.content
        print(f"✅ API 응답 완료 ({len(result)} 글자)")
        return result


async def main():
    """통합 테스트 실행"""
    print("\n" + "="*80)
    print("🧪 Node 2 통합 테스트 (2-A → 2-B → 2-C)")
    print("="*80)

    # 절대 import
    project_root = Path(__file__).parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from ai_agent.agents.tcfd_report.node_2a_scenario_analysis_v2 import ScenarioAnalysisNode
    from ai_agent.agents.tcfd_report.node_2b_impact_analysis_v2 import ImpactAnalysisNode
    from ai_agent.agents.tcfd_report.node_2c_mitigation_strategies_v2 import MitigationStrategiesNode

    # LLM 설정
    use_real = os.getenv("USE_REAL_LLM", "false").lower() == "true"

    if use_real:
        print("\n🚀 실제 OpenAI API 사용")
        try:
            llm = RealLLM()
        except Exception as e:
            print(f"❌ OpenAI 설정 실패: {e}")
            print("Mock LLM으로 전환합니다.")
            llm = MockLLM()
    else:
        print("\n🤖 Mock LLM 사용 (테스트용)")
        llm = MockLLM()

    # 노드 초기화
    node_2a = ScenarioAnalysisNode(llm_client=llm)
    node_2b = ImpactAnalysisNode(llm_client=llm)
    node_2c = MitigationStrategiesNode(llm_client=llm)

    # 샘플 데이터
    sites_data = create_sample_sites_data()
    report_template = create_sample_report_template()

    print("\n📄 입력 데이터:")
    print(f"  - 사업장 개수: {len(sites_data)}")
    print(f"  - 템플릿 필드: {len(report_template)}")

    # =================================================================
    # STEP 1: Node 2-A (Scenario Analysis)
    # =================================================================
    print("\n" + "="*80)
    print("STEP 1: Node 2-A (Scenario Analysis) 실행")
    print("="*80)

    result_2a = await node_2a.execute(
        sites_data=sites_data,
        report_template=report_template,
        agent_guideline=None
    )

    scenarios = result_2a["scenarios"]
    scenario_table = result_2a["scenario_table"]

    print(f"\n✅ Node 2-A 완료!")
    print(f"  - 시나리오 개수: {len(scenarios)}")
    print(f"  - TableBlock 생성: {scenario_table.get('type')}")

    # 시나리오 요약
    print(f"\n  시나리오 AAL 요약:")
    for key, data in scenarios.items():
        aal_start = data.get("aal_values", [0])[0]
        aal_end = data.get("aal_values", [0])[-1]
        print(f"    {key.upper()}: {aal_start}% → {aal_end}%")

    # =================================================================
    # STEP 2: Node 2-B (Impact Analysis)
    # =================================================================
    print("\n" + "="*80)
    print("STEP 2: Node 2-B (Impact Analysis) 실행")
    print("="*80)

    result_2b = await node_2b.execute(
        sites_data=sites_data,
        scenario_analysis=result_2a,
        report_template=report_template,
        sites_metadata=None
    )

    top_5_risks = result_2b["top_5_risks"]
    impact_analyses = result_2b["impact_analyses"]
    impact_blocks = result_2b["impact_blocks"]

    print(f"\n✅ Node 2-B 완료!")
    print(f"  - Top 5 리스크:")
    for risk in top_5_risks:
        print(f"    P{risk['rank']}. {risk['risk_type']}: AAL {risk['total_aal']}%")
    print(f"  - TextBlock 개수: {len(impact_blocks)}")

    # =================================================================
    # STEP 3: Node 2-C (Mitigation Strategies)
    # =================================================================
    print("\n" + "="*80)
    print("STEP 3: Node 2-C (Mitigation Strategies) 실행")
    print("="*80)

    result_2c = await node_2c.execute(
        impact_analyses=impact_analyses,
        report_template=report_template,
        company_context=None
    )

    mitigation_strategies = result_2c["mitigation_strategies"]
    mitigation_blocks = result_2c["mitigation_blocks"]
    implementation_roadmap = result_2c["implementation_roadmap"]

    print(f"\n✅ Node 2-C 완료!")
    print(f"  - 대응 전략 개수: {len(mitigation_strategies)}")
    print(f"  - TextBlock 개수: {len(mitigation_blocks)}")

    # 우선순위 요약
    priority_summary = {"매우 높음": 0, "높음": 0, "중간": 0}
    for strategy in mitigation_strategies:
        priority = strategy.get("priority", "중간")
        if priority in priority_summary:
            priority_summary[priority] += 1

    print(f"\n  우선순위 분포:")
    for priority, count in priority_summary.items():
        print(f"    {priority}: {count}개")

    # =================================================================
    # 통합 결과 정리
    # =================================================================
    print("\n" + "="*80)
    print("📊 통합 결과 요약")
    print("="*80)

    integrated_result = {
        "node_2a": {
            "scenarios": scenarios,
            "scenario_table": scenario_table,
            "scenario_text_block": result_2a["scenario_text_block"],
            "comparison_analysis": result_2a["comparison_analysis"]
        },
        "node_2b": {
            "top_5_risks": top_5_risks,
            "impact_analyses": impact_analyses,
            "impact_blocks": impact_blocks
        },
        "node_2c": {
            "mitigation_strategies": mitigation_strategies,
            "mitigation_blocks": mitigation_blocks,
            "implementation_roadmap": implementation_roadmap
        }
    }

    # 전체 통계
    print(f"\n전체 생성된 JSON 블록:")
    print(f"  - TableBlock: 1개 (Node 2-A)")
    print(f"  - TextBlock: {len(impact_blocks) + len(mitigation_blocks) + 1}개")
    print(f"    * Node 2-A: 1개 (시나리오 분석)")
    print(f"    * Node 2-B: {len(impact_blocks)}개 (P1~P5 영향 분석)")
    print(f"    * Node 2-C: {len(mitigation_blocks)}개 (P1~P5 대응 전략)")

    print(f"\n주요 산출물:")
    print(f"  - 4가지 SSP 시나리오 분석")
    print(f"  - Top 5 물리적 리스크 식별")
    print(f"  - 5개 리스크별 영향 분석 (재무/운영/자산)")
    print(f"  - 5개 리스크별 대응 전략 (단기/중기/장기)")
    print(f"  - 전체 실행 로드맵")

    # 결과 저장
    output_dir = Path(__file__).parent / "test_output"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"node2_integrated_{timestamp}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(integrated_result, f, ensure_ascii=False, indent=2)

    print(f"\n💾 통합 결과 저장: {output_file}")

    # LLM 호출 횟수 (Mock LLM인 경우)
    if isinstance(llm, MockLLM):
        print(f"\n📊 Mock LLM 호출 통계:")
        print(f"  - 총 호출 횟수: {llm.call_count}회")
        print(f"  - Node 2-A: 1회 (시나리오 분석)")
        print(f"  - Node 2-B: {len(top_5_risks)}회 (Top 5 병렬 분석)")
        print(f"  - Node 2-C: {len(mitigation_strategies)}회 (대응 전략 병렬 생성)")

    print("\n" + "="*80)
    print("✅ Node 2 통합 테스트 완료!")
    print("="*80)

    if not use_real:
        print("\n💡 실제 OpenAI API로 테스트하려면:")
        print("   1. set OPENAI_API_KEY=your_key")
        print("   2. set USE_REAL_LLM=true")
        print("   3. python -m ai_agent.agents.tcfd_report.test_node2_integrated")


if __name__ == "__main__":
    asyncio.run(main())
