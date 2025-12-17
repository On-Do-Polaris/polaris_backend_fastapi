"""
TCFD Report JSON Schema Definitions
프론트엔드 JSON 포맷 표준화를 위한 Pydantic 스키마

작성일: 2025-12-16
버전: v2.0
"""

from typing import Literal, List, Optional, Union, Dict, Any
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
    subheading: Optional[str] = Field(None, description="소제목 (목차 포함 시 설정, 없으면 목차에서 제외)")
    content: str = Field(..., description="본문 내용 (Markdown 또는 Plain Text)")

    class Config:
        # None 값인 필드는 JSON에서 제외
        exclude_none = True
        json_schema_extra = {
            "examples": [
                {
                    "type": "text",
                    "subheading": "1.1 이사회의 감독",
                    "content": "이사회는 기후 관련 리스크 및 기회에 대한..."
                },
                {
                    "type": "text",
                    "content": "소제목 없는 단순 텍스트 블록입니다."
                }
            ]
        }


# ============================================================
# Table Block (히트맵 스타일 포함)
# ============================================================

class TableHeader(BaseModel):
    """표 헤더"""
    text: str = Field(..., description="헤더 텍스트")
    value: str = Field(..., description="데이터 키")


class TableCellValue(BaseModel):
    """표 셀 값 (색상 코딩 포함)"""
    value: str = Field(..., description="셀 값 (예: '15.2%')")
    bg_color: Optional[str] = Field(None, description="배경색 (gray/yellow/orange/red)")


class LegendItem(BaseModel):
    """범례 항목"""
    color: str = Field(..., description="색상 (gray/yellow/orange/red)")
    label: str = Field(..., description="레이블 (예: '0-3% (낮음)')")


class TableBlock(BaseModel):
    """
    표 블록 (일반 표 + 히트맵 표)

    사용: 
    - 사업장별 AAL 히트맵
    - 시나리오별 데이터 표
    - 리스크 대응 전략 표
    
    히트맵 색상 기준:
    - gray: 0-3% (낮음)
    - yellow: 3-10% (중간)
    - orange: 10-30% (높음)
    - red: 30%+ (매우 높음)
    """
    type: Literal["table"] = "table"
    title: str = Field(..., description="표 제목")
    subheading: Optional[str] = Field(None, description="소제목 (목차 포함 시 설정, 없으면 목차에서 제외)")
    headers: List[TableHeader] = Field(..., description="헤더 리스트")
    items: List[Dict[str, Union[str, TableCellValue]]] = Field(..., description="데이터 행 리스트")
    legend: Optional[List[LegendItem]] = Field(None, description="색상 범례 (히트맵 표의 경우 필수)")

    class Config:
        # None 값인 필드는 JSON에서 제외
        exclude_none = True
        json_schema_extra = {
            "examples": [
                {
                    "type": "table",
                    "title": "사업장별 물리적 리스크 AAL 분포",
                    "subheading": "2.1 사업장별 AAL 히트맵",
                    "headers": [
                        {"text": "사업장", "value": "site"},
                        {"text": "HEAT_WAVE", "value": "heat_wave"},
                        {"text": "TYPHOON", "value": "typhoon"}
                    ],
                    "items": [
                        {
                            "site": "SK 판교캠퍼스",
                            "heat_wave": {"value": "15.2%", "bg_color": "orange"},
                            "typhoon": {"value": "2.1%", "bg_color": "gray"}
                        }
                    ],
                    "legend": [
                        {"color": "gray", "label": "0-3% (낮음)"},
                        {"color": "yellow", "label": "3-10% (중간)"},
                        {"color": "orange", "label": "10-30% (높음)"},
                        {"color": "red", "label": "30%+ (매우 높음)"}
                    ]
                },
                {
                    "type": "table",
                    "title": "시나리오별 AAL 추이",
                    "headers": [
                        {"text": "시나리오", "value": "scenario"},
                        {"text": "2024", "value": "year_2024"},
                        {"text": "2050", "value": "year_2050"}
                    ],
                    "items": [
                        {
                            "scenario": "SSP1-2.6",
                            "year_2024": "52.9%",
                            "year_2050": "48.1%"
                        }
                    ]
                }
            ]
        }


# ============================================================
# TableData / TableRow (Node 2-A 호환)
# ============================================================

class TableRow(BaseModel):
    """표 행 데이터"""
    cells: List[str] = Field(..., description="셀 값 리스트")


class TableData(BaseModel):
    """표 데이터 (Node 2-A 형식)"""
    headers: List[str] = Field(..., description="헤더 리스트")
    rows: List[TableRow] = Field(..., description="행 리스트")


# ============================================================
# Block Union Type
# ============================================================

Block = Union[TextBlock, TableBlock]


# ============================================================
# Section & Report
# ============================================================

class Section(BaseModel):
    """보고서 섹션"""
    section_id: str = Field(..., description="섹션 ID (governance, strategy, risk_management, metrics)")
    title: str = Field(..., description="섹션 제목")
    blocks: List[Block] = Field(..., description="블록 리스트")


class ReportMeta(BaseModel):
    """보고서 메타데이터"""
    title: str = Field(..., description="보고서 제목")


class TCFDReport(BaseModel):
    """
    최종 TCFD 보고서 JSON 구조 (프론트엔드 전달용)

    사용: FastAPI 응답
    """
    report_id: str = Field(..., description="보고서 ID")
    meta: ReportMeta = Field(..., description="메타데이터")
    sections: List[Section] = Field(..., description="섹션 리스트")

    class Config:
        json_schema_extra = {
            "example": {
                "report_id": "tcfd_report_20251216_163321",
                "meta": {
                    "title": "TCFD 보고서"
                },
                "sections": []
            }
        }


# ============================================================
# Utility Functions
# ============================================================

def get_heatmap_color(aal: float) -> str:
    """
    AAL 값에 따른 히트맵 색상 반환 (5-tier 등급)

    Args:
        aal: AAL 값 (%)

    Returns:
        str: 색상 코드 ("lightgray", "yellow", "orange", "red", "darkred")

    색상 기준:
        - lightgray: 0-3% (매우 낮음)
        - yellow: 3-10% (낮음)
        - orange: 10-20% (중간)
        - red: 20-30% (높음)
        - darkred: 30%+ (매우 높음)
    """
    if aal >= 30:
        return "darkred"
    elif aal >= 20:
        return "red"
    elif aal >= 10:
        return "orange"
    elif aal >= 3:
        return "yellow"
    else:
        return "lightgray"
