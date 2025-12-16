"""
Node 2-B Impact Analysis v2 간단 테스트

실행 방법:
    cd c:/Users/SKAX/Documents/POLARIS/polaris_backend_fastapi-develop
    python -m ai_agent.agents.tcfd_report.test_node2b_simple

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
                {"risk_type": "river_flood", "final_aal": 7.2},
                {"risk_type": "typhoon", "final_aal": 2.1},
                {"risk_type": "urban_flood", "final_aal": 5.1},
                {"risk_type": "extreme_heat", "final_aal": 2.5}
            ]
        },
        {
            "site_id": "site_002",
            "site_name": "판교 데이터센터",
            "risk_results": [
                {"risk_type": "river_flood", "final_aal": 11.0},
                {"risk_type": "extreme_heat", "final_aal": 5.5},
                {"risk_type": "urban_flood", "final_aal": 3.6}
            ]
        },
        {
            "site_id": "site_003",
            "site_name": "부산 사업장",
            "risk_results": [
                {"risk_type": "typhoon", "final_aal": 9.3},
                {"risk_type": "sea_level_rise", "final_aal": 6.2},
                {"risk_type": "river_flood", "final_aal": 0.0}
            ]
        }
    ]


def create_sample_scenario_analysis():
    """테스트용 Node 2-A 시나리오 분석 결과 생성"""
    return {
        "scenarios": {
            "ssp1_2.6": {
                "timeline": [2024, 2030, 2040, 2050, 2100],
                "aal_values": [52.9, 51.2, 49.5, 47.3, 45.0],
                "change_rate": -14.9
            },
            "ssp2_4.5": {
                "timeline": [2024, 2030, 2040, 2050, 2100],
                "aal_values": [52.9, 55.3, 59.8, 63.5, 68.1],
                "change_rate": 28.7
            },
            "ssp3_7.0": {
                "timeline": [2024, 2030, 2040, 2050, 2100],
                "aal_values": [52.9, 58.0, 66.5, 72.0, 78.5],
                "change_rate": 48.4
            },
            "ssp5_8.5": {
                "timeline": [2024, 2030, 2040, 2050, 2100],
                "aal_values": [52.9, 61.5, 74.2, 83.0, 92.5],
                "change_rate": 74.9
            }
        }
    }


def create_sample_report_template():
    """테스트용 Node 1 템플릿 생성"""
    return {
        "tone": {
            "formality": "formal",
            "audience": "institutional investors and stakeholders",
            "voice": "data-driven, professional, transparent"
        },
        "hazard_template_blocks": {
            "river_flood": {
                "kr_name": "하천 범람",
                "description_pattern": "[리스크명] 리스크는 [사업장]에 [영향]을 미칩니다.",
                "metrics": ["AAL", "침수 깊이", "영향 범위"],
                "impact_framing": "재무적 영향: [금액], 운영 중단: [일수]"
            },
            "typhoon": {
                "kr_name": "태풍",
                "description_pattern": "강풍 및 폭우로 인한 [자산] 피해",
                "metrics": ["풍속", "강수량", "피해액"],
                "impact_framing": "건물 외벽 손상 및 설비 파손 우려"
            }
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
        if "impact" in prompt.lower() or "영향" in prompt:
            print("✅ 모드: 영향 분석")

        print(f"{'='*60}\n")

        # Mock JSON 응답
        return json.dumps({
            "financial_impact": """
하천 범람 리스크로 인한 재무적 영향은 연간 **50-80억원** 규모로 추정됩니다.

**주요 재무 영향:**
- 직접 자산 손실: 30-50억원 (침수 피해)
- 운영 중단 손실: 20-30억원 (매출 감소)
- 보험 공제액: 5-10억원

**재무 지표 영향:**
- EBITDA 감소: 2-3%
- 순이익 영향: 5-8억원 (연간)
- 자산 가치 하락: 1-2%

이는 포트폴리오 AAL 18.2%에 기반한 추정치로, 최악의 시나리오에서는 손실이 2배 이상 증가할 수 있습니다.
""",
            "operational_impact": """
하천 범람 리스크는 **3개 주요 사업장**의 운영에 영향을 미칩니다.

**운영 중단 위험:**
- 서울 본사: 1-3일 (침수 깊이 0.5-1m)
- 판교 데이터센터: 3-7일 (전력 공급 중단)
- 인천 물류센터: 5-10일 (도로 접근 불가)

**공급망 영향:**
- 데이터 서비스 중단 시 고객사 영향
- 물류 지연으로 인한 계약 위반 리스크
- 백업 시스템 전환 비용 증가

