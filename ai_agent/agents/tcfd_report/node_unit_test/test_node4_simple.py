"""
Node 4: Validator & Refiner 테스트 파일
최종 수정일: 2025-12-15
버전: v1.0

개요:
    Node 4 Validator 노드의 입력, 출력, 실행 결과를 테스트하는 파일

테스트 내용:
    1. Node 3 출력 (Strategy Section) 샘플 데이터 생성
    2. Node 2-A, 2-B 샘플 데이터 생성 (검증용)
    3. Node 4 실행 및 검증 결과 확인
    4. TCFD 7대 원칙 점수 확인
    5. 품질 점수 확인
    6. 이슈 리스트 확인

실행 방법:
    python -m ai_agent.agents.tcfd_report.test_node4_simple

출력:
    - 콘솔: 검증 결과 상세 출력
    - JSON 파일: test_node4_output.json (검증 결과 저장)
"""

import asyncio
import json
from typing import Dict, List, Any
from datetime import datetime

from node_4_validator_v2 import ValidatorNode


# ============================================================================
# 샘플 데이터 생성 함수
# ============================================================================

def create_sample_strategy_section() -> Dict:
    """
    테스트용 Node 3 Strategy Section 출력 생성
    (정상 케이스 - 모든 필수 요소 포함)
    """
    return {
        "section_id": "strategy",
        "title": "전략 (Strategy)",
        "blocks": [
            # 1. Executive Summary
            {
                "type": "text",
                "subheading": "Executive Summary",
                "content": """본 TCFD 보고서는 ABC 기업의 물리적 기후 리스크를 종합적으로 분석한 결과입니다.
4개의 SSP 시나리오 분석 결과, 2050년까지 평균 AAL은 현재 대비 최대 27.3% 증가할 것으로 예측됩니다.
특히 하천 범람(18.2% AAL)과 극한 열파(15.7% AAL)가 가장 큰 위협 요인으로 식별되었습니다.
이에 대응하기 위해 ABC 기업은 5개년 단위 적응 전략을 수립하였으며, 총 5개 우선 리스크에 대한 완화 조치를 계획하고 있습니다."""
            },

            # 2. HeatmapTableBlock
            {
                "type": "heatmap_table",
                "title": "사업장별 물리적 리스크 AAL 분포",
                "data": {
                    "headers": ["사업장", "하천 범람", "극한 열파", "산불", "가뭄", "물 부족", "Total AAL"],
                    "rows": [
                        {
                            "site_name": "서울 본사",
                            "cells": [
                                {"value": "18.2%", "bg_color": "#FF6B6B"},
                                {"value": "15.7%", "bg_color": "#FFA500"},
                                {"value": "8.3%", "bg_color": "#FFD700"},
                                {"value": "5.1%", "bg_color": "#90EE90"},
                                {"value": "4.2%", "bg_color": "#90EE90"},
                                {"value": "51.5%", "bg_color": "#FF4500"}
                            ]
                        },
                        {
                            "site_name": "부산 공장",
                            "cells": [
                                {"value": "12.4%", "bg_color": "#FFA500"},
                                {"value": "11.2%", "bg_color": "#FFA500"},
                                {"value": "6.8%", "bg_color": "#FFD700"},
                                {"value": "4.3%", "bg_color": "#90EE90"},
                                {"value": "3.1%", "bg_color": "#90EE90"},
                                {"value": "37.8%", "bg_color": "#FFA500"}
                            ]
                        },
                        {
                            "site_name": "대구 물류센터",
                            "cells": [
                                {"value": "9.8%", "bg_color": "#FFD700"},
                                {"value": "8.5%", "bg_color": "#FFD700"},
                                {"value": "5.2%", "bg_color": "#90EE90"},
                                {"value": "3.7%", "bg_color": "#90EE90"},
                                {"value": "2.9%", "bg_color": "#90EE90"},
                                {"value": "30.1%", "bg_color": "#FFD700"}
                            ]
                        }
                    ],
                    "legend": [
                        {"label": "매우 높음 (>15%)", "color": "#FF6B6B"},
                        {"label": "높음 (10-15%)", "color": "#FFA500"},
                        {"label": "중간 (5-10%)", "color": "#FFD700"},
                        {"label": "낮음 (<5%)", "color": "#90EE90"}
                    ]
                }
            },

            # 3. Portfolio Analysis
            {
                "type": "text",
                "subheading": "Portfolio Analysis",
                "content": """ABC 기업의 포트폴리오 분석 결과, 현재 총 AAL은 52.9%로 높은 수준의 물리적 리스크에 노출되어 있습니다.
시나리오별 분석 결과, SSP5-8.5(고탄소 시나리오)에서 2050년까지 AAL이 67.4%까지 증가할 것으로 예측됩니다."""
            },

            # 4. P1 Block
            {
                "type": "text",
                "subheading": "P1: 하천 범람 (River Flood) - AAL 18.2%",
                "content": """하천 범람은 ABC 기업의 가장 큰 물리적 리스크로 식별되었습니다.
서울 본사가 가장 큰 영향을 받으며, 2050년까지 연평균 18.2%의 자산 손실이 예상됩니다."""
            },

            # 5. P2 Block
            {
                "type": "text",
                "subheading": "P2: 극한 열파 (Extreme Heat) - AAL 15.7%",
                "content": """극한 열파는 두 번째로 큰 리스크로, 특히 여름철 운영 중단 가능성이 높습니다."""
            },

            # 6. P3 Block
            {
                "type": "text",
                "subheading": "P3: 산불 (Wildfire) - AAL 8.3%",
                "content": """산불 리스크는 주로 산림 인접 지역에서 발생하며, 대구 물류센터가 가장 높은 노출도를 보입니다."""
            },

            # 7. P4 Block
            {
                "type": "text",
                "subheading": "P4: 가뭄 (Drought) - AAL 5.1%",
                "content": """가뭄은 장기적인 물 공급 중단 가능성을 높이며, 특히 물 의존도가 높은 부산 공장에 영향을 미칩니다."""
            },

            # 8. P5 Block
            {
                "type": "text",
                "subheading": "P5: 물 부족 (Water Stress) - AAL 4.2%",
                "content": """물 부족은 가뭄과 연관되어 발생하며, 장기적인 물 공급 안정성에 영향을 미칩니다."""
            }
        ],

        # Priority Actions Table (Node 3에서 생성)
        "priority_actions_table": {
            "type": "table",
            "title": "우선 완화 조치 계획",
            "data": {
                "headers": ["우선순위", "리스크 유형", "현재 AAL", "목표 AAL (2030)", "완화 조치"],
                "rows": [
                    ["P1", "하천 범람", "18.2%", "12.5%", "방수벽 설치, 배수 시스템 개선"],
                    ["P2", "극한 열파", "15.7%", "11.0%", "냉각 시스템 업그레이드, 단열재 보강"],
                    ["P3", "산불", "8.3%", "5.5%", "방화대 조성, 소화 시스템 설치"],
                    ["P4", "가뭄", "5.1%", "3.5%", "물 저장 시설 확대, 절수 설비 도입"],
                    ["P5", "물 부족", "4.2%", "2.8%", "중수도 시스템 구축, 물 재활용 설비"]
                ]
            }
        }
    }


