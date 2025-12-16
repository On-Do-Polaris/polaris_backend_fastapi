# TCFD Report Generation System Refactoring Plan

**작성일:** 2025-12-14
**작성자:** AI Development Team
**목적:** TCFD 보고서 생성 시스템 재설계 및 구조 개선

---

## 📋 변경 개요

### 주요 변경사항

1. **Data Processing 에이전트 재구성**
   - `vulnerability_analysis_agent.py` → `building_characteristics_agent.py` 이동 및 프롬프트 수정
   - `additional_data_agent.py` 신규 생성 (Excel 분석)
   - 두 에이전트 모두 "보고서 생성 가이드라인" 생성으로 역할 변경

2. **노드 구조 단순화**
   - 기존 10개 노드 → **7개 노드**
   - Node 4 (Metrics) 삭제 → Node 5 (Composer)에 통합
   - Node 4 (Risk Management) 삭제 → Node 5에 통합
   - Node 6 (Governance/Appendix) 삭제 → Node 5에 통합
   - Node 8 (Composer) 삭제 → Node 5에 통합
   - 새 Node 5 = Risk Management + Governance + Appendix + Metrics + Composer

3. **차트/표 JSON 형식 표준화**
   - `schemas.py` 신규 생성 (Pydantic 스키마 정의)
   - Heatmap, LineChart, BarChart, Table 통일된 형식

4. **데이터 로딩 방식 변경**
   - API 호출 → DB 직접 쿼리 (3-4배 속도 향상)

5. **분석 레이어 vs 포맷팅 레이어 분리**
   - Node 2-A/B/C: 순수 분석 (LLM)
   - Node 3: 포맷팅 + 시각화 (JSON 생성)
   - Node 4: 검증 (TCFD 원칙)
   - Node 5: 템플릿 통합 + Composer (Metrics 포함)

---

## 🎯 최종 노드 구조

### Data Processing (Optional)

```
building_characteristics_agent.py
├── 입력: lat, lon, address
├── 처리: 건축물 대장 API → BuildingDataFetcher
├── 출력: state["building_guideline"] (가이드라인)
└── LLM 프롬프트: "보고서 생성 에이전트를 위한 가이드라인 작성"

additional_data_agent.py (Conditional)
├── 입력: excel_file (if exists)
├── 처리: Excel 파싱 → 카테고리 분류 → LLM 분석
├── 출력: state["excel_guideline"] (가이드라인)
└── 조건: excel_file이 있을 때만 실행
```

### TCFD Report Generation (7개 노드)

```
Node 0: Data Loading
├── DB 직접 쿼리 (psycopg2)
├── 8개 사업장 병렬 로딩 (~150ms)
├── 테이블: sites, hazard_results, exposure_results, vulnerability_results, aal_scaled_results
└── JSON 가공

Node 1: Template Loading
├── RAG 쿼리 (Qdrant)
└── TCFD 구조 템플릿

Node 2-A: Scenario Analysis (분석 레이어)
├── LLM: 4가지 SSP 시나리오별 AAL 추이 분석
├── 포트폴리오 통합 분석
├── 📊 TableBlock 생성: 시나리오별 AAL 비교표
└── 추가 데이터 활용 (optional)

Node 2-B: Impact Analysis (분석 레이어)
├── Top 5 리스크 식별
├── LLM: 재무/운영/자산 영향 분석 (5개 병렬)
├── 📝 TextBlock 생성 x5: P1~P5 영향 분석
└── 추가 데이터 활용 (optional)

Node 2-C: Mitigation Strategies (분석 레이어)
├── LLM: Top 5 리스크별 대응 방안 (5개 병렬)
├── 단기/중기/장기 구분
├── 📝 TextBlock 생성 x5: P1~P5 대응 전략
└── 추가 데이터 활용 (optional)

Node 3: Strategy Section (포맷팅 레이어)
├── LLM: Executive Summary 생성
├── Node 2-A/B/C 결과 조립
├── 🔥 HeatmapTableBlock 생성: 사업장별 리스크 AAL 분포
└── 특정 사업장 추가 데이터 언급

Node 4: Validator
├── TCFD 7대 원칙 검증
├── 누락 섹션 체크
└── 1회 재생성 (critical 이슈만)

Node 5: Composer & Template Generator (통합 노드)
├── Risk Management 섹션 하드코딩 + Node 2-C 일부 삽입
├── Governance 섹션 하드코딩
├── Appendix 섹션 하드코딩
├── Metrics & Targets 섹션
│   ├── AAL 지표 텍스트 (Node 2-A 활용)
│   ├── 📈 LineChartBlock 생성: AAL 추이 차트 (2024-2100)
│   └── 목표 템플릿 하드코딩
├── 모든 섹션 순서대로 조립
├── 목차(TOC) 생성
└── 페이지 번호 매기기

Node 6: Finalizer
└── JSONB DB 저장 (reports 테이블)
```

---

## 📊 차트/표 형식 표준화

### schemas.py 구조

```python
# Block Types
- TextBlock
- TableBlock
- HeatmapTableBlock
- LineChartBlock
- BarChartBlock

# Data Structures
- TableData (headers, rows, footer)
- TableCell (value, bg_color, text_color, alignment)
- HeatmapTableData (headers, rows, legend)
- HeatmapCell (value, bg_color: gray|yellow|orange|red)
- LineChartData (x_axis, y_axis, series)
- SeriesData (name, color, data)
```

### 사용 노드

