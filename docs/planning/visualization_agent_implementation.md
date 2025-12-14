# Visualization Agent 구현 계획

**작성일**: 2025-12-13
**버전**: v1.0
**상태**: Planning (보류 중)

---

## 1. 개요

### 1.1 목적
TCFD 보고서 내에 표, 그래프, 히트맵 등 시각화 자료를 자동으로 생성하여 삽입

### 1.2 요구사항 (SK 보고서 기준)
- **테이블**: 20+ 개 (SSP 시나리오 비교표, 리스크 분류표, 비용 시나리오 등)
- **그래프**: 10+ 개 (탄소가격 추이, 배출량 추이, AAL 추이 등)
- **다이어그램**: 5+ 개 (거버넌스 구조도, 프로세스 플로우)

---

## 2. 구현 방식 비교

### Option 1: Python 라이브러리 기반 (권장 ✅)

**장점**:
- 완전 자동화 가능
- 데이터 → 이미지 파이프라인 구축
- Markdown/PDF 변환과 호환성 좋음

**단점**:
- 초기 개발 비용 높음
- 스타일 커스터마이징 복잡

**기술 스택**:
```python
# 1. 테이블 → Markdown Table
import pandas as pd

# 2. 그래프 생성
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

# 3. 다이어그램 생성
from graphviz import Digraph
import mermaid  # Mermaid.js Python wrapper
```

**워크플로우**:
```
ModelOps 데이터 (DB)
  ↓
VisualizationAgent
  ↓
  ├─ Table Generator → Markdown Table
  ├─ Chart Generator → PNG/SVG
  └─ Diagram Generator → PNG/SVG
  ↓
Report Composer
  ↓
Markdown (with images)
  ↓
PDF Converter
```

---

### Option 2: LLM 생성 코드 실행

**장점**:
- 유연성 높음 (사용자 요청에 맞춘 시각화)
- 코드 생성 → 실행 → 이미지 저장

**단점**:
- 보안 리스크 (Code Execution)
- 불안정성 (LLM이 잘못된 코드 생성 가능)

**워크플로우**:
```
Validation Agent 결과
  ↓
LLM (GPT-4) → "다음 데이터를 matplotlib로 시각화하세요"
  ↓
Python 코드 생성
  ↓
Sandbox 환경에서 코드 실행 (Docker/PyPy)
  ↓
이미지 파일 생성
  ↓
Report Composer에 삽입
```

---

### Option 3: Pre-built Template 기반

**장점**:
- 안정적 (미리 정의된 템플릿)
- 빠른 구현

**단점**:
- 유연성 낮음
- 새로운 시각화 추가 시 템플릿 수정 필요

**워크플로우**:
```
Template Library:
- template_1: SSP 시나리오 히트맵
- template_2: NGFS 탄소가격 추이 그래프
- template_3: 거버넌스 구조도
  ↓
VisualizationAgent가 적절한 템플릿 선택
  ↓
데이터 바인딩
  ↓
이미지 생성
```

---

## 3. 권장 구현: Option 1 (Python 라이브러리)

### 3.1 VisualizationAgent 구조