def create_sample_strategy_section_with_issues() -> Dict:
    """
    테스트용 Node 3 Strategy Section 출력 생성
    (이슈 포함 케이스 - Executive Summary 누락, 블록 개수 부족)
    """
    return {
        "section_id": "strategy",
        "title": "전략 (Strategy)",
        "blocks": [
            # Executive Summary 누락 (Critical 이슈)

            # 블록 개수 부족 (3개만 포함, 최소 5개 권장) - Warning 이슈
            {
                "type": "text",
                "subheading": "Portfolio Analysis",
                "content": "간단한 포트폴리오 분석입니다."
            },
            {
                "type": "text",
                "subheading": "P1: 하천 범람",
                "content": "하천 범람 설명입니다."
            },
            {
                "type": "text",
                "subheading": "P2: 극한 열파",
                "content": "극한 열파 설명입니다."
            }
        ],

        # HeatmapTableBlock 누락 (Warning 이슈)
        # Priority Actions Table은 존재
        "priority_actions_table": {
            "type": "table",
            "title": "우선 완화 조치 계획",
            "data": {
                "headers": ["우선순위", "리스크 유형", "완화 조치"],
                "rows": [
                    ["P1", "하천 범람", "방수벽 설치"]
                ]
            }
        }
    }


def create_sample_scenario_analysis() -> Dict:
    """테스트용 Node 2-A 시나리오 분석 결과 생성"""
    return {
        "scenarios": {
            "ssp1_2.6": {
                "scenario_name_kr": "저탄소 시나리오 (SSP1-2.6)",
                "aal_values": [52.9, 51.2, 49.5, 48.1, 45.0],
                "change_rate": -14.9
            },
            "ssp2_4.5": {
                "scenario_name_kr": "중간 시나리오 (SSP2-4.5)",
                "aal_values": [52.9, 54.1, 56.8, 59.2, 61.5],
                "change_rate": 16.3
            },
            "ssp3_7.0": {
                "scenario_name_kr": "고탄소 시나리오 (SSP3-7.0)",
                "aal_values": [52.9, 55.7, 59.4, 63.1, 65.8],
                "change_rate": 24.4
            },
            "ssp5_8.5": {
                "scenario_name_kr": "최악 시나리오 (SSP5-8.5)",
                "aal_values": [52.9, 56.3, 61.2, 65.8, 67.4],
                "change_rate": 27.3
            }
        }
    }