| 노드 | 생성 항목 | 타입 |
|------|----------|------|
| Node 2-A | 시나리오별 AAL 비교표 | TableBlock |
| Node 2-B | P1~P5 영향 분석 텍스트 | TextBlock × 5 |
| Node 2-C | P1~P5 대응 전략 텍스트 | TextBlock × 5 |
| Node 3 | 사업장별 리스크 Heatmap | HeatmapTableBlock |
| Node 5 | AAL 추이 차트 (2024-2100) | LineChartBlock |
| Node 5 | Risk Management, Governance, Appendix | TextBlock |

---

## 🔄 마이그레이션 체크리스트

### Phase 1: 준비 작업
- [x] 계획 문서 작성
- [ ] 진행상황 문서 초기화
- [ ] schemas.py 생성

### Phase 2: Data Processing 재구성
- [ ] vulnerability_analysis_agent.py → building_characteristics_agent.py 이동
- [ ] building_characteristics_agent.py 프롬프트 수정
- [ ] additional_data_agent.py 생성

### Phase 3: 노드 파일 수정 및 이름 변경
- [ ] Node 0: DB 직접 쿼리 구현
- [ ] Node 1: 유지 (변경 없음)
- [ ] Node 2-A: 추가 데이터 분기 처리 + TableBlock 생성
- [ ] Node 2-B: 추가 데이터 분기 처리 + TextBlock x5 생성
- [ ] Node 2-C: 추가 데이터 분기 처리 + TextBlock x5 생성
- [ ] Node 3: HeatmapTableBlock 생성 로직 추가
- [ ] Node 4: Validator (node_7_validator_refiner.py 이름 변경)
- [ ] Node 5: 새로 작성 (통합 노드 - Metrics 포함)
- [ ] Node 6: Finalizer (node_9_finalizer.py 이름 변경)

### Phase 4: 삭제 작업
- [ ] node_4_risk_management.py 삭제 → Node 5에 통합
- [ ] node_5_metrics_targets.py 삭제 → Node 5에 통합
- [ ] node_6_governance_appendix.py 삭제 → Node 5에 통합
- [ ] node_8_report_composer.py 삭제 → Node 5에 통합

### Phase 5: 워크플로우 재구성
- [ ] workflow.py 수정 (7개 노드 구조)
- [ ] __init__.py 수정 (export 업데이트)
- [ ] State 정의 수정 (building_guideline, excel_guideline 추가)

### Phase 6: 문서 업데이트
- [ ] ai_understanding.md 수정
- [ ] report_plan_v2.md 수정

### Phase 7: 테스트
- [ ] 단위 테스트 (각 노드별)
- [ ] 통합 테스트 (전체 워크플로우)
- [ ] 추가 데이터 있을 때/없을 때 분기 테스트

---

## 🚀 구현 우선순위

### Priority 1 (필수)
1. schemas.py 생성 ✅
2. Node 0 DB 쿼리 구현
3. Node 2-A/B/C 표/차트 JSON 생성
4. Node 3 Heatmap 생성
5. Node 5 통합 노드 구현 (Metrics 포함)

### Priority 2 (중요)
1. building_characteristics_agent.py 수정 ✅
2. additional_data_agent.py 생성 ✅
3. Node 2-A/B/C 추가 데이터 분기 처리
4. visualize_tcfd_workflow.py 생성 ✅

### Priority 3 (최적화)
1. workflow.py 재구성
2. 문서 업데이트
3. 테스트 코드 작성

---

## ⚠️ 주의사항

1. **추가 데이터 사용 범위**
   - Node 2-A/B/C에서만 사용
   - Node 3에서 특정 사업장만 언급 (전체 요약에는 포함 X)
   - Node 4 이후에는 사용 안 함

2. **DB 저장**
   - LLM 생성물(가이드라인)은 DB 저장 안 함 (State로만 전달)
   - 최종 리포트만 Node 7에서 JSONB로 저장

3. **하드코딩 템플릿**
   - Risk Management (3.1, 3.2, 3.3)
   - Governance (1.1, 1.2)
   - Appendix (A1, A2, A3)
   - 위 섹션들은 정보가 없어서 템플릿 기반으로 생성

4. **성능 목표**
   - 8개 사업장 기준 3.5-4.5분 이내
   - DB 쿼리 병렬 처리로 ~150ms 단축
   - LLM 병렬 처리 (Node 2-B/C에서 5개 리스크 동시 분석)

---

## 📝 예상 산출물

### 최종 JSON 구조

```json
{
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
  "table_of_contents": [...],
  "sections": [
    {
      "section_id": "executive_summary",
      "title": "Executive Summary",
      "page_start": 1,
      "page_end": 2,
      "blocks": [{"type": "text", "content": "..."}]
    },
    {
      "section_id": "governance",
      "title": "1. Governance",
      "page_start": 3,
      "page_end": 4,
      "blocks": [{"type": "text", "content": "..."}]
    },
    {
      "section_id": "strategy",
      "title": "2. Strategy",
      "page_start": 5,
      "page_end": 11,
      "blocks": [
        {"type": "text", "subheading": "2.1 리스크 식별", "content": "..."},
        {"type": "heatmap_table", "title": "...", "data": {...}},
        {"type": "text", "subheading": "P1. 하천 범람", "content": "..."}
      ]
    },
    {
      "section_id": "risk_management",
      "title": "3. Risk Management",
      "page_start": 12,
      "page_end": 14,
      "blocks": [...]
    },
    {
      "section_id": "metrics_targets",
      "title": "4. Metrics and Targets",
      "page_start": 15,
      "page_end": 18,
      "blocks": [
        {"type": "text", "content": "..."},
        {"type": "line_chart", "title": "AAL 추이", "data": {...}}
      ]
    },
    {
      "section_id": "appendix",
      "title": "Appendix",
      "page_start": 19,
      "page_end": 22,
      "blocks": [...]
    }
  ]
}
```

---

**작성 완료일:** 2025-12-14
**다음 단계:** Phase 1 구현 시작
