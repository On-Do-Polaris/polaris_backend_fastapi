"""
Node 5: Composer 테스트 파일
최종 수정일: 2025-12-15
버전: v1.0

개요:
    Node 5 Composer 노드의 입력, 출력, 실행 결과를 테스트하는 파일

테스트 내용:
    1. Node 3 출력 (Strategy Section) 샘플 데이터 생성
    2. Node 2-A, 2-B, 2-C 샘플 데이터 생성
    3. Node 5 실행 및 전체 보고서 생성 확인
    4. Governance, Risk Management, Metrics & Targets, Appendix 섹션 확인
    5. 목차 생성 확인
    6. 메타데이터 확인

실행 방법:
    python -m ai_agent.agents.tcfd_report.test_node5_simple

출력:
    - 콘솔: 보고서 생성 결과 상세 출력
    - JSON 파일: test_node5_output.json (전체 보고서 저장)
"""

import asyncio
import json
from typing import Dict, List, Any
from datetime import datetime

from node_5_composer_v2 import ComposerNode


# ============================================================================
# 샘플 데이터 생성 함수
# ============================================================================

def create_sample_strategy_section() -> Dict:
    """테스트용 Node 3 Strategy Section 출력 생성"""
    return {
        "section_id": "strategy",
        "title": "전략 (Strategy)",
        "page_start": 3,
        "page_end": 8,
        "blocks": [
            {
                "type": "text",
                "subheading": "Executive Summary",
                "content": """본 TCFD 보고서는 ABC 기업의 물리적 기후 리스크를 종합적으로 분석한 결과입니다.
4개의 SSP 시나리오 분석 결과, 2050년까지 평균 AAL은 현재 대비 최대 27.3% 증가할 것으로 예측됩니다."""
            },
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
            {
                "type": "text",
                "subheading": "Portfolio Analysis",
                "content": "ABC 기업의 포트폴리오 분석 결과입니다."
            },
            {
                "type": "text",
                "subheading": "P1: 하천 범람 (River Flood) - AAL 18.2%",
                "content": "하천 범람 리스크 분석 결과입니다."
            },
            {
                "type": "text",
                "subheading": "P2: 극한 열파 (Extreme Heat) - AAL 15.7%",
                "content": "극한 열파 리스크 분석 결과입니다."
            }
        ],
        "priority_actions_table": {
            "type": "table",
            "title": "우선 완화 조치 계획",
            "data": {
                "headers": ["우선순위", "리스크 유형", "현재 AAL", "목표 AAL (2030)", "완화 조치"],
                "rows": [
                    ["P1", "하천 범람", "18.2%", "12.5%", "방수벽 설치, 배수 시스템 개선"],
                    ["P2", "극한 열파", "15.7%", "11.0%", "냉각 시스템 업그레이드"]
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
                "scenario_name_en": "SSP1-2.6",
                "description": "지속가능한 발전 경로, 온실가스 감축 목표 달성",
                "aal_values": [52.9, 51.2, 49.5, 48.1, 45.0],
                "timeline": [2025, 2030, 2040, 2050, 2100],
                "change_rate": -14.9,
                "key_insights": "2050년까지 AAL 14.9% 감소 예상"
            },
            "ssp2_4.5": {
                "scenario_name_kr": "중간 시나리오 (SSP2-4.5)",
                "scenario_name_en": "SSP2-4.5",
                "description": "현재 정책 기조 유지, 중간 수준의 온실가스 배출",
                "aal_values": [52.9, 54.1, 56.8, 59.2, 61.5],
                "timeline": [2025, 2030, 2040, 2050, 2100],
                "change_rate": 16.3,
                "key_insights": "2050년까지 AAL 16.3% 증가 예상"
            },
            "ssp3_7.0": {
                "scenario_name_kr": "고탄소 시나리오 (SSP3-7.0)",
                "scenario_name_en": "SSP3-7.0",
                "description": "지역 분열, 높은 온실가스 배출",
                "aal_values": [52.9, 55.7, 59.4, 63.1, 65.8],
                "timeline": [2025, 2030, 2040, 2050, 2100],
                "change_rate": 24.4,
                "key_insights": "2050년까지 AAL 24.4% 증가 예상"
            },
            "ssp5_8.5": {
                "scenario_name_kr": "최악 시나리오 (SSP5-8.5)",
                "scenario_name_en": "SSP5-8.5",
                "description": "화석연료 기반 고성장, 최고 수준의 온실가스 배출",
                "aal_values": [52.9, 56.3, 61.2, 65.8, 67.4],
                "timeline": [2025, 2030, 2040, 2050, 2100],
                "change_rate": 27.3,
                "key_insights": "2050년까지 AAL 27.3% 증가 예상 (최악)"
            }
        },
        "portfolio_summary": {
            "total_sites": 3,
            "baseline_aal": 52.9,
            "min_future_aal": 45.0,
            "max_future_aal": 67.4
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
            "top_affected_sites": ["서울 본사", "부산 공장", "대구 물류센터"],
            "impact_description": "하천 범람으로 인한 심각한 피해 예상"
        },
        {
            "risk_type": "extreme_heat",
            "rank": 2,
            "total_aal": 15.7,
            "num_affected_sites": 3,
            "top_affected_sites": ["서울 본사", "부산 공장", "대구 물류센터"],
            "impact_description": "극한 열파로 인한 운영 중단 가능성"
        },
        {
            "risk_type": "wildfire",
            "rank": 3,
            "total_aal": 8.3,
            "num_affected_sites": 2,
            "top_affected_sites": ["대구 물류센터", "서울 본사"],
            "impact_description": "산불 리스크 증가"
        },
        {
            "risk_type": "drought",
            "rank": 4,
            "total_aal": 5.1,
            "num_affected_sites": 2,
            "top_affected_sites": ["부산 공장", "서울 본사"],
            "impact_description": "가뭄으로 인한 물 공급 중단 우려"
        },
        {
            "risk_type": "water_stress",
            "rank": 5,
            "total_aal": 4.2,
            "num_affected_sites": 2,
            "top_affected_sites": ["부산 공장", "대구 물류센터"],
            "impact_description": "물 부족 장기화 가능성"
        }
    ]


def create_sample_mitigation_strategies() -> List[Dict]:
    """테스트용 Node 2-C 완화 전략 결과 생성"""
    return [
        {
            "risk_type": "river_flood",
            "rank": 1,
            "current_aal": 18.2,
            "target_aal": 12.5,
            "reduction_target": 31.3,
            "timeline": {
                "short_term": {
                    "period": "2026년 (1년)",
                    "actions": ["방수벽 설계 및 예산 확보", "배수 시스템 현황 조사"],
                    "expected_aal": 17.0
                },
                "mid_term": {
                    "period": "2026-2030년 (5년, 연도별)",
                    "actions": ["방수벽 설치 (2027-2028)", "배수 시스템 개선 (2028-2029)"],
                    "expected_aal": 14.5
                },
                "long_term": {
                    "period": "2020년대/2030년대/2040년대/2050년대 (10년 단위)",
                    "actions": ["지속적인 모니터링 및 유지보수", "신규 기술 도입 검토"],
                    "expected_aal": 12.5
                }
            }
        },
        {
            "risk_type": "extreme_heat",
            "rank": 2,
            "current_aal": 15.7,
            "target_aal": 11.0,
            "reduction_target": 29.9,
            "timeline": {
                "short_term": {
                    "period": "2026년 (1년)",
                    "actions": ["냉각 시스템 성능 평가", "단열재 현황 조사"],
                    "expected_aal": 14.5
                },
                "mid_term": {
                    "period": "2026-2030년 (5년, 연도별)",
                    "actions": ["냉각 시스템 업그레이드 (2027-2028)", "단열재 보강 (2028-2029)"],
                    "expected_aal": 12.5
                },
                "long_term": {
                    "period": "2020년대/2030년대/2040년대/2050년대 (10년 단위)",
                    "actions": ["에너지 효율 개선", "친환경 냉각 기술 도입"],
                    "expected_aal": 11.0
                }
            }
        }
    ]


def create_sample_report_template() -> Dict:
    """테스트용 Node 1 보고서 템플릿 생성"""
    return {
        "report_id": "TCFD-2025-001",
        "meta": {
            "company_name": "ABC 기업",
            "report_type": "TCFD 물리적 리스크 보고서",
            "generated_at": datetime.now().isoformat(),
            "llm_model": "gpt-4-turbo",
            "site_count": 3,
            "total_aal": 52.9
        },
        "table_of_contents": []  # Node 5에서 생성
    }


# ============================================================================
# 메인 테스트 함수
# ============================================================================

async def test_node5_composition():
    """
    Node 5 Composer 테스트 메인 함수
    """
    print("\n" + "="*80)
    print("Node 5: Composer 테스트 시작")
    print("="*80)

    # ========================================
    # 1. 샘플 데이터 생성
    # ========================================
    print("\n[1/2] 샘플 데이터 생성 중...")

    strategy_section = create_sample_strategy_section()
    scenario_analysis = create_sample_scenario_analysis()
    impact_analyses = create_sample_impact_analyses()
    mitigation_strategies = create_sample_mitigation_strategies()
    report_template = create_sample_report_template()

    print(f"  ✅ Strategy Section 생성 완료")
    print(f"     - 블록 개수: {len(strategy_section.get('blocks', []))}")
    print(f"     - 페이지 범위: {strategy_section.get('page_start')}-{strategy_section.get('page_end')}")

    print(f"\n  ✅ 시나리오 분석 생성 완료")
    print(f"     - 시나리오 개수: {len(scenario_analysis.get('scenarios', {}))}")

    print(f"\n  ✅ 영향 분석 생성 완료")
    print(f"     - Top 5 리스크 개수: {len(impact_analyses)}")

    print(f"\n  ✅ 완화 전략 생성 완료")
    print(f"     - 완화 전략 개수: {len(mitigation_strategies)}")

    print(f"\n  ✅ 보고서 템플릿 생성 완료")
    print(f"     - 보고서 ID: {report_template.get('report_id')}")

    # ========================================
    # 2. Node 5 실행
    # ========================================
    print("\n" + "="*80)
    print("[2/2] Node 5 실행")
    print("="*80)

    composer = ComposerNode(llm_client=None)  # LLM 불필요 (하드코딩된 섹션)

    result = await composer.execute(
        strategy_section=strategy_section,
        report_template=report_template,
        scenario_analysis=scenario_analysis,
        impact_analyses=impact_analyses,
        mitigation_strategies=mitigation_strategies
    )

    full_report = result["full_report"]

    # ========================================
    # 3. 결과 검증
    # ========================================
    print("\n[생성된 보고서 요약]")
    print(f"  - 보고서 ID: {full_report.get('report_id')}")
    print(f"  - 총 섹션 개수: {len(full_report.get('sections', []))}")
    print(f"  - 총 페이지: {full_report.get('meta', {}).get('total_pages')}")

    print(f"\n[메타데이터]")
    meta = full_report.get("meta", {})
    for key, value in meta.items():
        if key == "generated_at":
            continue  # 시간 정보는 너무 길어서 생략
        print(f"  - {key}: {value}")

    print(f"\n[목차 (Table of Contents)]")
    toc = full_report.get("table_of_contents", [])
    for i, item in enumerate(toc, 1):
        print(f"  {i}. {item.get('title')} (페이지 {item.get('page_start')}-{item.get('page_end')})")

    print(f"\n[섹션별 상세]")
    sections = full_report.get("sections", [])
    for section in sections:
        section_id = section.get("section_id")
        title = section.get("title")
        blocks = section.get("blocks", [])
        page_range = f"{section.get('page_start')}-{section.get('page_end')}"

        print(f"\n  📌 {title} (ID: {section_id})")
        print(f"     - 페이지: {page_range}")
        print(f"     - 블록 개수: {len(blocks)}")

        # 블록 타입 분포
        block_types = {}
        for block in blocks:
            block_type = block.get("type", "unknown")
            block_types[block_type] = block_types.get(block_type, 0) + 1

        print(f"     - 블록 타입 분포:")
        for block_type, count in block_types.items():
            print(f"       * {block_type}: {count}개")

        # 특별한 블록 미리보기
        if section_id == "metrics_targets":
            # LineChartBlock 확인
            line_chart = None
            for block in blocks:
                if block.get("type") == "line_chart":
                    line_chart = block
                    break

            if line_chart:
                print(f"     - LineChartBlock 발견:")
                print(f"       * 제목: {line_chart.get('title')}")
                chart_data = line_chart.get("data", {})
                series = chart_data.get("series", [])
                print(f"       * 시계열 개수: {len(series)}")
                for s in series:
                    print(f"         - {s.get('name')}: {len(s.get('data', []))}개 데이터 포인트")

    # ========================================
    # 4. 결과 저장
    # ========================================
    output_data = {
        "test_timestamp": datetime.now().isoformat(),
        "test_description": "Node 5 Composer 테스트 - 전체 보고서 생성",
        "input": {
            "strategy_section_summary": {
                "blocks_count": len(strategy_section.get('blocks', [])),
                "page_range": f"{strategy_section.get('page_start')}-{strategy_section.get('page_end')}"
            },
            "scenario_analysis_count": len(scenario_analysis.get('scenarios', {})),
            "impact_analyses_count": len(impact_analyses),
            "mitigation_strategies_count": len(mitigation_strategies),
            "report_template_id": report_template.get('report_id')
        },
        "output": full_report
    }

    output_file = "test_node5_output.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print("\n" + "="*80)
    print(f"✅ Node 5 테스트 완료")
    print(f"   - 결과 저장: {output_file}")
    print(f"   - 총 섹션: {len(full_report.get('sections', []))}개")
    print(f"   - 총 페이지: {full_report.get('meta', {}).get('total_pages')}페이지")
    print("="*80)

    return output_data


# ============================================================================
# 실행
# ============================================================================

if __name__ == "__main__":
    asyncio.run(test_node5_composition())
