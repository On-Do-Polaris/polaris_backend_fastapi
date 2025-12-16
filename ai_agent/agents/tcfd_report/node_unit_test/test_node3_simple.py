"""
Node 3 Strategy Section v2 간단 테스트

실행 방법:
    cd c:/Users/SKAX/Documents/POLARIS/polaris_backend_fastapi-develop
    python -m ai_agent.agents.tcfd_report.test_node3_simple

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


def create_sample_scenario_analysis():
    """테스트용 Node 2-A 시나리오 분석 결과 생성"""
    return {
        "scenarios": {
            "ssp1_2.6": {
                "scenario_name_kr": "저탄소 시나리오 (SSP1-2.6)",
                "aal_values": [52.9, 51.2, 49.5, 48.1, 45.0],
                "change_rate": -14.9,
                "key_points": ["AAL 감소 추세", "2100년까지 45.0%"]
            },
            "ssp2_4.5": {
                "scenario_name_kr": "중간 시나리오 (SSP2-4.5)",
                "aal_values": [52.9, 55.3, 58.7, 63.5, 68.1],
                "change_rate": 28.7,
                "key_points": ["완만한 증가", "2100년까지 68.1%"]
            },
            "ssp3_7.0": {
                "scenario_name_kr": "높은 배출 시나리오 (SSP3-7.0)",
                "aal_values": [52.9, 57.1, 65.2, 73.8, 85.3],
                "change_rate": 61.2,
                "key_points": ["급격한 증가", "2100년까지 85.3%"]
            },
            "ssp5_8.5": {
                "scenario_name_kr": "최악 시나리오 (SSP5-8.5)",
                "aal_values": [52.9, 58.7, 67.3, 78.2, 92.5],
                "change_rate": 74.9,
                "key_points": ["최대 증가", "2100년까지 92.5%"]
            }
        }
    }


def create_sample_impact_analyses():
    """테스트용 Node 2-B 영향 분석 결과 생성"""
    return [
        {
            "risk_type": "river_flood",
            "rank": 1,
            "total_aal": 18.2,
            "num_affected_sites": 3,
            "financial_impact": "하천 범람으로 인한 연간 재무 손실은 50-80억원으로 추정됩니다.",
            "operational_impact": "3개 주요 사업장의 운영 중단 위험이 있습니다.",
            "asset_impact": "지하 전기실 및 기계실 침수 위험이 높습니다.",
            "summary": "Top 1 리스크로 즉각적인 대응이 필요합니다."
        },
        {
            "risk_type": "typhoon",
            "rank": 2,
            "total_aal": 11.4,
            "num_affected_sites": 2,
            "financial_impact": "태풍으로 인한 연간 손실은 30-50억원입니다.",
            "operational_impact": "부산 및 제주 사업장 운영 중단 위험이 있습니다.",
            "asset_impact": "건물 외벽 및 지붕 손상 위험이 있습니다.",
            "summary": "계절별 대응이 필요합니다."
        },
        {
            "risk_type": "urban_flood",
            "rank": 3,
            "total_aal": 8.7,
            "num_affected_sites": 4,
            "financial_impact": "도시 침수로 인한 손실은 20-30억원입니다.",
            "operational_impact": "도심 지역 사업장 접근성 문제가 발생합니다.",
            "asset_impact": "지하 주차장 침수 위험이 있습니다.",
            "summary": "배수 시스템 개선이 필요합니다."
        },
        {
            "risk_type": "extreme_heat",
            "rank": 4,
            "total_aal": 7.3,
            "num_affected_sites": 5,
            "financial_impact": "냉방 비용 증가로 연 10-15억원 손실이 예상됩니다.",
            "operational_impact": "데이터센터 냉각 부하 증가로 가동률 저하 위험이 있습니다.",
            "asset_impact": "냉각 설비 수명 단축이 예상됩니다.",
            "summary": "냉각 시스템 업그레이드가 필요합니다."
        },
        {
            "risk_type": "sea_level_rise",
            "rank": 5,
            "total_aal": 6.2,
            "num_affected_sites": 2,
            "financial_impact": "장기 손실은 연 5-10억원입니다.",
            "operational_impact": "해안 사업장 장기적 운영 리스크가 있습니다.",
            "asset_impact": "해안 인프라 침식 및 방조제 보강이 필요합니다.",
            "summary": "장기적 대응 전략이 필요합니다."
        }
    ]


def create_sample_mitigation_strategies():
    """테스트용 Node 2-C 대응 전략 생성"""
    return [
        {
            "risk_type": "river_flood",
            "rank": 1,
            "short_term": [
                "[2026년] 침수 취약 지역 배수 펌프 5대 설치 (용량: 100㎥/h)",
                "[2026년] 비상 대응 매뉴얼 수립 및 분기별 훈련 실시"
            ],
            "mid_term": [
                "[2026-2027년] 데이터센터 방수벽 2m 높이로 증축 (총 연장 500m)",
                "[2027-2028년] 지하 전기실 방수 공사 및 침수 감지 센서 설치"
            ],
            "long_term": [
                "[2020-2030년대] 침수 위험 높은 사업장 재배치 타당성 검토",
                "[2030-2040년대] 기후 회복력 설계 기준 적용한 신규 사업장 개발"
            ],
            "priority": "매우 높음",
            "estimated_cost": "단기: 15억원, 중기: 80억원, 장기: 200억원",
            "expected_benefit": "AAL 5-7%p 감소 예상"
        },
        {
            "risk_type": "typhoon",
            "rank": 2,
            "short_term": [
                "[2026년] 태풍 대비 건물 외벽 보강 (내풍 설계)",
                "[2026년] 비상 발전기 및 UPS 점검 강화"
            ],
            "mid_term": [
                "[2026-2027년] 지붕 및 외벽 내풍 성능 강화 공사",
                "[2028-2029년] 창호 교체 (강화 유리)"
            ],
            "long_term": [
                "[2020-2030년대] 태풍 빈발 지역 사업장 리스크 재평가",
                "[2030-2040년대] 내풍 설계 기준 강화"
            ],
            "priority": "높음",
            "estimated_cost": "단기: 10억원, 중기: 50억원, 장기: 100억원",
            "expected_benefit": "AAL 3-4%p 감소 예상"
        },
        {
            "risk_type": "urban_flood",
            "rank": 3,
            "short_term": [
                "[2026년] 지하 배수 펌프 용량 확대 (기존 대비 50% 증설)"
            ],
            "mid_term": [
                "[2026-2027년] 침수 방지판 설치 (높이 1m)"
            ],
            "long_term": [
                "[2020-2030년대] 도심 침수 취약 사업장 이전 검토"
            ],
            "priority": "중간",
            "estimated_cost": "단기: 8억원, 중기: 30억원, 장기: 80억원",
            "expected_benefit": "AAL 2-3%p 감소"
        },
        {
            "risk_type": "extreme_heat",
            "rank": 4,
            "short_term": [
                "[2026년] 냉각탑 증설 (용량 30% 증대)"
            ],
            "mid_term": [
                "[2026-2028년] 데이터센터 냉각 시스템 교체"
            ],
            "long_term": [
                "[2020-2030년대] 고효율 냉각 기술 도입"
            ],
            "priority": "중간",
            "estimated_cost": "단기: 12억원, 중기: 60억원, 장기: 150억원",
            "expected_benefit": "AAL 2%p 감소"
        },
        {
            "risk_type": "sea_level_rise",
            "rank": 5,
            "short_term": [
                "[2026년] 해안 사업장 리스크 모니터링 시스템 구축"
            ],
            "mid_term": [
                "[2027-2030년] 방조제 보강 (높이 +1m)"
            ],
            "long_term": [
                "[2030-2050년대] 해안 사업장 단계적 이전 계획 수립"
            ],
            "priority": "중간",
            "estimated_cost": "단기: 5억원, 중기: 40억원, 장기: 200억원",
            "expected_benefit": "AAL 1-2%p 감소"
        }
    ]


def create_sample_sites_data():
    """테스트용 사업장 데이터 생성"""
    return [
        {
            "site_id": "site_001",
            "site_info": {"name": "서울 본사", "address": "서울시 강남구"},
            "risk_results": [
                {"risk_type": "river_flood", "final_aal": 7.2},
                {"risk_type": "typhoon", "final_aal": 2.1},
                {"risk_type": "urban_flood", "final_aal": 5.1},
                {"risk_type": "extreme_heat", "final_aal": 2.5},
                {"risk_type": "sea_level_rise", "final_aal": 0.0}
            ]
        },
        {
            "site_id": "site_002",
            "site_info": {"name": "판교 데이터센터", "address": "경기도 성남시"},
            "risk_results": [
                {"risk_type": "river_flood", "final_aal": 6.5},
                {"risk_type": "typhoon", "final_aal": 3.8},
                {"risk_type": "urban_flood", "final_aal": 2.1},
                {"risk_type": "extreme_heat", "final_aal": 3.2},
                {"risk_type": "sea_level_rise", "final_aal": 0.0}
            ]
        },
        {
            "site_id": "site_003",
            "site_info": {"name": "부산 물류센터", "address": "부산시 해운대구"},
            "risk_results": [
                {"risk_type": "river_flood", "final_aal": 4.5},
                {"risk_type": "typhoon", "final_aal": 5.5},
                {"risk_type": "urban_flood", "final_aal": 1.5},
                {"risk_type": "extreme_heat", "final_aal": 1.6},
                {"risk_type": "sea_level_rise", "final_aal": 6.2}
            ]
        }
    ]


def create_sample_impact_blocks():
    """테스트용 Node 2-B TextBlock 생성"""
    return [
        {
            "type": "text",
            "subheading": "P1. 하천 홍수 - 영향 분석",
            "content": "## 재무적 영향\n\n연간 50-80억원 손실 예상...\n\n## 운영적 영향\n\n3개 주요 사업장 운영 중단..."
        },
        {
            "type": "text",
            "subheading": "P2. 태풍 - 영향 분석",
            "content": "## 재무적 영향\n\n연간 30-50억원 손실..."
        },
        {
            "type": "text",
            "subheading": "P3. 도시 홍수 - 영향 분석",
            "content": "## 재무적 영향\n\n연간 20-30억원 손실..."
        },
        {
            "type": "text",
            "subheading": "P4. 극심한 고온 - 영향 분석",
            "content": "## 재무적 영향\n\n연간 10-15억원 손실..."
        },
        {
            "type": "text",
            "subheading": "P5. 해수면 상승 - 영향 분석",
            "content": "## 재무적 영향\n\n연간 5-10억원 손실..."
        }
    ]


def create_sample_mitigation_blocks():
    """테스트용 Node 2-C TextBlock 생성"""
    return [
        {
            "type": "text",
            "subheading": "P1. 하천 홍수 - 대응 전략",
            "content": "### 단기 조치 (향후 1년 - 2026년)\n\n- 배수 펌프 설치...\n\n### 중기 조치 (향후 5년 - 2026-2030년)\n\n- 방수벽 증축..."
        },
        {
            "type": "text",
            "subheading": "P2. 태풍 - 대응 전략",
            "content": "### 단기 조치\n\n- 외벽 보강..."
        },
        {
            "type": "text",
            "subheading": "P3. 도시 홍수 - 대응 전략",
            "content": "### 단기 조치\n\n- 배수 펌프 용량 확대..."
        },
        {
            "type": "text",
            "subheading": "P4. 극심한 고온 - 대응 전략",
            "content": "### 단기 조치\n\n- 냉각탑 증설..."
        },
        {
            "type": "text",
            "subheading": "P5. 해수면 상승 - 대응 전략",
            "content": "### 단기 조치\n\n- 모니터링 시스템 구축..."
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
            "단기/중기/장기 대응 전략을 수립하여 기후 회복력을 강화하고 있습니다."
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
        if "executive summary" in prompt.lower() or "종합" in prompt:
            print("✅ 모드: Executive Summary 생성")

        print(f"{'='*60}\n")

        # Mock Executive Summary 반환
        return """
