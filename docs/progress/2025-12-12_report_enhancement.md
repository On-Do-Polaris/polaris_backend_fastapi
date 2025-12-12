# TCFD 보고서 에이전트 고도화 진행 상황

**날짜**: 2025-12-12
**담당**: Claude Code
**관련 Planning**: [report_agent_enhancement_plan.md](../planning/report_agent_enhancement_plan.md)

---

## 진행 상황 요약

### 완료된 작업 ✅

#### 1. SK TCFD 보고서 분석 완료
**파일**: `각종 자료/ESG REPORT/SK 주식회사/2025/2025_SK_Inc._Sustainability_Report_KOR_TCFD.pdf`

**주요 발견사항**:
- 총 23페이지 (26-48페이지)
- **로직 직접 설명 없음**: 계산 공식을 상세히 설명하지 않고, 분석 결과와 활용 방법 중심으로 서술
- **시각화 풍부**: 20+ 테이블, 10+ 그래프/다이어그램
- **시나리오 분석 중심**: NGFS (전환 리스크), SSP/RCP (물리적 리스크)

**구조**:
1. Governance (지배구조)
   - 이사회 감독 체계
   - KPI 및 보상 연계

2. Strategy (전략)
   - 리스크/기회 식별 (전환 8개, 물리적 2개, 기회 4개)
   - 시나리오 분석 (사업장 Level, 포트폴리오 Level)
   - 대응 방안

3. Risk Management (리스크 관리)
   - 통합 리스크 관리 프로세스
   - Value Chain 관리

4. Metrics and Targets (지표 및 목표)
   - Scope 1,2,3 배출량
   - Net Zero 2040, RE100 2040 목표

#### 2. 현재 시스템 구조 파악 완료
**Workflow**: LangGraph v07 (Phase 2)
- 11개 노드
- 7개 보고서 생성 에이전트

**에이전트 목록**:
1. report_analysis_agent_1.py (Template)
2. impact_analysis_agent_2.py (Impact)
3. strategy_generation_agent_3.py (Strategy)
4. report_composer_agent_4.py (Composer)
5. validation_agent_5.py (Validation)
6. refiner_agent_6.py (Refiner)
7. finalizer_node_7.py (Finalizer)

**RAG 현황**:
- 3개 에이전트만 RAG 사용 (Template, Impact, Strategy)
- 활용도 낮음 → 개선 필요

#### 3. Planning 문서 작성 완료
**파일**: `polaris_backend_fastapi/docs/planning/report_agent_enhancement_plan.md`

**핵심 전략**:
- **Phase 1 (현재 집중)**: 내용 퀄리티 향상
  - RAG 자료 확충
  - Prompt 고도화
  - 섹션 구조 확장 (2페이지 → 5+ 페이지)

- **Phase 2 (추후)**: 시각화 추가
  - VisualizationAgent (보류)
  - DataProcessingAgent (보류)

#### 4. LlamaParse 파싱 전략 수립 완료
**파일**: `polaris_backend_fastapi/docs/planning/rag_parsing_strategy.md`

**핵심 결정사항**:
- **파싱 범위**: 전체 문서 파싱 (110 pages total)
  - TCFD Official Report: ~80 pages
  - S&P Climanomics Report: ~30 pages
- **파싱 형식**: `result_type="markdown"` (테이블 보존)
- **캐싱 전략**: 로컬 JSON 캐싱으로 재파싱 방지
- **Qdrant 컬렉션**: 2개 분리 저장
  - `tcfd_documents`: 일반 문서 청크 (512 토큰 단위)
  - `tcfd_tables`: 테이블 데이터 (자연어 변환 + 구조화 메타데이터)

**출력 형식 설계**:
- **DB 저장**: JSON/JSONB 형식
  - sections 배열: 섹션별 구조화
  - full_markdown: 전체 마크다운
  - tables: 마크다운 + 구조화 데이터 병행
- **PDF 생성**: weasyprint (Markdown → HTML → PDF)

#### 5. LlamaParse 통합 코드 구현 완료
**파일**: `polaris_backend_fastapi/ai_agent/services/document_parser.py`

**주요 기능**:
- LlamaParse 클라이언트 초기화
- PDF → Markdown 변환
- 로컬 캐싱 (data/parsed_docs/)
- 파싱 메타데이터 추적 (페이지 사용량 관리)
- 테이블 추출 (Markdown 정규식 파싱)

**주의사항**:
- 실제 파싱 실행 금지 (Free Tier 1,000 pages/month)
- 캐시 우선 사용으로 재파싱 방지

#### 6. RAG Ingestion 서비스 구현 완료
**파일**: `polaris_backend_fastapi/ai_agent/services/rag_ingestion_service.py`

**주요 기능**:
- DocumentParser 통합
- 텍스트 청킹 (섹션 단위 → 문장 단위)
- 청크 오버랩 적용 (문맥 보존)
- 테이블 자연어 변환 (임베딩 최적화)
- Qdrant 2개 컬렉션 업로드
- 배치 처리 지원

**기존 코드 활용**:
- `qdrant_vector_store.py` (v01): 컬렉션 관리 및 검색
- `rag_helpers.py`: RAGEngine wrapper (Mock fallback)

