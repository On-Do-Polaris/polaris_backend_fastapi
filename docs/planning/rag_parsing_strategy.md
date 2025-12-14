# RAG 파싱 및 출력 형식 전략

**작성일**: 2025-12-12
**버전**: v1.0
**목적**: LlamaParse를 활용한 효율적인 문서 파싱 전략 및 보고서 출력 형식 설계

---

## 1. LlamaParse 파싱 전략

### 1.1 Free Tier 사용량 관리

**제약사항**:
- LlamaParse Free Tier: 1,000 pages/month
- **사용 후 제한**: 추가 파싱 불가

**전략**:
- ✅ **초기 한 번만 파싱**: 문서 변경 없으면 재파싱하지 않음
- ✅ **필수 문서만 파싱**: TCFD 권고안, S&P 보고서만
- ✅ **파싱 결과 캐싱**: JSON/Pickle로 로컬 저장 → 재사용

### 1.2 파싱 대상 문서

| 문서 | 경로 | 예상 페이지 수 | 우선순위 |
|------|------|---------------|---------|
| TCFD 권고안 | `각종 자료/For_RAG/FINAL-2017-TCFD-Report.pdf` | ~80 pages | HIGH |
| S&P Climanomics | `각종 자료/For_RAG/SnP_Climanomics_PangyoDC_Summary_Report_SK C&C_2024-02-08.pdf` | ~30 pages | HIGH |
| **합계** | | **~110 pages** | |

**사용량 체크**: 110 pages < 1,000 pages/month → ✅ 안전

### 1.3 파싱 전략: 단계별 접근

#### Option 1: 전체 문서 파싱 (추천)
```
장점:
- 한 번에 모든 컨텍스트 확보
- RAG 검색 품질 최대화
- 재파싱 불필요

단점:
- 초기 파싱 시간 소요 (10-15분 예상)
- 110 pages 사용

추천 이유:
- Free tier 충분 (1,000 pages/month)
- 서비스 시작 후 재파싱 필요 없음
- 한 번의 초기 투자로 장기간 활용
```

#### Option 2: 섹션별 선택적 파싱
```
장점:
- 사용량 최소화 (~50 pages)
- 파싱 시간 단축

단점:
- 필요한 섹션 수동 선택 필요
- 컨텍스트 누락 가능성
- 추후 추가 파싱 시 사용량 증가

비추천 이유:
- Free tier 충분하므로 굳이 제한할 필요 없음
```

#### ✅ **최종 선택: Option 1 (전체 문서 파싱)**

### 1.4 파싱 모드 선택

LlamaParse는 여러 result_type 지원:

| Result Type | 설명 | 장점 | 단점 |
|-------------|------|------|------|
| `"text"` | 순수 텍스트 | 빠름, 가벼움 | 구조 정보 손실 |
| `"markdown"` | Markdown 형식 | 구조 보존, 테이블 지원 | 복잡한 레이아웃 일부 손실 |
| `"json"` | JSON 구조화 | 메타데이터 풍부 | 파싱 느림 |

**✅ 추천: `result_type="markdown"`**
- 이유:
  - 테이블이 Markdown table로 변환 → 그대로 보고서에 삽입 가능
  - 섹션 구조 보존 (heading 유지)
  - RAG 임베딩 시 읽기 쉬움
  - JSON보다 가벼움

### 1.5 테이블/그림 처리 전략

#### 테이블
```python
# LlamaParse는 테이블을 Markdown table로 변환
# 예시:
"""
| Scenario | SSP1-2.6 | SSP2-4.5 | SSP5-8.5 |
|----------|----------|----------|----------|
| Extreme Heat | Low | Medium | High |
| River Flood | Low | Medium | High |
"""

# Qdrant 저장 시:
# 1. 전체 Markdown 텍스트 → 일반 컬렉션
# 2. 테이블 발견 시 → table_name, columns, rows 추출 → 별도 메타데이터
```

