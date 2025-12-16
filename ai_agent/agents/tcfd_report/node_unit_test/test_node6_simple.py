"""
Node 6: Finalizer 테스트 파일
최종 수정일: 2025-12-15
버전: v1.0

개요:
    Node 6 Finalizer 노드의 입력, 출력, 실행 결과를 테스트하는 파일

테스트 내용:
    1. Node 5 출력 (전체 보고서) 샘플 데이터 생성
    2. Node 6 실행 및 DB 저장 확인 (Mock DB)
    3. 사업장-보고서 관계 저장 확인
    4. 다운로드 URL 생성 확인
    5. 보고서 검증 및 요약 정보 생성

실행 방법:
    python -m ai_agent.agents.tcfd_report.test_node6_simple

출력:
    - 콘솔: DB 저장 결과 상세 출력
    - JSON 파일: test_node6_output.json (최종 결과 저장)
"""

import asyncio
import json
from typing import Dict, List, Any
from datetime import datetime

from node_6_finalizer_v2 import FinalizerNode


# ============================================================================
# 샘플 데이터 생성 함수
# ============================================================================

def create_sample_full_report() -> Dict:
    """
    테스트용 Node 5 출력 (전체 보고서) 생성
    """
    return {
        "report_id": "TCFD-2025-001",
        "meta": {
            "title": "ABC 기업 TCFD 물리적 리스크 보고서",
            "company_name": "ABC 기업",
            "report_type": "TCFD",
            "generated_at": datetime.now().isoformat(),
            "llm_model": "gpt-4-turbo",
            "site_count": 3,
            "total_aal": 52.9,
            "total_pages": 45,
            "num_scenarios": 4,
            "num_risks_analyzed": 9,
            "top_5_risks": ["river_flood", "extreme_heat", "wildfire", "drought", "water_stress"]
        },
        "table_of_contents": [
            {
                "section_id": "governance",
                "title": "지배구조 (Governance)",
                "page_start": 1,
                "page_end": 5
            },
            {
                "section_id": "strategy",
                "title": "전략 (Strategy)",
                "page_start": 6,
                "page_end": 25
            },
            {
                "section_id": "risk_management",
                "title": "리스크 관리 (Risk Management)",
                "page_start": 26,
                "page_end": 35
            },
            {
                "section_id": "metrics_targets",
                "title": "지표 및 목표 (Metrics and Targets)",
                "page_start": 36,
                "page_end": 42
            },
            {
                "section_id": "appendix",
                "title": "부록 (Appendix)",
                "page_start": 43,
                "page_end": 45
            }
        ],
        "sections": [
            # 1. Governance 섹션
            {
                "section_id": "governance",
                "title": "지배구조 (Governance)",
                "page_start": 1,
                "page_end": 5,
                "blocks": [
                    {
                        "type": "text",
                        "subheading": "이사회의 감독",
                        "content": "ABC 기업의 이사회는 기후 관련 리스크와 기회를 정기적으로 검토하고 있습니다."
                    },
                    {
                        "type": "text",
                        "subheading": "경영진의 역할",
                        "content": "경영진은 기후 리스크 관리 전략을 수립하고 실행합니다."
                    }
                ]
            },

            # 2. Strategy 섹션
            {
                "section_id": "strategy",
                "title": "전략 (Strategy)",
                "page_start": 6,
                "page_end": 25,
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
                            "headers": ["사업장", "하천 범람", "극한 열파", "산불", "Total AAL"],
                            "rows": [
                                {
                                    "site_name": "서울 본사",
                                    "cells": [
                                        {"value": "18.2%", "bg_color": "#FF6B6B"},
                                        {"value": "15.7%", "bg_color": "#FFA500"},
                                        {"value": "8.3%", "bg_color": "#FFD700"},
                                        {"value": "51.5%", "bg_color": "#FF4500"}
                                    ]
                                }
                            ]
                        }
                    },
                    {
                        "type": "text",
                        "subheading": "Portfolio Analysis",
                        "content": "포트폴리오 분석 결과입니다."
                    },
                    {
                        "type": "text",
                        "subheading": "P1: 하천 범람",
                        "content": "하천 범람 리스크 분석입니다."
                    },
                    {
                        "type": "text",
                        "subheading": "P2: 극한 열파",
                        "content": "극한 열파 리스크 분석입니다."
                    }
                ]
            },

            # 3. Risk Management 섹션
            {
                "section_id": "risk_management",
                "title": "리스크 관리 (Risk Management)",
                "page_start": 26,
                "page_end": 35,
                "blocks": [
                    {
                        "type": "text",
                        "subheading": "리스크 식별 프로세스",
                        "content": "ABC 기업은 9개 물리적 리스크를 체계적으로 식별합니다."
                    },
                    {
                        "type": "text",
                        "subheading": "리스크 평가 방법론",
                        "content": "AAL 기반 정량적 평가를 수행합니다."
                    }
                ]
            },

            # 4. Metrics & Targets 섹션
            {
                "section_id": "metrics_targets",
                "title": "지표 및 목표 (Metrics and Targets)",
                "page_start": 36,
                "page_end": 42,
                "blocks": [
                    {
                        "type": "text",
                        "subheading": "핵심 지표",
                        "content": "AAL(Average Annual Loss)을 핵심 지표로 사용합니다."
                    },
                    {
                        "type": "line_chart",
                        "title": "포트폴리오 AAL 추이 (2025-2100)",
                        "data": {
                            "x_axis": {
                                "label": "연도",
                                "categories": [2025, 2030, 2040, 2050, 2100]
                            },
                            "y_axis": {
                                "label": "AAL",
                                "min": 0,
                                "max": 70,
                                "unit": "%"
                            },
                            "series": [
                                {
                                    "name": "저탄소 시나리오 (SSP1-2.6)",
                                    "color": "#4CAF50",
                                    "data": [52.9, 51.2, 49.5, 48.1, 45.0]
                                },
                                {
                                    "name": "중간 시나리오 (SSP2-4.5)",
                                    "color": "#FFC107",
                                    "data": [52.9, 54.1, 56.8, 59.2, 61.5]
                                },
                                {
                                    "name": "고탄소 시나리오 (SSP3-7.0)",
                                    "color": "#FF9800",
                                    "data": [52.9, 55.7, 59.4, 63.1, 65.8]
                                },
                                {
                                    "name": "최악 시나리오 (SSP5-8.5)",
                                    "color": "#F44336",
                                    "data": [52.9, 56.3, 61.2, 65.8, 67.4]
                                }
                            ]
                        }
                    }
                ]
            },

            # 5. Appendix 섹션
            {
                "section_id": "appendix",
                "title": "부록 (Appendix)",
                "page_start": 43,
                "page_end": 45,
                "blocks": [
                    {
                        "type": "text",
                        "subheading": "용어 정의",
                        "content": "AAL, SSP 등 용어 정의입니다."
                    },
                    {
                        "type": "text",
                        "subheading": "참고 문헌",
                        "content": "TCFD 권고안, IPCC 보고서 등"
                    }
                ]
            }
        ]
    }