#### 7. 실행 스크립트 구현 완료
**파일**: `polaris_backend_fastapi/scripts/ingest_rag_documents.py`

**기능**:
- 환경변수 검증 (LLAMA_CLOUD_API_KEY, PDF 파일 존재 확인)
- 문서별 메타데이터 설정
- 통계 출력 (파싱 사용량, Qdrant 상태)
- CLI 인터페이스:
  - `--all`: 전체 문서 수집
  - `--document tcfd|snp`: 특정 문서만 수집
  - `--force-reparse`: 캐시 무시 (주의!)
  - `--stats`: 통계만 출력

**문서 설정**:
1. TCFD Official 2017 Report
   - document_id: `tcfd_official_2017`
   - tags: tcfd, governance, strategy, risk_management, metrics, guidelines
2. S&P Climanomics Pangyo DC 2024 Report
   - document_id: `snp_climanomics_pangyo_2024`
   - tags: s&p, climanomics, physical_risk, data_center, pangyo, analysis

---

## 다음 작업 계획

### 1. LlamaParse 파싱 실행 (사용자 확인 후)

**준비 완료 항목**:
- ✅ LLAMA_CLOUD_API_KEY 환경변수 설정
- ✅ S&P pptx → PDF 변환 완료
- ✅ DocumentParser 구현 완료
- ✅ RAGIngestionService 구현 완료
- ✅ 실행 스크립트 구현 완료

**실행 명령**:
```bash
# 통계 확인
python scripts/ingest_rag_documents.py --stats

# 전체 문서 파싱 및 업로드
python scripts/ingest_rag_documents.py --all
```

**주의사항**:
- 사용자 승인 후에만 실행
- Free Tier 사용량 확인 (110 pages 소모 예상)
- Qdrant 서버 실행 확인 필요

### 2. RAG 활용도 향상

**목표**:
- 7개 에이전트 중 RAG 미사용 4개 에이전트에 RAG 통합
  - report_composer_agent_4.py
  - validation_agent_5.py
  - refiner_agent_6.py
  - finalizer_node_7.py (필요 시)

**구현 방법**:
- `rag_helpers.py`의 `rag_query()` 함수 활용
- 에이전트별 적합한 쿼리 설계

### 3. Agent Prompt 개선

**우선순위**:
1. Report Analysis Agent (Template)
2. Impact Analysis Agent
3. Strategy Generation Agent
4. Report Composer Agent
5. Validation Agent

---

## 현재 제약사항

1. **DB/Qdrant 연결 불가**: 로컬 환경에서 연결 안 됨 → 구조만 설계
2. **VisualizationAgent 보류**: 표/그래프 기준 불명확
3. **추가 Excel 데이터 보류**: 추후 구현
4. **LlamaParse Free 요금제**: 과금 방지 필수

---

## 구현된 파일 목록

### 신규 생성 파일
1. `polaris_backend_fastapi/docs/planning/rag_parsing_strategy.md` - RAG 파싱 전략 문서
2. `polaris_backend_fastapi/ai_agent/services/document_parser.py` - DocumentParser 클래스
3. `polaris_backend_fastapi/ai_agent/services/rag_ingestion_service.py` - RAGIngestionService 클래스
4. `polaris_backend_fastapi/scripts/ingest_rag_documents.py` - 실행 스크립트

### 기존 활용 파일
1. `polaris_backend_fastapi/ai_agent/utils/qdrant_vector_store.py` (v01) - Qdrant 클라이언트
2. `polaris_backend_fastapi/ai_agent/utils/rag_helpers.py` - RAGEngine wrapper
3. `polaris_backend_fastapi/ai_agent/utils/rag_engine.py` (v00) - 기존 템플릿 생성 (유지)

---

## 기술 스택 확정

### LlamaParse
- Free Tier: 1,000 pages/month
- result_type: `"markdown"` (테이블 보존)
- 로컬 캐싱: `data/parsed_docs/`

### Qdrant Collections
1. **tcfd_documents**
   - Vector Size: 384 (all-MiniLM-L6-v2)
   - Distance: Cosine
   - Payload: document_id, company_name, report_year, report_type, section_type, content, metadata, tags

2. **tcfd_tables**
   - 동일한 벡터 설정
   - Payload: 추가로 markdown, headers, row_count, column_count 포함

### 출력 형식
- **JSON/JSONB**: sections 배열 + full_markdown
- **PDF**: weasyprint (Markdown → HTML → PDF)

---

## 해결된 이슈

### 1. ✅ LlamaParse API 키
- 환경변수 설정 완료: `LLAMA_CLOUD_API_KEY`

### 2. ✅ S&P pptx 파일
- PDF 변환 완료: `SnP_Climanomics_PangyoDC_Summary_Report_SK C&C_2024-02-08.pdf`

### 3. ✅ 보고서 출력 형식
- **확정**: JSON/JSONB (DB 저장) + PDF (weasyprint)
- Markdown을 중간 형식으로 활용

---

## 다음 업데이트 예정일
**2025-12-13**: 파싱 실행 및 Agent Prompt 개선 시작