```python
# polaris_backend_fastapi/ai_agent/agents/report_generation/visualization_agent_8.py

from typing import Dict, Any, List
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pathlib import Path

class VisualizationAgent:
    """
    보고서 시각화 에이전트

    기능:
    1. Table Generator: Markdown 테이블 생성
    2. Chart Generator: 그래프 생성 (matplotlib/seaborn)
    3. Diagram Generator: 다이어그램 생성 (graphviz/mermaid)
    """

    def __init__(self, output_dir: str = "reports/images"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def generate_visualizations(
        self,
        report_data: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """
        보고서 데이터로부터 시각화 생성

        Args:
            report_data: 보고서 데이터 (impact_analysis, strategies 등)

        Returns:
            {
                'tables': [markdown_table_1, markdown_table_2, ...],
                'charts': ['path/to/chart1.png', 'path/to/chart2.png', ...],
                'diagrams': ['path/to/diagram1.png', ...]
            }
        """
        visualizations = {
            'tables': [],
            'charts': [],
            'diagrams': []
        }

        # 1. 테이블 생성
        visualizations['tables'].extend(
            self._generate_tables(report_data)
        )

        # 2. 그래프 생성
        visualizations['charts'].extend(
            self._generate_charts(report_data)
        )

        # 3. 다이어그램 생성
        visualizations['diagrams'].extend(
            self._generate_diagrams(report_data)
        )

        return visualizations

    # ================================================================
    # Table Generators
    # ================================================================

    def _generate_tables(self, report_data: Dict) -> List[str]:
        """Markdown 테이블 생성"""
        tables = []

        # Table 1: SSP 시나리오 비교표
        tables.append(self._create_ssp_comparison_table(report_data))

        # Table 2: 리스크별 AAL 비교표
        tables.append(self._create_aal_comparison_table(report_data))

        # Table 3: 대응 전략 요약표
        tables.append(self._create_strategy_summary_table(report_data))

        return tables

    def _create_ssp_comparison_table(self, data: Dict) -> str:
        """SSP 시나리오별 물리적 리스크 히트맵"""

        # 데이터 추출
        scenarios = ['SSP1-2.6', 'SSP2-4.5', 'SSP3-7.0', 'SSP5-8.5']
        risks = [
            'Extreme Heat',
            'Extreme Cold',
            'Drought',
            'River Flood',
            'Urban Flood',
            'Sea Level Rise',
            'Typhoon',
            'Wildfire',
            'Water Stress'
        ]

        # Markdown 테이블 생성
        table = "| Risk Type | SSP1-2.6 | SSP2-4.5 | SSP3-7.0 | SSP5-8.5 |\n"
        table += "|-----------|----------|----------|----------|----------|\n"

        for risk in risks:
            row = f"| {risk} |"
            for scenario in scenarios:
                score = data.get('impact_analysis', {}).get(scenario, {}).get(risk, 50)
                level = self._score_to_level(score)
                row += f" {level} ({score:.1f}) |"
            table += row + "\n"

        return table

    def _score_to_level(self, score: float) -> str:
        """점수 → 레벨 변환 (색상 표시용)"""
        if score >= 80:
            return "🔴 Very High"
        elif score >= 60:
            return "🟠 High"
        elif score >= 40:
            return "🟡 Medium"
        elif score >= 20:
            return "🟢 Low"
        else:
            return "⚪ Very Low"

    def _create_aal_comparison_table(self, data: Dict) -> str:
        """리스크별 AAL 비교표"""

        table = "| Risk Type | AAL (%) | Expected Loss (KRW) | Severity |\n"
        table += "|-----------|---------|---------------------|----------|\n"

        aal_data = data.get('impact_analysis', {}).get('aal_values', {})

        for risk, aal in aal_data.items():
            expected_loss = aal * data.get('asset_value', 10_000_000_000)  # 100억 기본값
            severity = self._aal_to_severity(aal)

            table += f"| {risk} | {aal*100:.2f}% | {expected_loss:,.0f} | {severity} |\n"

        return table

    def _aal_to_severity(self, aal: float) -> str:
        """AAL → 심각도"""
        if aal >= 0.05:
            return "Critical"
        elif aal >= 0.03:
            return "High"
        elif aal >= 0.01:
            return "Moderate"
        else:
            return "Low"

    def _create_strategy_summary_table(self, data: Dict) -> str:
        """대응 전략 요약표"""

        table = "| Risk Type | Strategy | Investment Priority | Timeline |\n"
        table += "|-----------|----------|---------------------|----------|\n"

        strategies = data.get('response_strategy', [])

        for strategy in strategies:
            risk = strategy.get('risk', 'Unknown')
            summary = strategy.get('strategy_summary', '')
            priority = strategy.get('priority', 'Medium')
            timeline = strategy.get('timeline', 'Mid-term')

            table += f"| {risk} | {summary[:50]}... | {priority} | {timeline} |\n"

        return table

    # ================================================================
    # Chart Generators
    # ================================================================

    def _generate_charts(self, report_data: Dict) -> List[str]:
        """그래프 생성"""
        chart_paths = []

        # Chart 1: NGFS 탄소가격 추이
        chart_paths.append(
            self._create_carbon_price_chart(report_data)
        )

        # Chart 2: SSP별 AAL 추이
        chart_paths.append(
            self._create_aal_trend_chart(report_data)
        )

        # Chart 3: 리스크 포트폴리오 히트맵
        chart_paths.append(
            self._create_risk_heatmap(report_data)
        )

        return chart_paths

    def _create_carbon_price_chart(self, data: Dict) -> str:
        """NGFS 시나리오별 탄소가격 추이 그래프"""

        # 데이터 준비
        years = [2025, 2030, 2035, 2040, 2045, 2050]
        scenarios = {
            'Current Policies': [30, 40, 45, 50, 55, 60],
            'Delayed Transition': [30, 50, 80, 120, 150, 180],
            'Net Zero 2050': [30, 90, 120, 160, 200, 250]
        }

        # 그래프 생성
        plt.figure(figsize=(10, 6))

        for scenario, prices in scenarios.items():
            plt.plot(years, prices, marker='o', label=scenario, linewidth=2)

        plt.title('NGFS Carbon Price Projections (South Korea)', fontsize=14, fontweight='bold')
        plt.xlabel('Year', fontsize=12)
        plt.ylabel('Carbon Price (USD/tCO₂eq)', fontsize=12)
        plt.legend(loc='upper left', fontsize=10)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        # 저장
        output_path = self.output_dir / 'carbon_price_trend.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        return str(output_path)

    def _create_aal_trend_chart(self, data: Dict) -> str:
        """SSP별 AAL 추이 그래프"""

        # 데이터 준비
        years = [2030, 2040, 2050]
        scenarios = {
            'SSP1-2.6': [0.5, 0.6, 0.7],
            'SSP2-4.5': [0.6, 0.8, 1.0],
            'SSP3-7.0': [0.7, 1.2, 1.8],
            'SSP5-8.5': [0.8, 1.5, 2.5]
        }

        # 그래프 생성
        plt.figure(figsize=(10, 6))

        for scenario, aal_values in scenarios.items():
            plt.plot(years, aal_values, marker='s', label=scenario, linewidth=2)

        plt.title('Average Annual Loss (AAL) Projections by SSP Scenario', fontsize=14, fontweight='bold')
        plt.xlabel('Year', fontsize=12)
        plt.ylabel('AAL (% of Asset Value)', fontsize=12)
        plt.legend(loc='upper left', fontsize=10)
        plt.grid(True, alpha=0.3)
        plt.axhline(y=3.0, color='red', linestyle='--', alpha=0.5, label='High Risk Threshold (3%)')
        plt.tight_layout()

        # 저장
        output_path = self.output_dir / 'aal_trend_by_ssp.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        return str(output_path)

    def _create_risk_heatmap(self, data: Dict) -> str:
        """리스크 포트폴리오 히트맵"""

        # 데이터 준비
        risks = ['Heat', 'Cold', 'Drought', 'River Flood', 'Urban Flood',
                'Sea Rise', 'Typhoon', 'Wildfire', 'Water Stress']
        scenarios = ['SSP1-2.6', 'SSP2-4.5', 'SSP3-7.0', 'SSP5-8.5']

        # 샘플 데이터 (실제로는 data에서 추출)
        import numpy as np
        risk_scores = np.random.randint(20, 90, size=(len(risks), len(scenarios)))

        # 히트맵 생성
        plt.figure(figsize=(10, 8))
        sns.heatmap(
            risk_scores,
            annot=True,
            fmt='d',
            cmap='YlOrRd',
            xticklabels=scenarios,
            yticklabels=risks,
            cbar_kws={'label': 'Risk Score (0-100)'}
        )

        plt.title('Physical Risk Heatmap by SSP Scenario', fontsize=14, fontweight='bold')
        plt.xlabel('SSP Scenario', fontsize=12)
        plt.ylabel('Risk Type', fontsize=12)
        plt.tight_layout()

        # 저장
        output_path = self.output_dir / 'risk_heatmap.png'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

        return str(output_path)

    # ================================================================
    # Diagram Generators
    # ================================================================

    def _generate_diagrams(self, report_data: Dict) -> List[str]:
        """다이어그램 생성"""
        diagram_paths = []

        # Diagram 1: 거버넌스 구조도
        diagram_paths.append(
            self._create_governance_diagram()
        )

        # Diagram 2: 리스크 관리 프로세스
        diagram_paths.append(
            self._create_risk_process_diagram()
        )

        return diagram_paths

    def _create_governance_diagram(self) -> str:
        """거버넌스 구조도 (Mermaid)"""

        mermaid_code = """
        graph TD
            A[Board of Directors] --> B[Strategy & ESG Committee]
            B --> C[CEO]
            C --> D[CFO]
            C --> E[CSO Chief Sustainability Officer]
            E --> F[Climate Risk Management Team]
            F --> G[Site Managers]
            F --> H[Supply Chain Team]

            style A fill:#e1f5ff
            style B fill:#b3e0ff
            style C fill:#80ccff
            style E fill:#4db8ff
            style F fill:#1a9fff
        """

        # Mermaid → PNG 변환 (mermaid-cli 필요)
        # 간단히 mermaid 코드만 저장
        output_path = self.output_dir / 'governance_structure.mmd'
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(mermaid_code)

        return str(output_path)

    def _create_risk_process_diagram(self) -> str:
        """리스크 관리 프로세스 다이어그램"""

        mermaid_code = """
        graph LR
            A[1. Risk Identification] --> B[2. Risk Assessment]
            B --> C[3. Risk Response]
            C --> D[4. Monitoring & Reporting]
            D --> A

            B --> E[H × E × V Calculation]
            E --> F[AAL Estimation]
            F --> C

            style A fill:#ffcccc
            style B fill:#ffe6cc
            style C fill:#ffffcc
            style D fill:#ccffcc
        """

        output_path = self.output_dir / 'risk_management_process.mmd'
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(mermaid_code)

        return str(output_path)


# ================================================================
# Integration with Report Composer
# ================================================================

async def integrate_visualizations_into_report(
    draft_markdown: str,
    visualizations: Dict[str, List[str]]
) -> str:
    """
    시각화를 Markdown 보고서에 삽입

    Args:
        draft_markdown: 초안 Markdown
        visualizations: VisualizationAgent 출력

    Returns:
        시각화가 삽입된 최종 Markdown
    """

    # 1. 테이블 삽입
    for i, table in enumerate(visualizations['tables']):
        placeholder = f"{{{{TABLE_{i+1}}}}}"
        draft_markdown = draft_markdown.replace(placeholder, table)

    # 2. 그래프 삽입
    for i, chart_path in enumerate(visualizations['charts']):
        placeholder = f"{{{{CHART_{i+1}}}}}"
        markdown_image = f"![Chart {i+1}]({chart_path})"
        draft_markdown = draft_markdown.replace(placeholder, markdown_image)

    # 3. 다이어그램 삽입
    for i, diagram_path in enumerate(visualizations['diagrams']):
        placeholder = f"{{{{DIAGRAM_{i+1}}}}}"
        markdown_image = f"![Diagram {i+1}]({diagram_path})"
        draft_markdown = draft_markdown.replace(placeholder, markdown_image)

    return draft_markdown
```