## Executive Summary

우리는 **3개 사업장**에 대한 기후 물리적 리스크 분석을 수행하여,
포트폴리오 총 AAL **51.8%**를 확인했습니다.

### 주요 발견 사항

- **P1. 하천 홍수**: AAL 18.2% - 연간 50-80억원 손실 예상
- **P2. 태풍**: AAL 11.4% - 연간 30-50억원 손실 예상
- **P3. 도시 홍수**: AAL 8.7% - 연간 20-30억원 손실 예상

### 시나리오 분석 요약

- **저탄소 시나리오 (SSP1-2.6)**: 52.9% (2025) → 45.0% (2100) (-14.9%)
- **중간 시나리오 (SSP2-4.5)**: 52.9% (2025) → 68.1% (2100) (+28.7%)
- **높은 배출 시나리오 (SSP3-7.0)**: 52.9% (2025) → 85.3% (2100) (+61.2%)
- **최악 시나리오 (SSP5-8.5)**: 52.9% (2025) → 92.5% (2100) (+74.9%)

### 대응 전략

우리는 Top 5 리스크에 대해 **단기(2026년), 중기(2026-2030년), 장기(2020-2050년대)** 대응 전략을 수립했습니다.
우선순위가 높은 리스크에 대해서는 2026년 내 즉각적인 조치를 실행할 계획입니다.