#### 그림/차트
```python
# LlamaParse는 이미지를 텍스트 설명으로 변환 (OCR + Vision)
# 예시:
"""
[Figure 3.2: NGFS Scenario Carbon Price Projections]
Graph showing carbon price trends from 2020 to 2050 across three scenarios:
- Current Policies: gradual increase to $67/tCO2
- Delayed Transition: sharp rise after 2030 to $110/tCO2
- Net Zero 2050: steady climb to $160/tCO2
"""

# 우리 보고서에는:
# → 텍스트 설명만 포함 (실제 그래프 생성은 VisualizationAgent 구현 시)
```

### 1.6 파싱 결과 저장 전략

#### 로컬 캐싱
```
폴더 구조:
polaris_backend_fastapi/
├── data/
│   ├── parsed_docs/
│   │   ├── tcfd_report_parsed.json
│   │   ├── sp_climanomics_parsed.json
│   │   └── parsing_metadata.json  # 파싱 날짜, 버전 정보

이점:
- 재파싱 방지
- 오프라인 개발 가능
- Git에는 .gitignore 처리
```

#### Qdrant 저장 구조
```python
# Collection 1: tcfd_documents (일반 문서)
{
    "collection_name": "tcfd_documents",
    "vectors": [...],  # all-MiniLM-L6-v2 임베딩
    "payloads": [
        {
            "text": "...",  # 청크 텍스트
            "source": "FINAL-2017-TCFD-Report.pdf",
            "page": 12,
            "section": "Strategy",
            "doc_type": "tcfd_guideline"
        }
    ]
}

# Collection 2: tcfd_tables (테이블 전용)
{
    "collection_name": "tcfd_tables",
    "vectors": [...],  # 테이블 제목/컨텍스트 임베딩
    "payloads": [
        {
            "table_markdown": "| ... | ... |\n|-----|-----|",
            "table_summary": "SSP scenario physical risk heatmap",
            "source": "SK_TCFD_Report.pdf",
            "page": 32
        }
    ]
}
```

---

## 2. 보고서 출력 형식 전략

### 2.1 현재 요구사항

1. **DB 저장**: JSON/JSONB 형식
2. **최종 제공**: PDF
3. **중간 형식**: 표/그래프 포함 방법 고민 중

### 2.2 제안: Markdown 중심 Hybrid 전략

```
생성 흐름:
1. Report Composer Agent → Markdown 생성
2. JSON 구조에 Markdown 저장 + 테이블/메타데이터 추가
3. DB 저장 (JSONB)
4. PDF 변환 (Markdown → HTML → PDF)
```

### 2.3 JSON/JSONB 저장 구조

#### reports 테이블 (기존)
```sql
CREATE TABLE reports (
    id UUID PRIMARY KEY,
    site_id VARCHAR,
    created_at TIMESTAMP,
    report_content JSONB,  -- 여기에 전체 보고서 저장
    status VARCHAR
);
```

#### report_content JSONB 구조 (제안)
```json
{
    "metadata": {
        "generated_at": "2025-12-12T10:30:00Z",
        "version": "v2.0",
        "agent_version": "workflow_v07",
        "language": "en",
        "page_count": 6
    },
    "sections": [
        {
            "id": "executive_summary",
            "title": "Executive Summary",
            "order": 1,
            "content_markdown": "# Executive Summary\n\nThis report assesses...",
            "content_type": "text"
        },
        {
            "id": "governance",
            "title": "Governance",
            "order": 2,
            "subsections": [
                {
                    "id": "board_oversight",
                    "title": "Board Oversight",
                    "content_markdown": "## Board Oversight\n\nThe Board...",
                    "content_type": "text"
                }
            ]
        },
        {
            "id": "strategy_scenario_analysis",
            "title": "Scenario Analysis",
            "order": 3.2,
            "content_markdown": "### Scenario Analysis\n\nThe following table...",
            "content_type": "mixed",
            "tables": [
                {
                    "table_id": "transition_risk_table",
                    "caption": "Transition Risk Assessment",
                    "markdown": "| Risk ID | Type | Impact |\n|---------|------|--------|\n| T1 | Policy | High |",
                    "data": {
                        "headers": ["Risk ID", "Type", "Impact"],
                        "rows": [
                            ["T1", "Policy", "High"],
                            ["T3", "Policy", "High"]
                        ]
                    }
                }
            ]
        },
        {
            "id": "metrics",
            "title": "Metrics and Targets",
            "order": 4,
            "content_markdown": "## Metrics and Targets\n\n### Scope 1+2 Emissions...",
            "content_type": "text"
        }
    ],
    "full_markdown": "# TCFD Climate Risk Assessment Report\n\n## Executive Summary\n...\n\n## 1. Governance\n...",
    "raw_data": {
        "hazard_scores": {"extreme_heat": 67.2, ...},
        "aal_values": {"extreme_heat": 2.3, ...},
        "scenarios": ["NGFS_NZE_2050", "SSP5-8.5"]
    }
}
```

