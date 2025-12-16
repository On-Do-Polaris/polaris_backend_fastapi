"""
TCFD Report JSON Schema Definitions
차트 및 표 형식 표준화를 위한 Pydantic 스키마

작성일: 2025-12-14
버전: v1.0
"""

from typing import Literal, List, Optional, Union
from pydantic import BaseModel, Field


# ============================================================
# Text Block
# ============================================================

class TextBlock(BaseModel):
    """
    일반 텍스트 블록

    사용: 모든 섹션의 텍스트 콘텐츠
    """
    type: Literal["text"] = "text"
    subheading: Optional[str] = Field(None, description="소제목 (optional)")
    content: str = Field(..., description="본문 내용 (Markdown 또는 Plain Text)")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "text",
                "subheading": "2.1 리스크 및 기회 식별",
                "content": "우리는 9가지 물리적 리스크를 평가했습니다..."
            }
        }


# ============================================================
# Table (일반 표)
# ============================================================

class TableCell(BaseModel):
    """표 셀"""
    value: Union[str, float, int] = Field(..., description="셀 값")
    bg_color: Optional[str] = Field(None, description="배경색 (hex code)")
    text_color: Optional[str] = Field(None, description="텍스트 색상 (hex code)")
    alignment: Optional[Literal["left", "center", "right"]] = Field("left", description="정렬")


class TableRow(BaseModel):
    """표 행"""
    cells: List[Union[str, TableCell]] = Field(..., description="셀 리스트 (단순 문자열 or TableCell 객체)")


class TableData(BaseModel):
    """표 데이터"""
    headers: List[str] = Field(..., description="헤더 행")
    rows: List[TableRow] = Field(..., description="데이터 행")
    footer: Optional[List[str]] = Field(None, description="푸터 행 (합계 등)")


class TableBlock(BaseModel):
    """
    일반 표 블록

    사용: 시나리오별 AAL 추이 표 등
    """
    type: Literal["table"] = "table"
    title: str = Field(..., description="표 제목")
    data: TableData = Field(..., description="표 데이터")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "table",
                "title": "시나리오별 AAL 추이",
                "data": {
                    "headers": ["시나리오", "2024", "2030", "2050", "2100"],
                    "rows": [
                        {"cells": ["SSP1-2.6", "52.9%", "51.2%", "48.1%", "45.0%"]},
                        {"cells": ["SSP2-4.5", "52.9%", "55.3%", "63.5%", "68.1%"]}
                    ]
                }
            }
        }


# ============================================================
# Heatmap Table (히트맵 표)
# ============================================================

class HeatmapCell(BaseModel):
    """히트맵 셀"""
    value: str = Field(..., description="셀 값 (예: '18.2%')")
    bg_color: Literal["gray", "yellow", "orange", "red"] = Field(..., description="배경색 (AAL 기준)")


class HeatmapRow(BaseModel):
    """히트맵 행"""
    site_name: str = Field(..., description="사업장명")
    cells: List[HeatmapCell] = Field(..., description="리스크별 AAL 셀 + Total AAL")


class LegendItem(BaseModel):
    """범례 항목"""
    color: str = Field(..., description="색상 (gray/yellow/orange/red)")
    label: str = Field(..., description="레이블 (예: '0-3% (낮음)')")


class HeatmapTableData(BaseModel):
    """히트맵 표 데이터"""
    headers: List[str] = Field(..., description="헤더 행 (사업장, 리스크1, ..., Total AAL)")
    rows: List[HeatmapRow] = Field(..., description="사업장별 데이터 행")
    legend: List[LegendItem] = Field(..., description="색상 범례")


