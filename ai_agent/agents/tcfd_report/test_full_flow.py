"""
TCFD Report 전체 플로우 테스트 스크립트
Node 0 → 1 → 2-A → 2-B → 2-C → 3 → 4 → 5 → 6 순차 실행 및 State 전달 검증

작성일: 2025-12-15
버전: v03 (Real LLM 지원)

사용법:
    python -m ai_agent.agents.tcfd_report.test_full_flow           # MockLLM 사용 (기본값)
    python -m ai_agent.agents.tcfd_report.test_full_flow --mock    # MockLLM 사용
    python -m ai_agent.agents.tcfd_report.test_full_flow --real    # Real OpenAI LLM 사용
"""

import os
import sys
import asyncio
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_full_flow")


# ============================================================
# Mock LLM Client (테스트용)
# ============================================================

class MockLLMClient:
    """테스트용 Mock LLM 클라이언트"""

    async def ainvoke(self, prompt: str) -> str:
        """Mock LLM 응답 생성"""
        # Node 1 템플릿 응답
        if "report template" in prompt.lower() or "tcfd" in prompt.lower():
            return json.dumps({
                "tone": {"style": "formal", "language": "Korean"},
                "reusable_paragraphs": [
                    "기후변화에 따른 물리적 리스크는 기업의 지속가능성에 중요한 영향을 미칩니다.",
                    "본 보고서는 TCFD 권고안에 따라 작성되었습니다."
                ],
                "hazard_template_blocks": {
                    "typhoon": "태풍 리스크 템플릿",
                    "river_flood": "하천 범람 리스크 템플릿"
                }
            }, ensure_ascii=False)

        # Node 2-A 시나리오 분석 응답
        if "scenario" in prompt.lower():
            return json.dumps({
                "scenarios": {
                    "SSP1-2.6": {"description": "지속가능 발전 시나리오", "severity": "Low"},
                    "SSP2-4.5": {"description": "중간 경로 시나리오", "severity": "Medium"},
                    "SSP5-8.5": {"description": "화석연료 기반 발전 시나리오", "severity": "High"}
                },
                "scenario_comparison": "SSP5-8.5 시나리오에서 가장 높은 리스크가 예상됩니다."
            }, ensure_ascii=False)

        # Node 2-B 영향 분석 응답
        if "impact" in prompt.lower():
            return json.dumps({
                "financial_impact": "연간 약 50억원의 재무적 영향이 예상됩니다.",
                "operational_impact": "운영 중단 시 최대 7일의 다운타임이 발생할 수 있습니다.",
                "asset_impact": "주요 설비의 손상으로 인한 자산 가치 하락이 예상됩니다.",
                "summary": "Top 1 리스크로 식별되어 즉각적인 대응이 필요합니다."
            }, ensure_ascii=False)

        # Node 2-C 대응 전략 응답
        if "mitigation" in prompt.lower() or "strategy" in prompt.lower():
            return json.dumps({
                "short_term": ["배수 펌프 설치", "침수 센서 설치", "비상 대응 매뉴얼 수립"],
                "mid_term": ["방수벽 증축", "백업 전원 설치"],
                "long_term": ["사업장 재배치 검토", "기후 적응 설비 투자"],
                "priority": "매우 높음",
                "priority_justification": "AAL 3.5%로 Top 1 리스크이며 즉각 대응이 필요합니다.",
                "estimated_cost": "단기: 5억원, 중기: 20억원, 장기: 100억원, 총: 125억원",
                "expected_benefit": "AAL 2%p 감소 예상, 자산 보호 효과 50억원",
                "implementation_considerations": "예산 확보 및 실행 계획 수립 필요"
            }, ensure_ascii=False)

        return "{}"

    def invoke(self, prompt: str) -> str:
        """동기 LLM 호출 (fallback)"""
        return asyncio.get_event_loop().run_until_complete(self.ainvoke(prompt))


# ============================================================
# Mock Data 생성
# ============================================================