**장점**:
- ✅ Markdown → DB 저장 → 재사용 가능
- ✅ 테이블을 Markdown + 구조화 데이터 이중 저장 → 유연성
- ✅ PDF 생성 시 `full_markdown` 사용
- ✅ 웹 UI에서는 `sections` 파싱하여 동적 렌더링 가능

### 2.4 PDF 생성 전략

#### Option 1: Markdown → HTML → PDF (weasyprint)
```python
import markdown
from weasyprint import HTML, CSS

# Markdown → HTML
html_content = markdown.markdown(
    report['full_markdown'],
    extensions=['tables', 'fenced_code', 'toc']
)

# CSS 스타일 적용
css_string = """
@page {
    size: A4;
    margin: 2cm;
}
body {
    font-family: 'Noto Sans KR', Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.6;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin: 1em 0;
}
th, td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
}
"""

# PDF 생성
HTML(string=html_content).write_pdf(
    'tcfd_report.pdf',
    stylesheets=[CSS(string=css_string)]
)
```

**장점**:
- Python 라이브러리 → FastAPI와 통합 쉬움
- 한글 폰트 지원 (Noto Sans KR)
- 테이블 스타일링 자유로움

**단점**:
- 복잡한 레이아웃 제한적

#### Option 2: Pandoc
```bash
pandoc report.md -o report.pdf \
    --pdf-engine=xelatex \
    --variable mainfont="Noto Sans KR" \
    --variable fontsize=11pt \
    --toc
```

**장점**:
- 고품질 PDF
- 목차(TOC) 자동 생성
- LaTeX 기반 → 전문적인 출력

**단점**:
- Pandoc 설치 필요 (시스템 의존성)
- 한글 폰트 설정 복잡

#### ✅ **추천: weasyprint**
- 이유: Python native, 설치 간단, FastAPI 통합 쉬움

### 2.5 그래프/차트 처리 (향후)

**현재 (Phase 1)**:
- 텍스트 설명으로 대체
- 예: "극한 고온 리스크는 RCP 8.5 시나리오에서 67.2점으로 평가되었습니다."

**향후 (Phase 2 - VisualizationAgent 구현 시)**:
```json
{
    "sections": [
        {
            "id": "strategy_scenario_chart",
            "title": "Carbon Price Projections",
            "content_type": "visualization",
            "chart": {
                "type": "line",
                "data": {...},
                "image_base64": "iVBORw0KGgo...",  // PNG as base64
                "image_path": "./visualizations/carbon_price.png"
            },
            "content_markdown": "![Carbon Price](./visualizations/carbon_price.png)\n\n*Figure shows...*"
        }
    ]
}
```

---

## 3. 구현 로드맵

### Phase 1: RAG 파싱 인프라 (현재)

#### Step 1: LlamaParse 통합 코드 작성
```python
# polaris_backend_fastapi/ai_agent/services/document_parser.py
class DocumentParser:
    def __init__(self):
        self.parser = LlamaParse(
            api_key=os.getenv("LLAMA_CLOUD_API_KEY"),
            result_type="markdown",
            verbose=True
        )

    def parse_pdf(self, file_path: str, cache_path: str = None):
        """PDF 파싱 (캐시 활용)"""
        # 캐시 체크
        if cache_path and os.path.exists(cache_path):
            return self._load_from_cache(cache_path)

        # 파싱 실행
        documents = self.parser.load_data(file_path)

        # 캐시 저장
        if cache_path:
            self._save_to_cache(documents, cache_path)

        return documents
```