class HeatmapTableBlock(BaseModel):
    """
    히트맵 표 블록 (색상 코딩)

    사용: 사업장별 물리적 리스크 AAL 분포 (Node 3)
    색상 기준:
    - Gray: 0-3% (낮음)
    - Yellow: 3-10% (중간)
    - Orange: 10-30% (높음)
    - Red: 30%+ (매우 높음)
    """
    type: Literal["heatmap_table"] = "heatmap_table"
    title: str = Field(..., description="표 제목")
    data: HeatmapTableData = Field(..., description="히트맵 데이터")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "heatmap_table",
                "title": "사업장별 물리적 리스크 AAL 분포",
                "data": {
                    "headers": ["사업장", "하천범람", "태풍", "도시침수", "극심한고온", "해수면상승", "Total AAL"],
                    "rows": [
                        {
                            "site_name": "서울 본사",
                            "cells": [
                                {"value": "7.2%", "bg_color": "yellow"},
                                {"value": "2.1%", "bg_color": "gray"},
                                {"value": "5.1%", "bg_color": "yellow"},
                                {"value": "2.5%", "bg_color": "gray"},
                                {"value": "0.0%", "bg_color": "gray"},
                                {"value": "16.9%", "bg_color": "orange"}
                            ]
                        }
                    ],
                    "legend": [
                        {"color": "gray", "label": "0-3% (낮음)"},
                        {"color": "yellow", "label": "3-10% (중간)"},
                        {"color": "orange", "label": "10-30% (높음)"},
                        {"color": "red", "label": "30%+ (매우 높음)"}
                    ]
                }
            }
        }


# ============================================================
# Line Chart (선 그래프)
# ============================================================

class AxisConfig(BaseModel):
    """축 설정"""
    label: str = Field(..., description="축 레이블")
    categories: Optional[List[Union[str, int]]] = Field(None, description="카테고리 (x축용)")
    min: Optional[float] = Field(None, description="최소값 (y축용)")
    max: Optional[float] = Field(None, description="최대값 (y축용)")
    unit: Optional[str] = Field(None, description="단위 (%, 억원 등)")


class SeriesData(BaseModel):
    """시리즈 데이터"""
    name: str = Field(..., description="시리즈명 (예: 'SSP1-2.6')")
    color: str = Field(..., description="색상 (hex code)")
    data: List[float] = Field(..., description="데이터 포인트")


class LineChartData(BaseModel):
    """선 그래프 데이터"""
    x_axis: AxisConfig = Field(..., description="X축 설정")
    y_axis: AxisConfig = Field(..., description="Y축 설정")
    series: List[SeriesData] = Field(..., description="시리즈 리스트")


class LineChartBlock(BaseModel):
    """
    선 그래프 블록

    사용: AAL 추이 차트 (Node 4)
    """
    type: Literal["line_chart"] = "line_chart"
    title: str = Field(..., description="차트 제목")
    data: LineChartData = Field(..., description="차트 데이터")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "line_chart",
                "title": "포트폴리오 AAL 추이 (2024-2100)",
                "data": {
                    "x_axis": {
                        "label": "연도",
                        "categories": [2024, 2030, 2040, 2050, 2100]
                    },
                    "y_axis": {
                        "label": "AAL",
                        "min": 0,
                        "max": 100,
                        "unit": "%"
                    },
                    "series": [
                        {
                            "name": "SSP1-2.6",
                            "color": "#4CAF50",
                            "data": [52.9, 51.2, 49.5, 48.1, 45.0]
                        },
                        {
                            "name": "SSP5-8.5",
                            "color": "#F44336",
                            "data": [52.9, 58.7, 67.3, 78.2, 92.5]
                        }
                    ]
                }
            }
        }


# ============================================================
# Bar Chart (막대 그래프)
# ============================================================

class BarChartData(BaseModel):
    """막대 그래프 데이터"""
    x_axis: AxisConfig = Field(..., description="X축 설정")
    y_axis: AxisConfig = Field(..., description="Y축 설정")
    series: List[SeriesData] = Field(..., description="시리즈 리스트")