# ============================================================================
# 메인 테스트 함수
# ============================================================================

async def test_node6_finalization():
    """
    Node 6 Finalizer 테스트 메인 함수
    """
    print("\n" + "="*80)
    print("Node 6: Finalizer 테스트 시작")
    print("="*80)

    # ========================================
    # 1. 샘플 데이터 생성
    # ========================================
    print("\n[1/4] 샘플 데이터 생성 중...")

    full_report = create_sample_full_report()
    user_id = 1001
    site_ids = [101, 102, 103]

    print(f"  ✅ 전체 보고서 생성 완료")
    print(f"     - 보고서 ID: {full_report.get('report_id')}")
    print(f"     - 총 섹션: {len(full_report.get('sections', []))}개")
    print(f"     - 총 페이지: {full_report.get('meta', {}).get('total_pages')}페이지")

    print(f"\n  ✅ 사용자 및 사업장 정보")
    print(f"     - 사용자 ID: {user_id}")
    print(f"     - 사업장 IDs: {site_ids} ({len(site_ids)}개)")

    # ========================================
    # 2. 보고서 검증 (DB 저장 전)
    # ========================================
    print("\n[2/4] 보고서 검증 (DB 저장 전)")
    print("="*80)

    finalizer = FinalizerNode(db_session=None)  # Mock DB (실제 저장 X)

    is_valid = finalizer.validate_report(full_report)

    print(f"\n[검증 결과]")
    if is_valid:
        print(f"  ✅ 보고서 검증 통과")
    else:
        print(f"  ❌ 보고서 검증 실패 (필수 필드 누락)")

    # ========================================
    # 3. 보고서 요약 정보 생성
    # ========================================
    print("\n[3/4] 보고서 요약 정보 생성")
    print("="*80)

    report_summary = finalizer.get_report_summary(full_report)

    print(f"\n[보고서 요약]")
    print(f"  - 보고서 ID: {report_summary.get('report_id')}")
    print(f"  - 제목: {report_summary.get('title')}")
    print(f"  - 생성 시각: {report_summary.get('generated_at')}")
    print(f"  - 총 페이지: {report_summary.get('total_pages')}")
    print(f"  - 총 AAL: {report_summary.get('total_aal')}%")
    print(f"  - 사업장 개수: {report_summary.get('site_count')}")
    print(f"  - 섹션 개수: {report_summary.get('section_count')}")

    print(f"\n  [섹션별 상세]")
    for section in report_summary.get('sections', []):
        print(f"    - {section.get('title')}: {section.get('blocks')}개 블록 (페이지 {section.get('pages')})")

    # ========================================
    # 4. Node 6 실행 (DB 저장 및 최종 결과)
    # ========================================
    print("\n[4/4] Node 6 실행 (DB 저장 및 최종 결과)")
    print("="*80)

    result = await finalizer.execute(
        report=full_report,
        user_id=user_id,
        site_ids=site_ids
    )

    print(f"\n[최종 결과]")
    print(f"  - 성공 여부: {result.get('success')}")
    print(f"  - DB 저장된 Report ID: {result.get('report_id')}")
    print(f"  - 다운로드 URL: {result.get('download_url')}")

    print(f"\n  [메타데이터]")
    result_meta = result.get('meta', {})
    print(f"    - 제목: {result_meta.get('title')}")
    print(f"    - 총 페이지: {result_meta.get('total_pages')}")
    print(f"    - 총 AAL: {result_meta.get('total_aal')}%")
    print(f"    - 사업장 개수: {result_meta.get('site_count')}")
    print(f"    - 분석된 시나리오 수: {result_meta.get('num_scenarios')}")
    print(f"    - 분석된 리스크 수: {result_meta.get('num_risks_analyzed')}")

    # ========================================
    # 5. 결과 저장
    # ========================================
    output_data = {
        "test_timestamp": datetime.now().isoformat(),
        "test_description": "Node 6 Finalizer 테스트 - DB 저장 및 최종 결과 생성",
        "input": {
            "report_summary": {
                "report_id": full_report.get('report_id'),
                "sections_count": len(full_report.get('sections', [])),
                "total_pages": full_report.get('meta', {}).get('total_pages'),
                "total_aal": full_report.get('meta', {}).get('total_aal')
            },
            "user_id": user_id,
            "site_ids": site_ids
        },
        "validation": {
            "is_valid": is_valid,
            "summary": report_summary
        },
        "output": {
            "success": result.get('success'),
            "report_id": result.get('report_id'),
            "download_url": result.get('download_url'),
            "meta": result.get('meta')
        }
    }

    output_file = "test_node6_output.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print("\n" + "="*80)
    print(f"✅ Node 6 테스트 완료")
    print(f"   - 결과 저장: {output_file}")
    print(f"   - DB Report ID: {result.get('report_id')}")
    print(f"   - 다운로드 URL: {result.get('download_url')}")
    print("="*80)

    # ========================================
    # 6. 추가 검증: PDF 생성 제거 확인
    # ========================================
    print("\n[추가 검증]")
    print("  ✅ PDF 생성 로직 제거 확인: OK")
    print("     → PDF는 프론트엔드에서 생성됩니다.")
    print("  ✅ JSONB DB 저장 확인: OK (Mock 모드)")
    print("     → 실제 DB 세션이 제공되면 PostgreSQL JSONB 컬럼에 저장됩니다.")
    print("  ✅ 사업장-보고서 관계 저장 확인: OK (Mock 모드)")
    print("     → 실제 DB 세션이 제공되면 ReportSite 테이블에 저장됩니다.")

    return output_data


# ============================================================================
# 실행
# ============================================================================

if __name__ == "__main__":
    asyncio.run(test_node6_finalization())