---

## 4. Workflow 통합

### 4.1 기존 Workflow (v07)

```
Report Template → Impact Analysis → Strategy Generation → Report Composer → Validation → Refiner → Finalization
```

### 4.2 새 Workflow (v08 - Visualization 추가)

```
Report Template
  ↓
Impact Analysis
  ↓
Strategy Generation
  ↓
Report Composer (Draft with Placeholders)
  ↓
Visualization Agent (Tables/Charts/Diagrams 생성) ← 새로 추가
  ↓
Report Integration (Draft + Visualizations 병합)
  ↓
Validation
  ↓
Refiner
  ↓
Finalization
```

### 4.3 Graph 수정

```python
# polaris_backend_fastapi/ai_agent/workflow/graph.py

# 노드 추가
workflow.add_node('visualization', lambda state: visualization_node(state, config))

# 엣지 수정
workflow.add_edge('report_generation', 'visualization')  # Composer → Visualization
workflow.add_edge('visualization', 'validation')         # Visualization → Validation
```

---

## 5. 데이터 출처

### 5.1 Table 데이터
- `impact_analysis`: H×E×V 계산 결과
- `aal_values`: AAL 스케일링 결과
- `response_strategy`: 전략 생성 결과

### 5.2 Chart 데이터
- **NGFS 탄소가격**: 외부 데이터 (IEA, NGFS 시나리오)
- **AAL 추이**: ModelOps 계산 결과
- **리스크 히트맵**: `hazard_results`, `vulnerability_results`