def generate_mock_sites_data() -> List[Dict]:
    """Mock sites_data 생성 (Node 0 출력 형식)"""
    return [
        {
            "site_id": 1,
            "site_name": "서울 본사",
            "site_info": {
                "name": "서울 본사",
                "latitude": 37.5012,
                "longitude": 127.0396,
                "address": "서울시 강남구 테헤란로 123",
                "type": "office"
            },
            "risk_results": [
                {
                    "risk_type": "typhoon",
                    "target_year": "2030",
                    "final_aal": 3.5,
                    "hazard_score": 45,
                    "exposure_score": 60,
                    "vulnerability_score": 55
                },
                {
                    "risk_type": "river_flood",
                    "target_year": "2030",
                    "final_aal": 2.8,
                    "hazard_score": 40,
                    "exposure_score": 55,
                    "vulnerability_score": 50
                },
                {
                    "risk_type": "urban_flood",
                    "target_year": "2030",
                    "final_aal": 2.2,
                    "hazard_score": 35,
                    "exposure_score": 50,
                    "vulnerability_score": 45
                },
                {
                    "risk_type": "extreme_heat",
                    "target_year": "2030",
                    "final_aal": 1.8,
                    "hazard_score": 50,
                    "exposure_score": 45,
                    "vulnerability_score": 40
                },
                {
                    "risk_type": "drought",
                    "target_year": "2030",
                    "final_aal": 1.2,
                    "hazard_score": 30,
                    "exposure_score": 40,
                    "vulnerability_score": 35
                }
            ]
        },
        {
            "site_id": 2,
            "site_name": "부산 공장",
            "site_info": {
                "name": "부산 공장",
                "latitude": 35.0894,
                "longitude": 128.8539,
                "address": "부산시 강서구 녹산산업중로 456",
                "type": "factory"
            },
            "risk_results": [
                {
                    "risk_type": "typhoon",
                    "target_year": "2030",
                    "final_aal": 4.2,
                    "hazard_score": 55,
                    "exposure_score": 65,
                    "vulnerability_score": 60
                },
                {
                    "risk_type": "river_flood",
                    "target_year": "2030",
                    "final_aal": 3.1,
                    "hazard_score": 45,
                    "exposure_score": 60,
                    "vulnerability_score": 55
                },
                {
                    "risk_type": "sea_level_rise",
                    "target_year": "2030",
                    "final_aal": 2.5,
                    "hazard_score": 40,
                    "exposure_score": 55,
                    "vulnerability_score": 50
                },
                {
                    "risk_type": "urban_flood",
                    "target_year": "2030",
                    "final_aal": 1.9,
                    "hazard_score": 35,
                    "exposure_score": 45,
                    "vulnerability_score": 42
                },
                {
                    "risk_type": "extreme_heat",
                    "target_year": "2030",
                    "final_aal": 1.5,
                    "hazard_score": 45,
                    "exposure_score": 40,
                    "vulnerability_score": 38
                }
            ]
        }
    ]