class BarChartBlock(BaseModel):
    """
    막대 그래프 블록

    사용: 리스크별 AAL 비교 등
    """
    type: Literal["bar_chart"] = "bar_chart"
    title: str = Field(..., description="차트 제목")
    data: BarChartData = Field(..., description="차트 데이터")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "bar_chart",
                "title": "리스크별 AAL 비교",
                "data": {
                    "x_axis": {
                        "label": "리스크 유형",
                        "categories": ["하천범람", "태풍", "도시침수", "극심한고온", "해수면상승"]
                    },
                    "y_axis": {
                        "label": "AAL",
                        "max": 30,
                        "unit": "%"
                    },
                    "series": [
                        {
                            "name": "2024년 AAL",
                            "color": "#2196F3",
                            "data": [18.2, 11.4, 8.7, 7.3, 6.2]
                        }
                    ]
                }
            }
        }


# ============================================================
# Block Union Type
# ============================================================

Block = Union[
    TextBlock,
    TableBlock,
    HeatmapTableBlock,
    LineChartBlock,
    BarChartBlock
]


# ============================================================
# Section & Report
# ============================================================

class Section(BaseModel):
    """보고서 섹션"""
    section_id: str = Field(..., description="섹션 ID (executive_summary, governance, strategy, ...)")
    title: str = Field(..., description="섹션 제목")
    page_start: int = Field(..., description="시작 페이지")
    page_end: int = Field(..., description="종료 페이지")
    blocks: List[Block] = Field(..., description="블록 리스트")


class TableOfContents(BaseModel):
    """목차 항목"""
    title: str = Field(..., description="섹션 제목")
    page: int = Field(..., description="페이지 번호")


class ReportMeta(BaseModel):
    """보고서 메타데이터"""
    title: str = Field(..., description="보고서 제목")
    generated_at: str = Field(..., description="생성 시각 (ISO 8601)")
    llm_model: str = Field(..., description="사용 LLM 모델")
    site_count: int = Field(..., description="사업장 수")
    total_pages: int = Field(..., description="총 페이지 수")
    total_aal: float = Field(..., description="포트폴리오 총 AAL (%)")
    version: str = Field(..., description="보고서 버전")


class TCFDReport(BaseModel):
    """
    최종 TCFD 보고서 JSON 구조

    사용: Node 7 (Finalizer)에서 DB 저장
    """
    report_id: str = Field(..., description="보고서 ID")
    meta: ReportMeta = Field(..., description="메타데이터")
    table_of_contents: List[TableOfContents] = Field(..., description="목차")
    sections: List[Section] = Field(..., description="섹션 리스트")

    class Config:
        json_schema_extra = {
            "example": {
                "report_id": "tcfd_report_20251214_190000",
                "meta": {
                    "title": "TCFD 보고서",
                    "generated_at": "2025-12-14T19:00:00",
                    "llm_model": "gpt-4-1106-preview",
                    "site_count": 8,
                    "total_pages": 18,
                    "total_aal": 163.8,
                    "version": "2.0"
                },
                "table_of_contents": [
                    {"title": "Executive Summary", "page": 1},
                    {"title": "1. Governance", "page": 3}
                ],
                "sections": []
            }
        }


# ============================================================
# Helper Functions
# ============================================================

def get_heatmap_color(aal: float) -> Literal["gray", "yellow", "orange", "red"]:
    """
    AAL 값에 따른 히트맵 색상 결정

    Args:
        aal: AAL 값 (%)

    Returns:
        색상 코드 (gray/yellow/orange/red)
    """
    if aal < 3:
        return "gray"
    elif aal < 10:
        return "yellow"
    elif aal < 30:
        return "orange"
    else:
        return "red"


def create_heatmap_cell(aal: float) -> HeatmapCell:
    """
    AAL 값으로 히트맵 셀 생성

    Args:
        aal: AAL 값 (%)

    Returns:
        HeatmapCell 객체
    """
    return HeatmapCell(
        value=f"{aal:.1f}%",
        bg_color=get_heatmap_color(aal)
    )