**총 투자 예상액**: 단기 50억원, 중기 260억원, 장기 730억원

### 이해관계자 메시지

우리는 TCFD 권고안에 따라 기후 리스크를 체계적으로 관리하고 있으며,
지속적인 모니터링과 대응 전략 개선을 통해 기후 회복력을 강화하겠습니다.
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
                {"role": "system", "content": "You are an ELITE climate risk communications specialist."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        result = response.choices[0].message.content
        print(f"✅ API 응답 완료 ({len(result)} 글자)")
        return result


async def main():
    """테스트 실행"""
    print("\n" + "="*80)
    print("🧪 Node 3: Strategy Section v2 테스트")
    print("="*80)

    # 절대 import로 변경
    project_root = Path(__file__).parent.parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from ai_agent.agents.tcfd_report.node_3_strategy_section_v2 import StrategySectionNode

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

    # Node 3 초기화
    node = StrategySectionNode(llm_client=llm)

    # 샘플 데이터
    scenario_analysis = create_sample_scenario_analysis()
    impact_analyses = create_sample_impact_analyses()
    mitigation_strategies = create_sample_mitigation_strategies()
    sites_data = create_sample_sites_data()
    impact_blocks = create_sample_impact_blocks()
    mitigation_blocks = create_sample_mitigation_blocks()
    report_template = create_sample_report_template()

    print("\n📄 입력 데이터:")
    print(f"  - 시나리오 분석: {len(scenario_analysis['scenarios'])}개 시나리오")
    print(f"  - 영향 분석: {len(impact_analyses)}개 리스크")
    print(f"  - 대응 전략: {len(mitigation_strategies)}개 리스크")
    print(f"  - 사업장 데이터: {len(sites_data)}개 사업장")
    print(f"  - 영향 분석 블록: {len(impact_blocks)}개")
    print(f"  - 대응 전략 블록: {len(mitigation_blocks)}개")

    # Node 3 실행
    print("\n" + "="*80)
    print("▶ Node 3 실행")
    print("="*80)

    result = await node.execute(
        scenario_analysis=scenario_analysis,
        impact_analyses=impact_analyses,
        mitigation_strategies=mitigation_strategies,
        sites_data=sites_data,
        impact_blocks=impact_blocks,
        mitigation_blocks=mitigation_blocks,
        report_template=report_template,
        implementation_roadmap=None
    )

    # 결과 확인
    section_id = result["section_id"]
    title = result["title"]
    blocks = result["blocks"]
    heatmap_table_block = result["heatmap_table_block"]
    priority_actions_table = result["priority_actions_table"]
    total_pages = result["total_pages"]

    print("\n✅ 실행 완료!")
    print(f"\n📊 결과 요약:")
    print(f"  - Section ID: {section_id}")
    print(f"  - Title: {title}")
    print(f"  - 총 블록 개수: {len(blocks)}")
    print(f"  - 총 페이지 수: {total_pages}")

    # Executive Summary 확인
    print(f"\n🔍 Executive Summary 미리보기:")
    exec_summary_block = blocks[0]
    print(f"  Type: {exec_summary_block['type']}")
    print(f"  Subheading: {exec_summary_block['subheading']}")
    content = exec_summary_block['content']
    print(f"  내용 길이: {len(content)} 글자")
    print(f"  내용 미리보기:\n{content[:400]}...\n")

    # HeatmapTableBlock 확인
    print(f"\n📋 HeatmapTableBlock:")
    print(f"  Type: {heatmap_table_block['type']}")
    print(f"  Title: {heatmap_table_block['title']}")
    print(f"  Headers: {heatmap_table_block['data']['headers']}")
    print(f"  Rows: {len(heatmap_table_block['data']['rows'])}개")
    print(f"  Legend: {len(heatmap_table_block['data']['legend'])}개")

    # 첫 번째 행 미리보기
    if heatmap_table_block['data']['rows']:
        first_row = heatmap_table_block['data']['rows'][0]
        print(f"\n  첫 번째 행 (사업장: {first_row['site_name']}):")
        for i, cell in enumerate(first_row['cells'][:3]):
            print(f"    - Cell {i+1}: {cell['value']} (색상: {cell['bg_color']})")

    # Priority Actions Table 확인
    print(f"\n📋 Priority Actions Table:")
    print(f"  Type: {priority_actions_table['type']}")
    print(f"  Title: {priority_actions_table['title']}")
    print(f"  Headers: {priority_actions_table['data']['headers']}")
    print(f"  Rows: {len(priority_actions_table['data']['rows'])}개")

    # 첫 번째 행 미리보기
    if priority_actions_table['data']['rows']:
        first_row = priority_actions_table['data']['rows'][0]
        print(f"\n  첫 번째 행:")
        for i, cell in enumerate(first_row['cells']):
            print(f"    - {priority_actions_table['data']['headers'][i]}: {cell}")

    # 블록 구조 확인
    print(f"\n📚 블록 구조:")
    block_types = {}
    for block in blocks:
        block_type = block.get('type', 'unknown')
        block_types[block_type] = block_types.get(block_type, 0) + 1

    for block_type, count in block_types.items():
        print(f"  - {block_type}: {count}개")

    # 결과 저장
    output_dir = Path(__file__).parent / "test_output"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"node3_result_{timestamp}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n💾 결과 저장: {output_file}")

    print("\n" + "="*80)
    print("✅ Node 3 테스트 완료!")
    print("="*80)

    if not use_real:
        print("\n💡 실제 OpenAI API로 테스트하려면:")
        print("   1. set OPENAI_API_KEY=your_key")
        print("   2. set USE_REAL_LLM=true")
        print("   3. python -m ai_agent.agents.tcfd_report.test_node3_simple")


if __name__ == "__main__":
    asyncio.run(main())
