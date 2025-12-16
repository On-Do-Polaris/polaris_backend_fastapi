# TCFD Report Generation Agents v2

**작성일:** 2025-12-15
**버전:** v2.1 (7-Node Refactoring)
**설계 문서:** [tcfd_report_refactoring_plan.md](../../../docs/planning/tcfd_report_refactoring_plan.md)

## 개요

항목별 순차 분석 구조 (Scenario → Impact → Mitigation)로 설계된 TCFD 보고서 생성 AI Agent 시스템입니다.

**주요 변경사항 (v2.1)**:
- 10개 노드 → **7개 노드**로 통합 (Node 4, 5, 6, 8 → Node 5로 통합)
- JSON 블록 생성 로직 추가 (TableBlock, HeatmapTableBlock, LineChartBlock)
- 노드 번호 재정리 (Validator: Node 7→4, Composer: Node 8→5, Finalizer: Node 9→6)

## 디렉토리 구조

```
tcfd_report/
├── __init__.py                          # 모듈 export
├── README.md                            # 이 파일
├── workflow.py                          # LangGraph 워크플로우 정의
├── schemas.py                           # Pydantic 스키마 (JSON 블록 타입)
│
├── node_0_data_preprocessing.py        # Node 0: DB + Excel 데이터 로딩
├── node_1_template_loading.py          # Node 1: RAG + TCFD 템플릿
├── node_2a_scenario_analysis.py        # Node 2-A: 시나리오 분석 + TableBlock
├── node_2b_impact_analysis.py          # Node 2-B: 영향 분석 + TextBlock x5
├── node_2c_mitigation_strategies.py    # Node 2-C: 대응 방안 + TextBlock x5
├── node_3_strategy_section.py          # Node 3: Strategy 섹션 + HeatmapTableBlock
├── node_4_validator.py                 # Node 4: Validator (구 node_7)
├── node_5_composer.py                  # Node 5: Composer (Risk+Governance+Metrics+Appendix 통합)
├── node_6_finalizer.py                 # Node 6: Finalizer (구 node_9)
│
├── visualize_tcfd_workflow.py          # 워크플로우 시각화 스크립트
├── tcfd_workflow_diagram.mmd           # Mermaid 다이어그램
└── tcfd_chart_matrix.mmd               # Chart 생성 매트릭스
```

## 워크플로우 순서 (7-Node)

### 순차 처리
```
Node 0 → Node 1 → Node 2-A → Node 2-B → Node 2-C → Node 3 → Node 4 → Node 5 → Node 6
```

### 병렬 처리
- **Node 0 내부**: 8개 사업장 데이터 로딩 (~10초)
- **Node 2-A 내부**: 8개 사업장 시나리오 AAL 계산 (~15초)
- **Node 2-B 내부**: Top 5 리스크 영향 분석 (~60초)
- **Node 2-C 내부**: Top 5 리스크 대응 방안 (~60초)

## 주요 설계 결정

### v2.0 → v2.1 변경사항 (7-Node Refactoring)

1. **노드 통합**: Node 4, 5, 6, 8 → Node 5 (Composer)로 통합
   - Risk Management (하드코딩 + Node 2-C 일부)
   - Governance (완전 하드코딩)
   - Metrics & Targets (템플릿 + LineChartBlock)
   - Appendix (완전 하드코딩)
   - Report Composer (목차 생성, 페이지 번호)

2. **JSON 블록 생성**: 각 노드가 자체 Chart/Table 생성
   - Node 2-A: TableBlock (시나리오 AAL 비교)
   - Node 2-B: TextBlock x5 (P1~P5 영향 분석)
   - Node 2-C: TextBlock x5 (P1~P5 대응 전략)
   - Node 3: HeatmapTableBlock (사업장별 리스크 분포)
   - Node 5: LineChartBlock (AAL 추이 2024-2100)

3. **노드 번호 재정리**:
   - node_7_validator_refiner.py → node_4_validator.py
   - node_8_report_composer.py → node_5_composer.py (통합)
   - node_9_finalizer.py → node_6_finalizer.py

4. **스키마 파일 추가**: `schemas.py` (Pydantic 모델 394줄)

### 병렬 처리 전략