### 5.3 Diagram 데이터
- **거버넌스 구조**: 고정 템플릿
- **프로세스 플로우**: 고정 템플릿

---

## 6. 출력 형식

### 6.1 Markdown 통합 예시

```markdown
## 2. Strategy

### 2.2 Scenario Analysis

#### 2.2.1 Transition Risk Scenarios

**NGFS Carbon Price Projections**

![NGFS Carbon Price Trend](reports/images/carbon_price_trend.png)

Based on NGFS scenarios, South Korea's carbon prices are projected to:
- Current Policies: USD 60/tCO₂eq by 2050
- Delayed Transition: USD 180/tCO₂eq by 2050
- Net Zero 2050: USD 250/tCO₂eq by 2050

#### 2.2.2 Physical Risk Scenarios

**SSP Scenario Comparison**

| Risk Type | SSP1-2.6 | SSP2-4.5 | SSP3-7.0 | SSP5-8.5 |
|-----------|----------|----------|----------|----------|
| Extreme Heat | 🟡 Medium (42.3) | 🟠 High (65.7) | 🟠 High (78.9) | 🔴 Very High (89.2) |
| River Flood | 🟢 Low (25.1) | 🟡 Medium (35.4) | 🟡 Medium (45.8) | 🟠 High (62.3) |

**Average Annual Loss (AAL) Projections**

![AAL Trend](reports/images/aal_trend_by_ssp.png)

All facilities show AAL < 3% under SSP1-2.6 and SSP2-4.5, indicating manageable risk.
```