#### Step 2: Qdrant 저장
```python
# polaris_backend_fastapi/ai_agent/services/rag_service.py
class RAGService:
    def ingest_parsed_documents(self, documents: List[Document]):
        """파싱된 문서를 Qdrant에 저장"""
        for doc in documents:
            # 청크 분할
            chunks = self._chunk_document(doc.text, chunk_size=512)

            # 임베딩 + 저장
            for chunk in chunks:
                vector = self.embedder.encode(chunk['text'])
                self.qdrant_client.upsert(
                    collection_name="tcfd_documents",
                    points=[{
                        "vector": vector,
                        "payload": {
                            "text": chunk['text'],
                            "source": doc.metadata.get('file_name'),
                            "page": chunk.get('page'),
                            "section": chunk.get('section')
                        }
                    }]
                )

        # 테이블 별도 처리
        self._extract_and_store_tables(documents)
```

#### Step 3: 파싱 스크립트 (one-time 실행)
```python
# scripts/parse_rag_documents.py
"""
한 번만 실행하는 파싱 스크립트
주의: Free tier 사용량 소진하므로 신중하게 실행
"""

def main():
    parser = DocumentParser()

    docs_to_parse = [
        {
            "path": "각종 자료/For_RAG/FINAL-2017-TCFD-Report.pdf",
            "cache": "data/parsed_docs/tcfd_report_parsed.json"
        },
        {
            "path": "각종 자료/For_RAG/SnP_Climanomics_PangyoDC_Summary_Report_SK C&C_2024-02-08.pdf",
            "cache": "data/parsed_docs/sp_climanomics_parsed.json"
        }
    ]

    for doc_info in docs_to_parse:
        print(f"Parsing {doc_info['path']}...")
        documents = parser.parse_pdf(
            doc_info['path'],
            cache_path=doc_info['cache']
        )
        print(f"✅ Parsed {len(documents)} documents")

    # Qdrant에 저장
    rag_service = RAGService()
    all_docs = []
    for doc_info in docs_to_parse:
        cached_docs = parser._load_from_cache(doc_info['cache'])
        all_docs.extend(cached_docs)

    rag_service.ingest_parsed_documents(all_docs)
    print("✅ All documents ingested to Qdrant")

if __name__ == "__main__":
    # 실행 전 확인 메시지
    confirm = input("⚠️  This will consume LlamaParse free tier quota. Continue? (yes/no): ")
    if confirm.lower() == 'yes':
        main()
    else:
        print("Cancelled.")
```

### Phase 2: 보고서 출력 형식 구현

#### Step 1: Report Composer 개선
```python
# report_composer_agent_4.py
def compose_final_report(self, state: SuperAgentState) -> Dict[str, Any]:
    """
    JSON 구조 + Markdown 생성
    """
    sections = []

    # 1. Executive Summary
    sections.append({
        "id": "executive_summary",
        "title": "Executive Summary",
        "order": 1,
        "content_markdown": self._generate_executive_summary(state),
        "content_type": "text"
    })

    # 2. Governance
    sections.append(self._generate_governance_section(state))

    # 3. Strategy (with tables)
    sections.append(self._generate_strategy_section(state))

    # ... 기타 섹션

    # Full Markdown 조립
    full_markdown = self._assemble_markdown(sections)

    return {
        "report_json": {
            "metadata": {...},
            "sections": sections,
            "full_markdown": full_markdown,
            "raw_data": {
                "hazard_scores": state['hazard_scores'],
                "aal_values": state['aal_values'],
                ...
            }
        },
        "estimated_pages": self._estimate_pages(full_markdown)
    }
```

#### Step 2: PDF 생성 (Finalizer)
```python
# finalizer_node_7.py
def finalize_report(state: SuperAgentState) -> Dict:
    """
    Markdown → PDF 변환 및 저장
    """
    report_json = state['generated_report']['report_json']

    # 1. DB 저장
    db.save_report(
        site_id=state['site_id'],
        report_content=report_json  # JSONB 컬럼
    )

    # 2. Markdown 파일 저장
    md_path = f"./output/{session_id}/report.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(report_json['full_markdown'])

    # 3. PDF 생성
    pdf_path = f"./output/{session_id}/report.pdf"
    generate_pdf_from_markdown(md_path, pdf_path)

    return {
        "output_paths": {
            "markdown": md_path,
            "json": f"./output/{session_id}/report.json",
            "pdf": pdf_path
        },
        "final_status": "completed"
    }
```