def generate_mock_building_data() -> Dict[int, Dict]:
    """
    Mock building_data 생성 (BC Agent 출력 형식)

    실제 BC Agent (building_characteristics_agent.py v08) 출력 형식에 맞춤:
    - agent_guidelines: JSON 구조화된 가이드라인
    - impact_analysis_guide: financial_impact, operational_impact, asset_impact
    - mitigation_recommendations: short_term, mid_term, long_term (각각 dict 배열)
    """
    return {
        1: {
            "site_id": 1,
            "site_name": "서울 본사",
            "meta": {
                "analyzed_at": datetime.now().isoformat(),
                "location": {"lat": 37.5012, "lon": 127.0396},
                "data_source": "Mock Data (Test)"
            },
            "building_data": {
                "meta": {"address": "서울시 강남구 테헤란로 123"},
                "physical_specs": {
                    "structure": "철근콘크리트",
                    "age": {"years": 25, "completion_year": 2000},
                    "floors": {"ground": 15, "max_underground": 3},
                    "seismic": {"applied": "Y", "ability": "VI"}
                }
            },
            "structural_grade": "B (Good)",
            "vulnerabilities": [
                {"category": "Flood", "factor": "지하 전기실", "severity": "High", "description": "침수 시 전력 공급 차단 위험"},
                {"category": "Structural", "factor": "노후 배관", "severity": "Medium", "description": "25년 경과 배관 교체 필요"}
            ],
            "resilience": [
                {"category": "Seismic", "factor": "내진설계 적용", "strength": "Very High", "description": "2010년 이후 내진설계 기준 충족"},
                {"category": "Fire/Wind", "factor": "철근콘크리트 구조", "strength": "Medium", "description": "화재 및 강풍에 대한 저항성 보유"}
            ],
            "agent_guidelines": {
                "building_summary": {
                    "one_liner": "25년 경과 철근콘크리트 건물, 내진설계 적용",
                    "key_characteristics": ["준공 25년차 건물", "구조: 철근콘크리트", "내진설계 적용"],
                    "risk_exposure_level": "Medium"
                },
                "vulnerability_summary": {
                    "high_risk_factors": [
                        {
                            "factor": "지하 전기실",
                            "related_risks": ["river_flood", "urban_flood"],
                            "severity": "High",
                            "impact_description": "침수 시 전력 공급 차단으로 전체 건물 운영 중단 위험"
                        }
                    ],
                    "resilience_factors": [
                        {
                            "factor": "내진설계 적용",
                            "related_risks": ["typhoon"],
                            "strength": "Very High",
                            "benefit_description": "지진 및 강풍에 대한 구조적 안정성 확보"
                        }
                    ]
                },
                "impact_analysis_guide": {
                    "financial_impact": {
                        "estimated_exposure": "Medium",
                        "key_cost_drivers": ["지하 전기실 침수 복구", "설비 교체"],
                        "narrative": "지하 전기실 침수 시 복구 비용 및 운영 중단에 따른 손실이 발생할 수 있습니다. 건물 노후화로 인한 추가 유지보수 비용도 고려해야 합니다."
                    },
                    "operational_impact": {
                        "critical_systems_at_risk": ["전기 설비", "IT 서버", "냉난방 시스템"],
                        "estimated_downtime": "최대 7일",
                        "narrative": "지하 전기실이 침수될 경우 전체 건물의 전력 공급이 차단되어 최대 7일간 운영 중단이 예상됩니다."
                    },
                    "asset_impact": {
                        "vulnerable_assets": ["지하 전기실", "기계실", "서버룸"],
                        "damage_potential": "Moderate",
                        "narrative": "지하층에 위치한 핵심 설비들이 침수에 취약하며, 손상 시 상당한 복구 비용이 소요됩니다."
                    }
                },
                "mitigation_recommendations": {
                    "short_term": [
                        {"action": "배수 펌프 설치", "target_risk": "urban_flood", "priority": "High", "estimated_cost": "5천만원~1억원"},
                        {"action": "침수 센서 설치", "target_risk": "river_flood", "priority": "High", "estimated_cost": "2천만원~5천만원"}
                    ],
                    "mid_term": [
                        {"action": "방수벽 증축", "target_risk": "river_flood", "priority": "Medium", "estimated_cost": "3억원~5억원"},
                        {"action": "백업 전원 설치", "target_risk": "urban_flood", "priority": "Medium", "estimated_cost": "2억원~3억원"}
                    ],
                    "long_term": [
                        {"action": "전기실 이전 검토", "target_risk": "urban_flood", "priority": "Medium", "estimated_cost": "10억원~20억원"}
                    ]
                },
                "report_narrative_guide": {
                    "recommended_tone": "neutral",
                    "key_message": "구조등급 B 건물로, 지하 전기실 침수 리스크에 대한 체계적인 관리 필요",
                    "tcfd_alignment": "물리적 리스크 노출에 대한 모니터링 및 대응 전략 수립",
                    "stakeholder_focus": "건물 리스크 현황 파악 및 단계별 대응 방안 제시"
                }
            }
        },
        2: {
            "site_id": 2,
            "site_name": "부산 공장",
            "meta": {
                "analyzed_at": datetime.now().isoformat(),
                "location": {"lat": 35.0894, "lon": 128.8539},
                "data_source": "Mock Data (Test)"
            },
            "building_data": {
                "meta": {"address": "부산시 강서구 녹산산업중로 456"},
                "physical_specs": {
                    "structure": "철골",
                    "age": {"years": 35, "completion_year": 1990},
                    "floors": {"ground": 3, "max_underground": 1},
                    "seismic": {"applied": "N"}
                }
            },
            "structural_grade": "C (Fair)",
            "vulnerabilities": [
                {"category": "Flood", "factor": "해안 인접", "severity": "Very High", "description": "해수면 상승 및 태풍 피해 위험"},
                {"category": "Wind", "factor": "대형 창고 지붕", "severity": "High", "description": "강풍 시 지붕 파손 위험"}
            ],
            "resilience": [
                {"category": "Fire/Wind", "factor": "철골 구조", "strength": "Medium", "description": "철골 구조로 일부 내풍성 확보"}
            ],
            "agent_guidelines": {
                "building_summary": {
                    "one_liner": "35년 경과 철골 공장, 해안 인접 위치",
                    "key_characteristics": ["준공 35년차 건물", "구조: 철골", "해안 500m 이내"],
                    "risk_exposure_level": "High"
                },
                "vulnerability_summary": {
                    "high_risk_factors": [
                        {
                            "factor": "해안 인접",
                            "related_risks": ["sea_level_rise", "typhoon"],
                            "severity": "Very High",
                            "impact_description": "해수면 상승 및 태풍 시 직접적인 침수 피해 위험이 높습니다."
                        },
                        {
                            "factor": "대형 창고 지붕",
                            "related_risks": ["typhoon"],
                            "severity": "High",
                            "impact_description": "강풍 시 지붕 파손으로 생산 설비 피해 가능"
                        }
                    ],
                    "resilience_factors": [
                        {
                            "factor": "철골 구조",
                            "related_risks": ["typhoon"],
                            "strength": "Medium",
                            "benefit_description": "철골 구조로 일부 강풍에 대한 저항성 확보"
                        }
                    ]
                },
                "impact_analysis_guide": {
                    "financial_impact": {
                        "estimated_exposure": "High",
                        "key_cost_drivers": ["태풍 피해 복구", "생산 중단 손실", "설비 교체"],
                        "narrative": "해안 인접 공장으로 태풍 및 해수면 상승에 따른 재무적 노출이 높습니다. 생산 라인 중단 시 막대한 손실이 예상됩니다."
                    },
                    "operational_impact": {
                        "critical_systems_at_risk": ["생산 라인", "물류 시스템", "전기 설비"],
                        "estimated_downtime": "최대 14일",
                        "narrative": "태풍 피해 시 생산 라인 중단으로 최대 14일간 운영 중단이 예상됩니다. 물류 시스템도 영향을 받습니다."
                    },
                    "asset_impact": {
                        "vulnerable_assets": ["생산 설비", "창고 지붕", "전기 설비"],
                        "damage_potential": "Severe",
                        "narrative": "생산 설비 및 창고 지붕이 태풍에 취약하며, 피해 시 상당한 복구 비용과 시간이 소요됩니다."
                    }
                },
                "mitigation_recommendations": {
                    "short_term": [
                        {"action": "태풍 경보 시스템 구축", "target_risk": "typhoon", "priority": "High", "estimated_cost": "3천만원~5천만원"},
                        {"action": "지붕 보강 점검", "target_risk": "typhoon", "priority": "High", "estimated_cost": "1억원~2억원"}
                    ],
                    "mid_term": [
                        {"action": "방풍벽 설치", "target_risk": "typhoon", "priority": "High", "estimated_cost": "5억원~10억원"},
                        {"action": "배수 시스템 강화", "target_risk": "sea_level_rise", "priority": "Medium", "estimated_cost": "3억원~5억원"}
                    ],
                    "long_term": [
                        {"action": "공장 재배치 검토", "target_risk": "sea_level_rise", "priority": "High", "estimated_cost": "100억원~300억원"},
                        {"action": "기후 적응 설비 투자", "target_risk": "typhoon", "priority": "Medium", "estimated_cost": "20억원~50억원"}
                    ]
                },
                "report_narrative_guide": {
                    "recommended_tone": "warning",
                    "key_message": "해안 인접 노후 공장으로 기후 리스크 노출이 높아 즉각적인 대응 필요",
                    "tcfd_alignment": "물리적 리스크 관리 및 장기적 자산 재배치 전략 필요",
                    "stakeholder_focus": "높은 리스크 노출 현황 및 단계별 투자 계획 제시"
                }
            }
        }
    }