def create_sample_impact_analyses() -> List[Dict]:
    """테스트용 Node 2-B 영향 분석 결과 생성"""
    return [
        {
            "risk_type": "river_flood",
            "rank": 1,
            "total_aal": 18.2,
            "num_affected_sites": 3,
            "top_affected_sites": ["서울 본사", "부산 공장", "대구 물류센터"]
        },
        {
            "risk_type": "extreme_heat",
            "rank": 2,
            "total_aal": 15.7,
            "num_affected_sites": 3,
            "top_affected_sites": ["서울 본사", "부산 공장", "대구 물류센터"]
        },
        {
            "risk_type": "wildfire",
            "rank": 3,
            "total_aal": 8.3,
            "num_affected_sites": 2,
            "top_affected_sites": ["대구 물류센터", "서울 본사"]
        },
        {
            "risk_type": "drought",
            "rank": 4,
            "total_aal": 5.1,
            "num_affected_sites": 2,
            "top_affected_sites": ["부산 공장", "서울 본사"]
        },
        {
            "risk_type": "water_stress",
            "rank": 5,
            "total_aal": 4.2,
            "num_affected_sites": 2,
            "top_affected_sites": ["부산 공장", "대구 물류센터"]
        }
    ]


# ============================================================================
# 메인 테스트 함수
# ============================================================================

