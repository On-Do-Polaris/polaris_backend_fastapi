"""
Node 2-A Template Loading v2 간단 테스트

실행 방법:
    cd c:/Users/SKAX/Documents/POLARIS/polaris_backend_fastapi-develop
    python -m ai_agent.agents.tcfd_report.test_node2a_simple

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
    """테스트용 샘플 사업장 데이터 생성"""
    return [
        {
            "site_id": "site_001",
            "site_name": "서울 본사",
            "risk_results": [
                {
                    "risk_type": "river_flood",
                    "final_aal": 7.2,
                    "scenarios": {
                        "ssp1_2.6": {"2024": 7.2, "2030": 7.0, "2040": 6.5, "2050": 6.0, "2100": 5.5},
                        "ssp2_4.5": {"2024": 7.2, "2030": 7.5, "2040": 8.2, "2050": 9.0, "2100": 10.1},
                        "ssp3_7.0": {"2024": 7.2, "2030": 8.0, "2040": 9.5, "2050": 11.0, "2100": 12.5},
                        "ssp5_8.5": {"2024": 7.2, "2030": 8.5, "2040": 10.5, "2050": 13.0, "2100": 15.2}
                    }
                },
                {
                    "risk_type": "typhoon",
                    "final_aal": 2.1,
                    "scenarios": {
                        "ssp1_2.6": {"2024": 2.1, "2030": 2.0, "2040": 1.9, "2050": 1.8, "2100": 1.7},
                        "ssp2_4.5": {"2024": 2.1, "2030": 2.2, "2040": 2.5, "2050": 2.8, "2100": 3.1},
                        "ssp3_7.0": {"2024": 2.1, "2030": 2.5, "2040": 3.0, "2050": 3.5, "2100": 4.0},
                        "ssp5_8.5": {"2024": 2.1, "2030": 2.8, "2040": 3.5, "2050": 4.2, "2100": 5.0}
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
                        "ssp1_2.6": {"2024": 11.0, "2030": 10.5, "2040": 10.0, "2050": 9.5, "2100": 9.0},
                        "ssp2_4.5": {"2024": 11.0, "2030": 11.5, "2040": 12.5, "2050": 13.5, "2100": 14.8},
                        "ssp3_7.0": {"2024": 11.0, "2030": 12.0, "2040": 14.0, "2050": 16.0, "2100": 18.0},
                        "ssp5_8.5": {"2024": 11.0, "2030": 13.0, "2040": 16.0, "2050": 19.0, "2100": 22.5}
                    }
                },
                {
                    "risk_type": "extreme_heat",
                    "final_aal": 5.5,
                    "scenarios": {
                        "ssp1_2.6": {"2024": 5.5, "2030": 5.3, "2040": 5.0, "2050": 4.8, "2100": 4.5},
                        "ssp2_4.5": {"2024": 5.5, "2030": 6.0, "2040": 7.0, "2050": 8.0, "2100": 9.2},
                        "ssp3_7.0": {"2024": 5.5, "2030": 6.5, "2040": 8.0, "2050": 10.0, "2100": 12.0},
                        "ssp5_8.5": {"2024": 5.5, "2030": 7.0, "2040": 9.5, "2050": 12.0, "2100": 15.0}
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
        "formatting_rules": {
            "headings": "숫자. 제목 (예: 1. Governance)",
            "subheadings": "1.1, 1.2 형식",
            "emphasis": "**굵은 글씨** 또는 밑줄"
        },
        "reusable_paragraphs": [
            "우리는 TCFD 권고안에 따라 기후변화 리스크를 체계적으로 평가했습니다.",
            "시나리오 분석을 통해 물리적 리스크의 재무적 영향을 정량화했습니다.",
            "포트폴리오 AAL은 [수치]%로 산정되었으며, 이는 [해석]을 의미합니다."
        ]
    }


class MockLLM:
    """Mock LLM (테스트용)"""
    async def ainvoke(self, prompt):
        print(f"\n{'='*60}")
        print("🤖 Mock LLM 호출")
        print(f"{'='*60}")
        print(f"프롬프트 길이: {len(prompt):,} 글자")

        # 키워드 확인
        if "scenario" in prompt.lower() or "시나리오" in prompt:
            print("✅ 모드: 시나리오 분석")

        print(f"{'='*60}\n")

        # Mock 응답
        return """
## Executive Summary

포트폴리오 전체의 기후 리스크는 4가지 SSP 시나리오에 따라 크게 달라집니다.
SSP1-2.6 시나리오에서는 AAL이 2100년까지 45.0%로 감소하는 반면,
SSP5-8.5 시나리오에서는 92.5%까지 증가할 것으로 예상됩니다.

## Scenario-by-Scenario Analysis

### SSP1-2.6 (지속가능 발전)
AAL은 2024년 52.9%에서 2100년 45.0%로 **14.9% 감소**합니다.
친환경 정책과 국제 협력으로 온실가스 감축이 성공하는 시나리오입니다.

### SSP2-4.5 (중간 경로)
AAL은 2024년 52.9%에서 2100년 68.1%로 **28.7% 증가**합니다.
현재 추세가 유지되며 점진적인 기후 대응이 이루어지는 시나리오입니다.

### SSP3-7.0 (지역 경쟁)
AAL은 2024년 52.9%에서 2100년 78.5%로 **48.4% 증가**합니다.
국가 간 경쟁이 심화되고 기후 대응이 미흡한 시나리오입니다.