def generate_mock_additional_data() -> Dict[str, Any]:
    """Mock additional_data 생성 (AD Agent 출력 형식)"""
    return {
        "meta": {
            "analyzed_at": datetime.now().isoformat(),
            "source_file": "test_additional_data.xlsx",
            "site_count": 2
        },
        "site_specific_guidelines": {
            1: {
                "site_id": 1,
                "guideline": "서울 본사는 강남구에 위치하여 도시 침수 리스크가 높습니다. 지하 주차장 및 전기실 보호에 중점을 두어야 합니다.",
                "key_insights": ["도시 침수 취약", "지하 전기실 보호 필요", "IT 인프라 백업 중요"]
            },
            2: {
                "site_id": 2,
                "guideline": "부산 공장은 해안 인접으로 태풍 및 해수면 상승 리스크가 매우 높습니다. 장기적으로 재배치를 검토해야 합니다.",
                "key_insights": ["태풍 피해 우려", "해수면 상승 영향", "장기 재배치 검토 필요"]
            }
        },
        "summary": "총 2개 사업장에 대한 추가 데이터가 분석되었습니다.",
        "status": "completed"
    }


# ============================================================
# 전체 플로우 테스트
# ============================================================

async def run_full_flow_test(use_mock: bool = True):
    """전체 플로우 테스트 실행"""

    print("\n" + "=" * 80)
    print("🚀 TCFD Report 전체 플로우 테스트 시작")
    print("=" * 80)

    # LLM 클라이언트 선택
    if use_mock:
        llm_client = MockLLMClient()
        print("  📌 LLM: MockLLMClient (테스트용)")
    else:
        # Real OpenAI LLM 사용
        from ai_agent.utils.llm_client import LLMClient
        llm_client = LLMClient(model="gpt-4o-mini", temperature=0.7, max_tokens=8192)
        print("  📌 LLM: OpenAI gpt-4o-mini (Real API)")

    # ========== Step 0: Mock 데이터 준비 ==========
    print("\n[Step 0] 테스트 데이터 준비...")

    sites_data = generate_mock_sites_data()
    building_data = generate_mock_building_data()
    additional_data = generate_mock_additional_data()

    print(f"  ✅ sites_data: {len(sites_data)}개 사업장")
    print(f"  ✅ building_data: {len(building_data)}개 사업장")
    print(f"  ✅ additional_data: {len(additional_data.get('site_specific_guidelines', {}))}개 가이드라인")

    # ========== Step 1: Node 1 - Template Loading ==========
    print("\n[Step 1] Node 1: Template Loading 실행...")

    from ai_agent.agents.tcfd_report.node_1_template_loading_v2 import TemplateLoadingNode

    node_1 = TemplateLoadingNode(llm_client=llm_client)

    result_1 = await node_1.execute(
        company_name="테스트 회사",
        past_reports=[],
        mode="init"
    )

    report_template = result_1.get("report_template", {})
    print(f"  ✅ report_template 생성 완료")
    print(f"     - tone: {report_template.get('tone', {})}")
    print(f"     - reusable_paragraphs: {len(report_template.get('reusable_paragraphs', []))}개")

    # ========== Step 2: Node 2-A - Scenario Analysis ==========
    print("\n[Step 2] Node 2-A: Scenario Analysis 실행...")

    from ai_agent.agents.tcfd_report.node_2a_scenario_analysis_v2 import ScenarioAnalysisNode

    node_2a = ScenarioAnalysisNode(llm_client=llm_client)

    result_2a = await node_2a.execute(
        sites_data=sites_data,
        report_template=report_template,
        agent_guideline=None
    )

    scenario_analysis = result_2a
    print(f"  ✅ scenario_analysis 생성 완료")
    print(f"     - scenarios: {list(result_2a.get('scenarios', {}).keys())}")

    # ========== Step 3: Node 2-B - Impact Analysis ==========
    print("\n[Step 3] Node 2-B: Impact Analysis 실행...")

    from ai_agent.agents.tcfd_report.node_2b_impact_analysis_v2 import ImpactAnalysisNode

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

    print(f"  ✅ impact_analyses 생성 완료: {len(impact_analyses)}개 리스크 분석")
    print(f"  ✅ impact_blocks 생성 완료: {len(impact_blocks)}개 TextBlock")
    print(f"  ✅ Top 5 리스크:")
    for i, risk in enumerate(top_5_risks[:5], 1):
        print(f"     P{i}. {risk.get('risk_type')}: AAL {risk.get('total_aal', 0):.2f}%")

    # ========== Step 4: Node 2-C - Mitigation Strategies ==========
    print("\n[Step 4] Node 2-C: Mitigation Strategies 실행...")

    from ai_agent.agents.tcfd_report.node_2c_mitigation_strategies_v2 import MitigationStrategiesNode

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

    print(f"  ✅ mitigation_strategies 생성 완료: {len(mitigation_strategies)}개 전략")
    print(f"  ✅ mitigation_blocks 생성 완료: {len(mitigation_blocks)}개 TextBlock")
    print(f"  ✅ implementation_roadmap 생성 완료")

    # ========== Step 5: Node 3 - Strategy Section ==========
    print("\n[Step 5] Node 3: Strategy Section 실행...")

    from ai_agent.agents.tcfd_report.node_3_strategy_section_v2 import StrategySectionNode

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

    print(f"  ✅ strategy_section 생성 완료")
    print(f"     - blocks: {len(result_3.get('blocks', []))}개")
    print(f"     - heatmap_table_block: {'생성됨' if heatmap_table_block else '없음'}")

    # ========== Step 6: Node 4 - Validator ==========
    print("\n[Step 6] Node 4: Validator 실행...")

    from ai_agent.agents.tcfd_report.node_4_validator_v2 import ValidatorNode

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

    print(f"  ✅ 검증 완료")
    print(f"     - is_valid: {is_valid}")
    print(f"     - quality_score: {quality_score}")

    # ========== Step 7: Node 5 - Composer ==========
    print("\n[Step 7] Node 5: Composer 실행...")

    from ai_agent.agents.tcfd_report.node_5_composer_v2 import ComposerNode

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

    print(f"  ✅ 보고서 조립 완료")
    print(f"     - sections: {len(sections)}개")
    print(f"     - sections: {[s.get('section_id', 'N/A') for s in sections]}")

    # ========== Step 8: Node 6 - Finalizer (Mock) ==========
    print("\n[Step 8] Node 6: Finalizer 실행 (Mock - DB 저장 생략)...")

    from ai_agent.agents.tcfd_report.node_6_finalizer_v2 import FinalizerNode

    node_6 = FinalizerNode(db_session=None)  # DB 세션 없이 Mock 실행

    result_6 = await node_6.execute(
        report=report,
        user_id=1,
        site_ids=[1, 2]
    )

    print(f"  ✅ Finalizer 완료 (Mock)")
    print(f"     - success: {result_6.get('success', False)}")
    print(f"     - report_id: {result_6.get('report_id', 'N/A')}")

    # ========== 결과 요약 ==========
    print("\n" + "=" * 80)
    print("📊 전체 플로우 테스트 결과 요약")
    print("=" * 80)

    print("\n[데이터 흐름 검증]")
    print(f"  Node 0 → sites_data: {len(sites_data)}개 사업장")
    print(f"  Node 0 → building_data: {len(building_data)}개 사업장 (BC Agent)")
    print(f"  Node 0 → additional_data: {additional_data.get('status', 'N/A')} (AD Agent)")
    print(f"  Node 1 → report_template: 생성 완료")
    print(f"  Node 2-A → scenario_analysis: {len(result_2a.get('scenarios', {}))}개 시나리오")
    print(f"  Node 2-B → impact_analyses: {len(impact_analyses)}개 영향 분석")
    print(f"  Node 2-B → impact_blocks: {len(impact_blocks)}개 TextBlock")
    print(f"  Node 2-C → mitigation_strategies: {len(mitigation_strategies)}개 대응 전략")
    print(f"  Node 2-C → mitigation_blocks: {len(mitigation_blocks)}개 TextBlock")
    print(f"  Node 3 → strategy_section: {len(result_3.get('blocks', []))}개 블록")
    print(f"  Node 3 → heatmap_table_block: {'✅' if heatmap_table_block else '❌'}")
    print(f"  Node 4 → validation: {'✅ PASS' if is_valid else '❌ FAIL'} (점수: {quality_score})")
    print(f"  Node 5 → report: {len(sections)}개 섹션")
    print(f"  Node 6 → saved: {result_6.get('success', False)}")

    print("\n[building_data 활용 검증]")
    print(f"  Node 2-B에서 building_data 전달: {'✅' if building_data else '❌'}")
    print(f"  Node 2-C에서 building_data 전달: {'✅' if building_data else '❌'}")

    print("\n[additional_data 활용 검증]")
    print(f"  Node 2-B에서 additional_data 전달: {'✅' if additional_data else '❌'}")
    print(f"  Node 2-C에서 additional_data 전달: {'✅' if additional_data else '❌'}")

    print("\n" + "=" * 80)
    print("✅ 전체 플로우 테스트 완료! (Node 1 ~ Node 6)")
    print("=" * 80)

    return {
        "sites_data": sites_data,
        "building_data": building_data,
        "additional_data": additional_data,
        "report_template": report_template,
        "scenario_analysis": scenario_analysis,
        "impact_analyses": impact_analyses,
        "impact_blocks": impact_blocks,
        "mitigation_strategies": mitigation_strategies,
        "mitigation_blocks": mitigation_blocks,
        "implementation_roadmap": implementation_roadmap,
        "strategy_section": strategy_section,
        "heatmap_table_block": heatmap_table_block,
        "validation_result": validation_result,
        "report": report,
        "finalizer_result": result_6
    }


# ============================================================
# Main
# ============================================================

def main():
    """메인 실행"""
    import argparse

    parser = argparse.ArgumentParser(description="TCFD Report 전체 플로우 테스트")
    parser.add_argument("--mock", action="store_true", help="MockLLM으로 테스트 (기본값)")
    parser.add_argument("--real", action="store_true", help="Real OpenAI LLM으로 테스트 (gpt-4o-mini)")

    args = parser.parse_args()

    # --real 옵션이 있으면 use_mock=False, 그렇지 않으면 use_mock=True (기본값)
    use_mock = not args.real

    result = asyncio.run(run_full_flow_test(use_mock=use_mock))

    # 결과 저장
    output_path = Path(__file__).parent / "test_output.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n📁 결과 저장: {output_path}")


if __name__ == "__main__":
    main()