---

## 4. 예상 결과

### 4.1 파싱 결과 (예시)

#### TCFD 권고안 파싱 결과
```markdown
# Introduction

The Financial Stability Board (FSB) established the Task Force on Climate-related
Financial Disclosures (TCFD) to develop recommendations for more effective
climate-related disclosures...

## Governance

Organizations should disclose:
a) The board's oversight of climate-related risks and opportunities
b) Management's role in assessing and managing climate-related risks and opportunities

...

### Table 1: TCFD Recommended Disclosures

| Pillar | Recommended Disclosure |
|--------|------------------------|
| Governance | Describe board oversight |
| Strategy | Describe climate-related risks |
| Risk Management | Describe processes |
| Metrics & Targets | Disclose metrics |
```

### 4.2 최종 보고서 출력 (예시)

#### Markdown
```markdown
# TCFD Climate Risk Assessment Report

**Company**: ABC Corporation
**Site**: Pangyo Data Center
**Generated**: 2025-12-12
**Version**: 2.0

---

## Executive Summary

This report assesses climate-related risks and opportunities for Pangyo Data Center
based on TCFD recommendations. Key findings:

- **Top Physical Risk**: Extreme heat (Score: 67.2/100 under RCP 8.5)
- **Top Transition Risk**: RE100 policy volatility in South Korea
- **Financial Impact**: Estimated carbon costs of KRW 196.2 billion by 2040 under Net Zero pathway

---

## 1. Governance

### 1.1 Board Oversight

The Board of Directors oversees climate-related issues through the Strategy & ESG Committee,
which meets quarterly to review:
- Climate risk assessment results
- Net Zero 2040 implementation progress
- RE100 achievement status

### 1.2 Management's Role

The Chief Sustainability Officer (CSO) is responsible for:
- Developing climate strategies
- Monitoring carbon emissions (Scope 1, 2, 3)
- Reporting to the Board on climate performance

Climate-related KPIs are integrated into executive compensation, with 15% of annual
incentive tied to:
- Net Zero milestone achievement
- RE100 progress
- ESG rating improvements

---

## 2. Strategy

### 2.1 Climate-related Risks and Opportunities

#### 2.1.1 Transition Risks

| Risk ID | Type | Description | Time Horizon | Impact |
|---------|------|-------------|--------------|--------|
| T1 | Policy | RE100 policy changes in South Korea | Short/Mid/Long | High |
| T3 | Policy | Emissions Trading Scheme (ETS) tightening | Short/Mid | High |

*Table 1: Key Transition Risks*

#### 2.1.2 Physical Risks

| Risk ID | Type | Description | Time Horizon | Impact |
|---------|------|-------------|--------------|--------|
| P1 | Acute | Extreme heat events affecting cooling costs | Long | High |
| P2 | Chronic | Rising average temperatures | Long | High |

*Table 2: Key Physical Risks*

### 2.2 Scenario Analysis

#### 2.2.1 Transition Risk Scenarios

**NGFS Net Zero 2050**

Under this scenario, South Korea's carbon prices are projected to reach:
- 2030: USD 90/tCO₂eq
- 2040: USD 160/tCO₂eq

**Financial Impact** (2021-2040 cumulative):
- Business-as-Usual: KRW 153.1 billion
- With Net Zero implementation: KRW 196.2 billion

The Net Zero pathway requires upfront renewable energy investments but reduces
long-term carbon price exposure.

#### 2.2.2 Physical Risk Scenarios

**SSP5-8.5 (High Emissions)**

Based on S&P Global Climanomics analysis, under the SSP5-8.5 pathway:

| Hazard | 2030 | 2040 | Risk Level |
|--------|------|------|------------|
| Extreme Heat | Moderate | Elevated | Medium |
| River Flooding | Low | Low | Low |
| Water Stress | Low | Low-Moderate | Low |

*Table 3: Physical Risk Assessment by Hazard Type*

**Modeled Average Annual Loss (AAL)**:
- Pangyo Data Center: < 3% of asset value
- Daedeok Data Center: < 3% of asset value

All facilities demonstrate manageable physical risk exposure across all SSP scenarios.

### 2.3 Response Strategies

#### Net Zero 2040 Roadmap

1. **Renewable Energy Transition (RE100)**
   - 2024: 24.7% renewable electricity
   - 2030: 60% target
   - 2040: 100% target

2. **Energy Efficiency**
   - High-efficiency cooling systems
   - Data center PUE < 1.4 by 2030

3. **Carbon Offsetting**
   - Internal carbon pricing: Reflects NGFS carbon price projections
   - Investment decision criteria

---

## 3. Risk Management

### 3.1 Risk Identification Process

Climate risks are identified through:
1. Annual scenario analysis (NGFS, RCP/SSP)
2. Stakeholder engagement (customers, regulators, investors)
3. Industry benchmarking

### 3.2 Risk Integration

Climate risks are integrated into enterprise risk management (ERM) framework:
- ISO 14001 Environmental Management System
- Quarterly risk reviews by ESG Committee
- Escalation to Board for material risks

---

## 4. Metrics and Targets

### 4.1 Greenhouse Gas Emissions

| Scope | 2023 (Baseline) | 2024 | 2030 Target | 2040 Target |
|-------|-----------------|------|-------------|-------------|
| Scope 1 | 1,434 tCO₂eq | 1,283 tCO₂eq | -60% | Net Zero |
| Scope 2 (Location) | 125,207 tCO₂eq | 135,382 tCO₂eq | -60% | Net Zero |
| Scope 2 (Market) | 102,604 tCO₂eq | 102,626 tCO₂eq | -60% | Net Zero |
| Scope 3 | 13,860,200 tCO₂eq | 14,210,016 tCO₂eq | N/A | -90% by 2050 |

*Table 4: GHG Emissions and Reduction Targets*

### 4.2 RE100 Progress

| Year | Target | Achievement |
|------|--------|-------------|
| 2023 | 16% | 18.1% ✅ |
| 2024 | 23% | 24.7% ✅ |
| 2025 | 30% | - |
| 2030 | 60% | - |
| 2040 | 100% | - |

*Table 5: RE100 Targets and Progress*

---

## Appendix A: Data Sources

- Climate projections: CMIP6 ensemble models
- Scenario frameworks: NGFS, RCP/SSP
- Physical risk assessment: S&P Global Climanomics®
- Emissions calculations: IPCC 2006 Guidelines
- Carbon prices: IEA Net Zero 2050 Scenario

---

**Report generated by POLARIS TCFD Agent v2.0**
**Based on TCFD Recommendations (2017)**
```

#### PDF 출력 (A4, 약 6-7 페이지 예상)
- 폰트: Noto Sans KR 11pt
- 여백: 2cm
- 테이블 스타일: 1px solid border
- 목차 자동 생성 가능

---

## 5. 다음 단계

### 즉시 실행 (코드만 작성, 파싱 X)
1. ✅ DocumentParser 클래스 구현
2. ✅ RAGService 업데이트 (테이블 처리)
3. ✅ 파싱 스크립트 작성

### 파싱 실행 시점 (확인 후)
- 사용자 확인 후 `scripts/parse_rag_documents.py` 실행
- 약 110 pages 소진 예상

### 보고서 출력 구현
1. Report Composer JSON 구조 개선
2. weasyprint PDF 생성 함수 추가
3. Finalizer 업데이트

---

**요약**:
- **파싱 전략**: 전체 문서 파싱 (110 pages), Markdown 형식, 캐싱 활용
- **출력 형식**: JSON (Markdown + 테이블 데이터) → DB 저장, Markdown → PDF (weasyprint)
- **그래프**: Phase 1에서는 텍스트 설명, Phase 2에서 VisualizationAgent 구현 시 이미지 추가