### 6.2 PDF 변환
Markdown → PDF 변환 시 이미지 포함:
- `pandoc` 또는 `weasyprint` 사용
- 이미지 경로 자동 해결

---

## 7. 구현 순서

### Phase 1: 기본 구조 (1-2일)
1. `VisualizationAgent` 클래스 생성
2. Table Generator 구현 (3종)
3. Workflow 통합

### Phase 2: Chart Generator (2-3일)
1. NGFS 탄소가격 그래프
2. AAL 추이 그래프
3. 리스크 히트맵

### Phase 3: Diagram Generator (1-2일)
1. 거버넌스 구조도 (Mermaid)
2. 리스크 프로세스 (Mermaid)
3. Mermaid → PNG 변환 (optional)

### Phase 4: 통합 테스트 (1일)
1. 전체 워크플로우 실행
2. 이미지 경로 검증
3. PDF 변환 테스트

---

## 8. 기술적 제약사항

### 8.1 의존성
```bash
pip install matplotlib seaborn pandas graphviz
npm install -g @mermaid-js/mermaid-cli  # Mermaid → PNG 변환 (optional)
```

### 8.2 성능
- 그래프 생성: ~1초/차트
- 테이블 생성: ~0.1초/테이블
- 전체: ~5초 추가 소요

### 8.3 저장 공간
- 이미지 파일: ~500KB/차트
- 보고서당 ~5MB 예상

---

## 9. 대안: 간단한 구현 (Quick Win)

**Phase 0: Markdown Table만 우선 구현**
- Chart/Diagram은 나중에 추가
- Table Generator만 먼저 구현 (1일)
- 기존 Workflow에 바로 통합 가능

```python
# 간단한 Table만 생성
class SimpleTableGenerator:
    def create_ssp_table(self, data):
        return "| Risk | SSP1 | SSP2 | SSP3 | SSP5 |\n|-----|------|------|------|------|\n..."
```

---

## 10. 성공 지표

### 정량적
- [ ] 테이블: 5+ 개
- [ ] 그래프: 3+ 개
- [ ] 다이어그램: 2+ 개
- [ ] 보고서 페이지: 5+ 페이지 (시각화 포함)

### 정성적
- [ ] SK 보고서 수준의 시각화 품질
- [ ] Markdown → PDF 변환 시 이미지 정상 표시
- [ ] 데이터 출처 명확

---

## 11. 다음 단계

1. **우선순위 결정**
   - 현재 Phase 1 (내용 품질) 완료 후 착수
   - 또는 병행 개발 (별도 팀)

2. **POC 구현**
   - Table Generator부터 시작
   - 1개 테이블로 E2E 테스트

3. **사용자 피드백**
   - 어떤 시각화가 필요한지 명확히
   - SK 보고서 벤치마킹 심화

---

**작성자**: AI Agent
**검토 필요**: ModelOps Team, FastAPI Team
