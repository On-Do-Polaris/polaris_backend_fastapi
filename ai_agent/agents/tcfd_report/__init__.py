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

from .node_0_data_preprocessing import DataPreprocessingNode
from .node_1_template_loading import TemplateLoadingNode
from .node_2a_scenario_analysis import ScenarioAnalysisNode
from .node_2b_impact_analysis import ImpactAnalysisNode
from .node_2c_mitigation_strategies import MitigationStrategiesNode
from .node_3_strategy_section import StrategySectionNode
from .node_4_validator import ValidatorNode
from .node_5_composer import ComposerNode
from .node_6_finalizer import FinalizerNode
from .workflow import create_tcfd_workflow, TCFDReportState
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
    # Nodes (7개)
    "DataPreprocessingNode",
    "TemplateLoadingNode",
    "ScenarioAnalysisNode",
    "ImpactAnalysisNode",
    "MitigationStrategiesNode",
    "StrategySectionNode",
    "ValidatorNode",
    "ComposerNode",
    "FinalizerNode",
    # Workflow
    "create_tcfd_workflow",
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