**인력 영향:**
- 직원 출퇴근 어려움
- 재택근무 전환 필요
- 비상 대응 인력 동원
""",
            "asset_impact": """
물리적 자산에 대한 영향은 다음과 같습니다.

**건물 및 시설:**
- 지하 1-2층 침수 위험 (전기실, 기계실)
- 외벽 및 방수 시설 손상
- 냉난방 시스템 고장

**IT 인프라:**
- 서버실 침수 위험 (판교 DC)
- 네트워크 장비 손상
- 데이터 백업 시스템 위험

**장기적 자산 영향:**
- 건물 내구성 저하 (5-10년)
- 설비 수명 단축 (20-30%)
- 유지보수 비용 증가 (연 10-20%)
""",
            "summary": """
하천 범람은 Top 1 리스크로 식별되었으며, AAL 18.2%로 **즉각적인 대응이 필요**합니다.
연간 50-80억원의 재무적 손실이 예상되며, 3개 사업장의 운영 중단 위험이 있습니다.
단기적으로 방수 시설 보강 및 비상 대응 체계 구축이 시급합니다.
"""
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
                {"role": "system", "content": "You are an ELITE climate risk impact analyst."},
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
    print("🧪 Node 2-B: Impact Analysis v2 테스트")
    print("="*80)

    # 절대 import로 변경
    project_root = Path(__file__).parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from ai_agent.agents.tcfd_report.node_2b_impact_analysis_v2 import ImpactAnalysisNode

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

    # Node 2-B 초기화
    node = ImpactAnalysisNode(llm_client=llm)

    # 샘플 데이터
    sites_data = create_sample_sites_data()
    scenario_analysis = create_sample_scenario_analysis()
    report_template = create_sample_report_template()

    print("\n📄 입력 데이터:")
    print(f"  - 사업장 개수: {len(sites_data)}")
    print(f"  - 시나리오 개수: {len(scenario_analysis['scenarios'])}")

    # Node 2-B 실행
    print("\n" + "="*80)
    print("▶ Node 2-B 실행")
    print("="*80)

    result = await node.execute(
        sites_data=sites_data,
        scenario_analysis=scenario_analysis,
        report_template=report_template,
        sites_metadata=None
    )

    # 결과 확인
    top_5_risks = result["top_5_risks"]
    impact_analyses = result["impact_analyses"]
    impact_blocks = result["impact_blocks"]

    print("\n✅ 실행 완료!")
    print(f"\n📊 결과 요약:")
    print(f"  - Top 5 리스크 개수: {len(top_5_risks)}")
    print(f"  - 영향 분석 개수: {len(impact_analyses)}")
    print(f"  - TextBlock 개수: {len(impact_blocks)}")

    # Top 5 리스크 출력
    print(f"\n🔍 Top 5 리스크:")
    for risk in top_5_risks:
        print(f"  P{risk['rank']}. {risk['risk_type']}: AAL {risk['total_aal']}%")

    # 영향 분석 미리보기
    print(f"\n📋 영향 분석 미리보기 (P1):")
    if impact_analyses:
        first_impact = impact_analyses[0]
        print(f"  리스크: {first_impact['risk_type']}")
        print(f"  재무적 영향: {first_impact['financial_impact'][:100]}...")
        print(f"  운영적 영향: {first_impact['operational_impact'][:100]}...")
        print(f"  자산 영향: {first_impact['asset_impact'][:100]}...")

    # TextBlock 미리보기
    print(f"\n📝 TextBlock 미리보기 (P1):")
    if impact_blocks:
        first_block = impact_blocks[0]
        print(f"  타입: {first_block['type']}")
        print(f"  소제목: {first_block['subheading']}")
        content = first_block['content']
        print(f"  내용 길이: {len(content)} 글자")
        print(f"  내용 미리보기: {content[:200]}...")

    # 결과 저장
    output_dir = Path(__file__).parent / "test_output"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"node2b_result_{timestamp}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n💾 결과 저장: {output_file}")

    print("\n" + "="*80)
    print("✅ Node 2-B 테스트 완료!")
    print("="*80)

    if not use_real:
        print("\n💡 실제 OpenAI API로 테스트하려면:")
        print("   1. set OPENAI_API_KEY=your_key")
        print("   2. set USE_REAL_LLM=true")
        print("   3. python -m ai_agent.agents.tcfd_report.test_node2b_simple")


if __name__ == "__main__":
    asyncio.run(main())
