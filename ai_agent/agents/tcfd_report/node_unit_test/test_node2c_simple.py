"""
Node 2-C Mitigation Strategies v2 간단 테스트

실행 방법:
    cd c:/Users/SKAX/Documents/POLARIS/polaris_backend_fastapi-develop
    python -m ai_agent.agents.tcfd_report.test_node2c_simple

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


def create_sample_impact_analyses():
    """테스트용 Node 2-B 영향 분석 결과 생성"""
    return [
        {
            "risk_type": "river_flood",
            "rank": 1,
            "total_aal": 18.2,
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
""",
            "operational_impact": """
하천 범람 리스크는 **3개 주요 사업장**의 운영에 영향을 미칩니다.

**운영 중단 위험:**
- 서울 본사: 1-3일 (침수 깊이 0.5-1m)
- 판교 데이터센터: 3-7일 (전력 공급 중단)
- 인천 물류센터: 5-10일 (도로 접근 불가)
""",
            "asset_impact": """
물리적 자산에 대한 영향은 다음과 같습니다.

**건물 및 시설:**
- 지하 1-2층 침수 위험 (전기실, 기계실)
- 외벽 및 방수 시설 손상
- 냉난방 시스템 고장
""",
            "summary": "하천 범람은 Top 1 리스크로 즉각적인 대응이 필요합니다."
        },
        {
            "risk_type": "typhoon",
            "rank": 2,
            "total_aal": 11.4,
            "financial_impact": "태풍으로 인한 연간 재무 손실은 30-50억원으로 추정됩니다.",
            "operational_impact": "부산 및 제주 사업장의 운영 중단 위험이 있습니다.",
            "asset_impact": "건물 외벽 및 지붕 손상 위험이 있습니다.",
            "summary": "태풍은 Top 2 리스크로 계절별 대응이 필요합니다."
        },
        {
            "risk_type": "urban_flood",
            "rank": 3,
            "total_aal": 8.7,
            "financial_impact": "도시 침수로 인한 손실은 20-30억원으로 추정됩니다.",
            "operational_impact": "도심 지역 사업장의 접근성 문제가 발생합니다.",
            "asset_impact": "지하 주차장 및 전산실 침수 위험이 있습니다.",
            "summary": "도시 침수는 배수 시스템 개선이 필요합니다."
        },
        {
            "risk_type": "extreme_heat",
            "rank": 4,
            "total_aal": 7.3,
            "financial_impact": "극심한 고온으로 인한 냉방 비용 증가는 연 10-15억원입니다.",
            "operational_impact": "데이터센터 냉각 시스템 부하 증가로 가동률 저하 위험이 있습니다.",
            "asset_impact": "냉각 설비 수명 단축 및 교체 비용 증가가 예상됩니다.",
            "summary": "극심한 고온은 냉각 시스템 업그레이드가 필요합니다."
        },
        {
            "risk_type": "sea_level_rise",
            "rank": 5,
            "total_aal": 6.2,
            "financial_impact": "해수면 상승으로 인한 장기 손실은 연 5-10억원입니다.",
            "operational_impact": "해안 사업장의 장기적 운영 리스크가 있습니다.",
            "asset_impact": "해안 인프라 침식 및 방조제 보강이 필요합니다.",
            "summary": "해수면 상승은 장기적 대응 전략이 필요합니다."
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
        "reusable_paragraphs": [
            "우리는 TCFD 권고안에 따라 기후변화 리스크를 체계적으로 평가했습니다.",
            "단기/중기/장기 대응 전략을 수립하여 기후 회복력을 강화하고 있습니다.",
            "비용 효율적인 리스크 저감 방안을 우선 순위에 따라 실행할 계획입니다."
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
        if "mitigation" in prompt.lower() or "대응" in prompt or "전략" in prompt:
            print("✅ 모드: 대응 전략 생성")

        print(f"{'='*60}\n")

        # Mock JSON 응답
        return json.dumps({
            "short_term": [
                "[2026년] 침수 취약 지역 배수 펌프 5대 설치 (용량: 100㎥/h)",
                "[2026년] 비상 대응 매뉴얼 수립 및 분기별 훈련 실시",
                "[2026년] 취약 지점 긴급 점검 및 임시 방수벽 설치 (높이: 0.5m)",
                "[2026년] 실시간 기상 모니터링 시스템 구축 (AWS 연동)",
                "[2026년] 침수 위험 지역 중요 자산 이전 (1층 → 2층 이상)"
            ],
            "mid_term": [
                "[2026-2027년] 데이터센터 방수벽 2m 높이로 증축 (총 연장 500m)",
                "[2027-2028년] 지하 전기실 방수 공사 및 침수 감지 센서 설치",
                "[2028-2029년] 배수 시스템 용량 2배 확대 (200㎥/h → 400㎥/h)",
                "[2029-2030년] 비상 전력 공급 장치(UPS) 고층 이전 공사"
            ],
            "long_term": [
                "[2020-2030년대] 침수 위험 높은 사업장 재배치 타당성 검토",
                "[2030-2040년대] 기후 회복력 설계 기준 적용한 신규 사업장 개발",
                "[2040-2050년대] 포트폴리오 다변화를 통한 지역 리스크 분산"
            ],
            "priority": "매우 높음",
            "priority_justification": "Top 1 리스크로 AAL 18.2%에 해당하며, 연간 50-80억원의 재무적 손실이 예상되어 즉각적인 대응이 필요합니다. 3개 주요 사업장의 운영 중단 위험이 있어 사업 연속성 측면에서도 최우선 순위입니다.",
            "estimated_cost": "단기: 15억원, 중기: 80억원, 장기: 200억원, 총: 295억원",
            "expected_benefit": "AAL 5-7%p 감소 예상 (18.2% → 11-13%), 자산 보호 효과 연 30-50억원, ROI 3-5년",
            "implementation_considerations": "- 단기 조치는 2025년 상반기 내 완료 목표\n- 중기 조치는 예산 확보 후 2026년 착수\n- 장기 조치는 타당성 검토 후 이사회 승인 필요"
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
                {"role": "system", "content": "You are an ELITE climate adaptation strategist."},
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
    print("🧪 Node 2-C: Mitigation Strategies v2 테스트")
    print("="*80)

    # 절대 import로 변경
    project_root = Path(__file__).parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

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

    # Node 2-C 초기화
    node = MitigationStrategiesNode(llm_client=llm)

    # 샘플 데이터
    impact_analyses = create_sample_impact_analyses()
    report_template = create_sample_report_template()

    print("\n📄 입력 데이터:")
    print(f"  - 영향 분석 개수: {len(impact_analyses)}")
    print(f"  - Top 5 리스크:")
    for impact in impact_analyses:
        print(f"    P{impact['rank']}. {impact['risk_type']}: AAL {impact['total_aal']}%")

    # Node 2-C 실행
    print("\n" + "="*80)
    print("▶ Node 2-C 실행")
    print("="*80)

    result = await node.execute(
        impact_analyses=impact_analyses,
        report_template=report_template,
        company_context=None
    )

    # 결과 확인
    mitigation_strategies = result["mitigation_strategies"]
    mitigation_blocks = result["mitigation_blocks"]
    implementation_roadmap = result["implementation_roadmap"]

    print("\n✅ 실행 완료!")
    print(f"\n📊 결과 요약:")
    print(f"  - 대응 전략 개수: {len(mitigation_strategies)}")
    print(f"  - TextBlock 개수: {len(mitigation_blocks)}")
    print(f"  - 우선순위 액션 개수: {len(implementation_roadmap.get('priority_actions', []))}")

    # 대응 전략 미리보기
    print(f"\n🔍 대응 전략 미리보기 (P1 - 하천 범람):")
    if mitigation_strategies:
        first_strategy = mitigation_strategies[0]
        print(f"  리스크: {first_strategy['risk_type']}")
        print(f"  우선순위: {first_strategy.get('priority', 'N/A')}")
        print(f"  예상 비용: {first_strategy.get('estimated_cost', 'N/A')}")
        print(f"  예상 효과: {first_strategy.get('expected_benefit', 'N/A')}")

        print(f"\n  단기 조치 ({len(first_strategy.get('short_term', []))}개):")
        for i, action in enumerate(first_strategy.get('short_term', [])[:3], 1):
            print(f"    {i}. {action}")

        print(f"\n  중기 조치 ({len(first_strategy.get('mid_term', []))}개):")
        for i, action in enumerate(first_strategy.get('mid_term', [])[:2], 1):
            print(f"    {i}. {action}")

        print(f"\n  장기 조치 ({len(first_strategy.get('long_term', []))}개):")
        for i, action in enumerate(first_strategy.get('long_term', [])[:2], 1):
            print(f"    {i}. {action}")

    # 전체 전략 우선순위 요약
    print(f"\n📋 전체 전략 우선순위:")
    priority_counts = {"매우 높음": 0, "높음": 0, "중간": 0}
    for strategy in mitigation_strategies:
        priority = strategy.get("priority", "중간")
        if priority in priority_counts:
            priority_counts[priority] += 1

    for priority, count in priority_counts.items():
        print(f"  {priority}: {count}개")

    # TextBlock 미리보기
    print(f"\n📝 TextBlock 미리보기 (P1):")
    if mitigation_blocks:
        first_block = mitigation_blocks[0]
        print(f"  타입: {first_block['type']}")
        print(f"  소제목: {first_block['subheading']}")
        content = first_block['content']
        print(f"  내용 길이: {len(content)} 글자")
        print(f"  내용 미리보기:\n{content[:400]}...")

    # 실행 로드맵
    print(f"\n🗓️  실행 로드맵:")
    timeline = implementation_roadmap.get("timeline", {})
    print(f"  단기 (향후 1년): {timeline.get('short_term', 'N/A')}")
    print(f"  중기 (향후 5년): {timeline.get('mid_term', 'N/A')}")
    print(f"  장기 (2050년까지 10년 단위): {timeline.get('long_term', 'N/A')}")
    print(f"  총 예상 비용: {implementation_roadmap.get('total_cost', 'N/A')}")

    print(f"\n  우선순위 액션 (상위 3개):")
    for i, action in enumerate(implementation_roadmap.get('priority_actions', [])[:3], 1):
        print(f"    {i}. {action}")

    # 결과 저장
    output_dir = Path(__file__).parent / "test_output"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"node2c_result_{timestamp}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n💾 결과 저장: {output_file}")

    print("\n" + "="*80)
    print("✅ Node 2-C 테스트 완료!")
    print("="*80)

    if not use_real:
        print("\n💡 실제 OpenAI API로 테스트하려면:")
        print("   1. set OPENAI_API_KEY=your_key")
        print("   2. set USE_REAL_LLM=true")
        print("   3. python -m ai_agent.agents.tcfd_report.test_node2c_simple")


if __name__ == "__main__":
    asyncio.run(main())
