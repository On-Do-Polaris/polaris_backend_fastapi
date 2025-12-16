"""
TCFD Report Generation Agents v2.1
7-Node Refactoring (항목별 순차 분석 구조: Scenario → Impact → Mitigation)

작성일: 2025-12-15
설계 문서: docs/planning/report_plan_v3.md

노드 통합 (v2.0 → v2.1):
- 구 Node 4, 5, 6, 8 → 신 Node 5 (Composer)로 통합
- 구 Node 7 → 신 Node 4 (Validator)
- 구 Node 9 → 신 Node 6 (Finalizer)
"""

# Lazy import를 위해 개별 노드 import는 주석 처리
# 필요 시 직접 import 사용: from ai_agent.agents.tcfd_report.node_0_data_preprocessing import DataPreprocessingNode

from .state import TCFDReportState
from .schemas import (
    TextBlock,
    TableBlock,
    HeatmapTableBlock,
    LineChartBlock,
    BarChartBlock,
    Section,
    TableOfContents,
    TCFDReport
)

__all__ = [
    # State
    "TCFDReportState",
    # Schemas
    "TextBlock",
    "TableBlock",
    "HeatmapTableBlock",
    "LineChartBlock",
    "BarChartBlock",
    "Section",
    "TableOfContents",
    "TCFDReport",
]