### SSP5-8.5 (화석연료 집약)
AAL은 2024년 52.9%에서 2100년 92.5%로 **74.9% 증가**합니다.
화석연료 의존이 지속되는 최악의 기후변화 시나리오입니다.

## Comparative Analysis

**시나리오 간 AAL 차이:**
- 최선 시나리오(SSP1-2.6): 45.0%
- 최악 시나리오(SSP5-8.5): 92.5%
- **차이: 47.5%p** (2배 이상)

**주요 인사이트:**
- 2030년까지는 모든 시나리오에서 AAL 차이가 크지 않음
- 2050년 이후 시나리오 간 격차가 급격히 벌어짐
- SSP5-8.5 시나리오에서는 2100년 AAL이 90%를 초과

## Strategic Recommendations

**Top 3 우선순위:**
1. 단기(2025-2030): 모든 시나리오 대비 기본 회복력 구축
2. 중기(2030-2050): 시나리오 모니터링 및 적응 전략 조정
3. 장기(2050+): 최악 시나리오 대비 변혁적 대응 준비

**투자 로드맵:**
- 단기: 10-20억원 (모니터링, 긴급 대응)
- 중기: 50-100억원 (인프라 강화)
- 장기: 200-500억원 (사업장 재배치 검토)

## Stakeholder Messaging

"우리 포트폴리오는 다양한 기후 시나리오에 대한 회복력을 갖추고 있습니다.
최악의 시나리오에서도 체계적인 대응 전략을 수립하여 리스크를 관리하고 있습니다."
"""


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
                {"role": "system", "content": "You are an ESG report analyst specializing in TCFD disclosures."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )
        result = response.choices[0].message.content
        print(f"✅ API 응답 완료 ({len(result)} 글자)")
        return result


async def main():
    """테스트 실행"""
    print("\n" + "="*80)
    print("🧪 Node 2-A: Scenario Analysis v2 테스트")
    print("="*80)

    # 절대 import로 변경 (프로젝트 루트를 sys.path에 추가)
    project_root = Path(__file__).parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from ai_agent.agents.tcfd_report.node_2a_scenario_analysis_v2 import ScenarioAnalysisNode

    # LLM 클라이언트 설정
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

    # Node 2-A 초기화
    node = ScenarioAnalysisNode(llm_client=llm)

    # 샘플 데이터
    sites_data = create_sample_sites_data()
    report_template = create_sample_report_template()

    print("\n📄 입력 데이터:")
    print(f"  - 사업장 개수: {len(sites_data)}")
    print(f"  - 템플릿 필드 개수: {len(report_template)}")

    # Node 2-A 실행
    print("\n" + "="*80)
    print("▶ Node 2-A 실행")
    print("="*80)

    result = await node.execute(
        sites_data=sites_data,
        report_template=report_template,
        agent_guideline=None
    )

    # 결과 확인
    scenarios = result["scenarios"]
    scenario_table = result["scenario_table"]
    scenario_text_block = result["scenario_text_block"]
    comparison_analysis = result["comparison_analysis"]

    print("\n✅ 실행 완료!")
    print(f"\n📊 결과 요약:")
    print(f"  - 시나리오 개수: {len(scenarios)}")
    print(f"  - TableBlock 타입: {scenario_table.get('type')}")
    print(f"  - TextBlock 타입: {scenario_text_block.get('type')}")
    print(f"  - 비교 분석 길이: {len(comparison_analysis)} 글자")

    # 시나리오별 AAL 출력
    print(f"\n🔍 시나리오별 AAL:")
    for scenario_key, data in scenarios.items():
        aal_start = data.get("aal_values", [0])[0]
        aal_end = data.get("aal_values", [0])[-1]
        change_rate = data.get("change_rate", 0)
        name_kr = data.get("scenario_name_kr", "")

        print(f"  {scenario_key.upper()} ({name_kr}):")
        print(f"    2024: {aal_start}% → 2100: {aal_end}% ({change_rate:+.1f}%)")

    # TableBlock 미리보기
    print(f"\n📋 TableBlock 미리보기:")
    table_data = scenario_table.get("data", {})
    print(f"  제목: {scenario_table.get('title')}")
    print(f"  헤더: {table_data.get('headers')}")
    print(f"  행 개수: {len(table_data.get('rows', []))}")

    # TextBlock 미리보기
    print(f"\n📝 TextBlock 미리보기:")
    print(f"  소제목: {scenario_text_block.get('subheading')}")
    content = scenario_text_block.get('content', '')
    print(f"  내용 길이: {len(content)} 글자")
    print(f"  내용 미리보기: {content[:200]}...")

    # 비교 분석 미리보기
    print(f"\n📊 비교 분석 미리보기:")
    print(f"{comparison_analysis[:500]}...")

    # 결과 저장
    output_dir = Path(__file__).parent / "test_output"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"node2a_result_{timestamp}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n💾 결과 저장: {output_file}")

    print("\n" + "="*80)
    print("✅ Node 2-A 테스트 완료!")
    print("="*80)

    # 실제 LLM 사용 안내
    if not use_real:
        print("\n💡 실제 OpenAI API로 테스트하려면:")
        print("   1. set OPENAI_API_KEY=your_key")
        print("   2. set USE_REAL_LLM=true")
        print("   3. python -m ai_agent.agents.tcfd_report.test_node2a_simple")


if __name__ == "__main__":
    asyncio.run(main())