| 노드 | 병렬 대상 | 성능 이득 |
|------|----------|-----------|
| Node 0 | 8개 사업장 데이터 로딩 | ~10초 (순차 시 30초) |
| Node 2-A | 8개 사업장 시나리오 AAL 계산 | ~15초 (순차 시 40초) |
| Node 2-B | Top 5 리스크 영향 분석 | ~60초 (순차 시 150초) |
| Node 2-C | Top 5 리스크 대응 방안 | ~60초 (순차 시 150초) |

**총 처리 시간**: 3.5-4.5분 (8개 사업장 기준)

### JSON 블록 타입 (5가지)

| 블록 타입 | 생성 위치 | 개수 | 설명 |
|---------|---------|------|-----|
| TextBlock | Node 2-B, 2-C, 3, 5 | 다수 | 일반 텍스트 |
| TableBlock | Node 2-A | 1개 | 시나리오 AAL 비교표 |
| HeatmapTableBlock | Node 3 | 1개 | 사업장별 리스크 분포 (Gray/Yellow/Orange/Red) |
| LineChartBlock | Node 5 | 1개 | AAL 추이 차트 (2024-2100) |
| BarChartBlock | (미사용) | 0개 | 향후 확장용 |

## 사용 방법

### 1. 워크플로우 초기화

```python
from ai_agent.agents.tcfd_report import create_tcfd_workflow

workflow = create_tcfd_workflow()
```

### 2. 실행

```python
initial_state = {
    "site_ids": [101, 102, 103, 104, 105, 106, 107, 108],
    "excel_file": "path/to/file.xlsx",  # Optional
    "user_id": 456
}

result = await workflow.ainvoke(initial_state)
print(result["report_id"])
```

## 구현 상태 (v2.1)

### ✅ 완료 (2025-12-15)
- ✅ 7개 노드 구조 정의
- ✅ schemas.py 생성 (Pydantic 모델)
- ✅ Node 2-A: TableBlock 생성 로직 추가
- ✅ Node 2-B: TextBlock x5 생성 로직 추가
- ✅ Node 2-C: TextBlock x5 생성 로직 추가
- ✅ Node 3: HeatmapTableBlock 생성 로직 추가
- ✅ Node 5: Composer 통합 (14KB, 370줄)
- ✅ Node 4, 6: 파일 이름 변경
- ✅ 최종 JSON 구조 문서 작성 ([tcfd_report_final_structure.md](../../../docs/tcfd_report_final_structure.md))
- ✅ 워크플로우 시각화 스크립트 ([visualize_tcfd_workflow.py](visualize_tcfd_workflow.py))

### 🚧 진행 중 (50% 완료)
- [ ] Node 0: DB 직접 쿼리 (psycopg2) 구현
- [ ] Node 2-A/B/C: LLM 프롬프트 작성
- [ ] Node 3: Executive Summary LLM 프롬프트
- [ ] Node 4: TCFD 검증 로직
- [ ] workflow.py: 7-node 구조 반영
- [ ] __init__.py: export 업데이트
- [ ] LangGraph 엣지 연결
- [ ] 에러 핸들링
- [ ] 단위 테스트
- [ ] 통합 테스트

## 참고 자료

### 문서
- **Refactoring Plan**: [tcfd_report_refactoring_plan.md](../../../docs/planning/tcfd_report_refactoring_plan.md)
- **Progress**: [tcfd_report_refactoring_progress.md](../../../docs/progress/tcfd_report_refactoring_progress.md)
- **최종 JSON 구조**: [tcfd_report_final_structure.md](../../../docs/tcfd_report_final_structure.md)
- **TCFD 가이드**: [tcfd_guide.md](../../../docs/for_better_understanding/tcfd_guide.md)
- **SK ESG 참조**: [sk_esg_2025.md](../../../docs/for_better_understanding/sk_esg_2025.md)

### 코드
- **스키마**: [schemas.py](schemas.py) - 5가지 JSON 블록 타입 정의
- **시각화**: [visualize_tcfd_workflow.py](visualize_tcfd_workflow.py)
- **다이어그램**: [tcfd_workflow_diagram.mmd](tcfd_workflow_diagram.mmd)

## 다음 단계

1. **Phase 3 완료**: Node 0 DB 쿼리 구현
2. **Phase 4**: workflow.py 업데이트 (7-node 구조)
3. **Phase 5**: LLM 프롬프트 작성 (Node 2-A/B/C, 3)
4. **Phase 6**: 테스트 및 최적화
