"""
Node 3: Strategy Section Generator
Executive Summary + Portfolio 통합 + Heatmap + P1~P5 섹션 생성

설계 이유:
- Node 6 삭제 통합: v1의 Portfolio 분석을 Node 3에 통합
- HeatmapTableBlock 생성: 사업장별 리스크 분포 히트맵 JSON 생성
- 색상 코딩: Gray/Yellow/Orange/Red 4단계 AAL 시각화
- 7-8 페이지: TCFD 보고서의 핵심 섹션

작성일: 2025-12-14 (v2 Refactoring)
"""

from typing import Dict, Any, List
from .schemas import HeatmapTableBlock, HeatmapTableData, HeatmapRow, HeatmapCell, get_heatmap_color


class StrategySectionNode:
    """
    Node 3: Strategy 섹션 생성 노드

    입력:
        - scenario_analysis: Dict (Node 2-A 출력)
        - impact_analyses: List[dict] (Node 2-B 출력)
        - mitigation_strategies: List[dict] (Node 2-C 출력)
        - sites_data: List[dict] (Node 0 출력)

    출력:
        - section_id: "strategy"
        - blocks: List[dict] (text, heatmap_table, ...)
        - total_pages: int
    """

    def __init__(self, llm):
        self.llm = llm

    async def execute(
        self,
        scenario_analysis: Dict,
        impact_analyses: List[Dict],
        mitigation_strategies: List[Dict],
        sites_data: List[Dict],
        impact_blocks: List[Dict],
        mitigation_blocks: List[Dict]
    ) -> Dict[str, Any]:
        """
        메인 실행 함수
        """
        # 1. HeatmapTableBlock 생성 (JSON 형식)
        top_5_risks = [ia["risk_type"] for ia in impact_analyses]
        heatmap_table_block = self._generate_heatmap_table_block(sites_data, top_5_risks)

        # 2. Executive Summary 생성
        exec_summary = await self._generate_executive_summary(
            scenario_analysis,
            impact_analyses,
            sites_data
        )

        # 3. 전체 블록 조립
        blocks = [
            {"type": "text", "subheading": "Executive Summary", "content": exec_summary},
            {"type": "text", "subheading": "2.1 리스크 및 기회 식별", "content": "기후 물리적 리스크 분석 결과를 기반으로..."},
            heatmap_table_block,  # HeatmapTableBlock
            {"type": "text", "subheading": "2.2 사업 및 재무 영향", "content": "포트폴리오 전체의 기후 리스크 노출도..."},
            {"type": "text", "subheading": "2.3 주요 리스크별 영향 분석 및 대응 방안", "content": ""},
        ] + self._integrate_impact_and_mitigation(impact_blocks, mitigation_blocks)

        return {
            "section_id": "strategy",
            "title": "Strategy",
            "blocks": blocks,
            "heatmap_table_block": heatmap_table_block,  # 별도로도 반환
            "total_pages": 7
        }

    def _generate_heatmap_table_block(
        self,
        sites_data: List[Dict],
        top_5_risks: List[str]
    ) -> Dict:
        """
        HeatmapTableBlock 생성 (schemas.py 형식)

        Returns:
            HeatmapTableBlock JSON
        """
        # 리스크 이름 한글 매핑
        risk_name_mapping = {
            "river_flood": "하천범람",
            "typhoon": "태풍",
            "urban_flood": "도시침수",
            "extreme_heat": "극심한고온",
            "sea_level_rise": "해수면상승",
            "drought": "가뭄",
            "landslide": "산사태",
            "wildfire": "산불",
            "cold_wave": "한파"
        }

        # 헤더 생성
        headers = ["사업장"] + [risk_name_mapping.get(r, r) for r in top_5_risks] + ["Total AAL"]

        # 행 데이터 생성
        rows = []
        for site in sites_data:
            site_name = site.get("site_info", {}).get("name", "Unknown")
            cells = []
            site_total_aal = 0.0

            # 각 리스크별 AAL 계산
            for risk_type in top_5_risks:
                # risk_results에서 해당 리스크 찾기
                aal = 0.0
                for risk_result in site.get("risk_results", []):
                    if risk_result.get("risk_type") == risk_type:
                        aal = risk_result.get("final_aal", 0.0)
                        break

                site_total_aal += aal

                # HeatmapCell 생성
                cells.append({
                    "value": f"{aal:.1f}%",
                    "bg_color": get_heatmap_color(aal)
                })

            # Total AAL 셀 추가
            cells.append({
                "value": f"{site_total_aal:.1f}%",
                "bg_color": get_heatmap_color(site_total_aal)
            })

            rows.append({
                "site_name": site_name,
                "cells": cells
            })

        # HeatmapTableBlock 생성
        heatmap_table_block = {
            "type": "heatmap_table",
            "title": "사업장별 물리적 리스크 AAL 분포",
            "data": {
                "headers": headers,
                "rows": rows,
                "legend": [
                    {"color": "gray", "label": "0-3% (낮음)"},
                    {"color": "yellow", "label": "3-10% (중간)"},
                    {"color": "orange", "label": "10-30% (높음)"},
                    {"color": "red", "label": "30%+ (매우 높음)"}
                ]
            }
        }

        return heatmap_table_block

    async def _generate_executive_summary(
        self,
        scenario_analysis: Dict,
        impact_analyses: List[Dict],
        sites_data: List[Dict]
    ) -> str:
        """
        Executive Summary 생성
        """
        # TODO: LLM 프롬프트 작성
        return "Executive Summary 내용"  # TODO

    def _integrate_impact_and_mitigation(
        self,
        impact_blocks: List[Dict],
        mitigation_blocks: List[Dict]
    ) -> List[Dict]:
        """
        Node 2-B와 Node 2-C에서 생성된 블록들을 P1~P5 순서로 통합

        Args:
            impact_blocks: Node 2-B의 TextBlock x5 (영향 분석)
            mitigation_blocks: Node 2-C의 TextBlock x5 (대응 전략)

        Returns:
            통합된 블록 리스트 (P1 영향 + P1 대응 + P2 영향 + P2 대응 + ...)
        """
        integrated_blocks = []

        for impact_block, mitigation_block in zip(impact_blocks, mitigation_blocks):
            integrated_blocks.append(impact_block)
            integrated_blocks.append(mitigation_block)

        return integrated_blocks