async def test_node4_validation():
    """
    Node 4 Validator 테스트 메인 함수
    """
    print("\n" + "="*80)
    print("Node 4: Validator & Refiner 테스트 시작")
    print("="*80)

    # ========================================
    # 1. 샘플 데이터 생성
    # ========================================
    print("\n[1/3] 샘플 데이터 생성 중...")

    # 정상 케이스
    strategy_section_normal = create_sample_strategy_section()
    scenario_analysis = create_sample_scenario_analysis()
    impact_analyses = create_sample_impact_analyses()

    print(f"  ✅ 정상 Strategy Section 생성 완료")
    print(f"     - 블록 개수: {len(strategy_section_normal.get('blocks', []))}")
    print(f"     - Executive Summary 포함: Yes")
    print(f"     - HeatmapTableBlock 포함: Yes")
    print(f"     - Priority Actions Table 포함: Yes")

    # 이슈 포함 케이스
    strategy_section_with_issues = create_sample_strategy_section_with_issues()

    print(f"\n  ✅ 이슈 포함 Strategy Section 생성 완료")
    print(f"     - 블록 개수: {len(strategy_section_with_issues.get('blocks', []))}")
    print(f"     - Executive Summary 포함: No (Critical)")
    print(f"     - HeatmapTableBlock 포함: No (Warning)")
    print(f"     - Priority Actions Table 포함: Yes")

    # ========================================
    # 2. Node 4 실행 (정상 케이스)
    # ========================================
    print("\n" + "="*80)
    print("[2/3] Node 4 실행 (정상 케이스)")
    print("="*80)

    validator = ValidatorNode(llm_client=None)  # LLM 불필요 (규칙 기반 검증)

    result_normal = await validator.execute(
        strategy_section=strategy_section_normal,
        report_template=None,
        scenario_analysis=scenario_analysis,
        impact_analyses=impact_analyses
    )

    validation_result_normal = result_normal["validation_result"]

    print("\n[검증 결과 - 정상 케이스]")
    print(f"  - 검증 통과: {validation_result_normal['is_valid']}")
    print(f"  - 품질 점수: {validation_result_normal['quality_score']:.1f}/100")
    print(f"  - 이슈 개수: {len(validation_result_normal['issues'])}")

    if validation_result_normal['issues']:
        print(f"\n  [발견된 이슈]")
        for i, issue in enumerate(validation_result_normal['issues'], 1):
            print(f"    {i}. [{issue['severity'].upper()}] {issue['message']}")

    print(f"\n  [TCFD 7대 원칙 점수]")
    for principle, score in validation_result_normal['principle_scores'].items():
        print(f"    - {principle}: {score:.1f}/100")

    print(f"\n  [피드백]")
    print(f"    {validation_result_normal['feedback']}")

    # ========================================
    # 3. Node 4 실행 (이슈 포함 케이스)
    # ========================================
    print("\n" + "="*80)
    print("[3/3] Node 4 실행 (이슈 포함 케이스)")
    print("="*80)

    result_with_issues = await validator.execute(
        strategy_section=strategy_section_with_issues,
        report_template=None,
        scenario_analysis=scenario_analysis,
        impact_analyses=impact_analyses
    )

    validation_result_with_issues = result_with_issues["validation_result"]

    print("\n[검증 결과 - 이슈 포함 케이스]")
    print(f"  - 검증 통과: {validation_result_with_issues['is_valid']}")
    print(f"  - 품질 점수: {validation_result_with_issues['quality_score']:.1f}/100")
    print(f"  - 이슈 개수: {len(validation_result_with_issues['issues'])}")

    if validation_result_with_issues['issues']:
        print(f"\n  [발견된 이슈]")
        for i, issue in enumerate(validation_result_with_issues['issues'], 1):
            severity_icon = "🔴" if issue['severity'] == "critical" else "🟡"
            print(f"    {severity_icon} {i}. [{issue['severity'].upper()}] {issue['message']}")

    print(f"\n  [TCFD 7대 원칙 점수]")
    for principle, score in validation_result_with_issues['principle_scores'].items():
        print(f"    - {principle}: {score:.1f}/100")

    print(f"\n  [피드백]")
    feedback_lines = validation_result_with_issues['feedback'].split('\n')
    for line in feedback_lines:
        print(f"    {line}")

    # ========================================
    # 4. 결과 저장
    # ========================================
    output_data = {
        "test_timestamp": datetime.now().isoformat(),
        "test_description": "Node 4 Validator 테스트 - 정상 케이스 및 이슈 포함 케이스",
        "normal_case": {
            "input": {
                "strategy_section_summary": {
                    "blocks_count": len(strategy_section_normal.get('blocks', [])),
                    "has_exec_summary": True,
                    "has_heatmap": True,
                    "has_priority_table": True
                },
                "scenario_analysis_provided": scenario_analysis is not None,
                "impact_analyses_count": len(impact_analyses)
            },
            "output": validation_result_normal
        },
        "with_issues_case": {
            "input": {
                "strategy_section_summary": {
                    "blocks_count": len(strategy_section_with_issues.get('blocks', [])),
                    "has_exec_summary": False,
                    "has_heatmap": False,
                    "has_priority_table": True
                },
                "scenario_analysis_provided": scenario_analysis is not None,
                "impact_analyses_count": len(impact_analyses)
            },
            "output": validation_result_with_issues
        }
    }

    output_file = "test_node4_output.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print("\n" + "="*80)
    print(f"✅ Node 4 테스트 완료")
    print(f"   - 결과 저장: {output_file}")
    print("="*80)

    return output_data


# ============================================================================
# 실행
# ============================================================================

if __name__ == "__main__":
    asyncio.run(test_node4_validation())
