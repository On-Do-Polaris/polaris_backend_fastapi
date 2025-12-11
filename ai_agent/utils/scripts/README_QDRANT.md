# Qdrant Vector Store Integration

## 개요

이 프로젝트는 ESG/TCFD 보고서 분석을 위한 Qdrant Vector Store 통합을 구현합니다.
ReportAnalysisAgent가 기존 보고서를 벤치마크로 활용할 수 있도록 RAG(Retrieval Augmented Generation) 패턴을 사용합니다.

## 주요 컴포넌트

### 1. QdrantVectorStore (`qdrant_vector_store.py`)
- Qdrant 클라이언트 래퍼
- 벡터 검색, 문서 추가, 컬렉션 관리 기능 제공
- 임베딩 모델: `sentence-transformers/all-MiniLM-L6-v2` (384차원)
- 거리 메트릭: Cosine Similarity

### 2. RAGEngine (`rag_helpers.py`)
- ReportAnalysisAgent에서 사용하는 검색 엔진
- Qdrant 모드와 Mock 모드 지원
- 자동 fallback 기능 (Qdrant 연결 실패 시 Mock 데이터 사용)

### 3. Upload Script (`upload_reports.py`)
- PDF 보고서를 Qdrant에 업로드하는 스크립트
- PDF 파싱, 섹션 감지, 텍스트 청킹 기능
- 단일 파일 및 배치 디렉토리 업로드 지원

## 설치

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

필수 패키지:
- `qdrant-client==1.7.0`
- `sentence-transformers==2.3.1`

### 2. Qdrant 서버 시작

#### 로컬 Docker 사용:
```bash
docker run -p 6333:6333 qdrant/qdrant
```

#### Qdrant Cloud 사용:
1. https://cloud.qdrant.io 에서 계정 생성
2. 클러스터 생성 후 URL과 API 키 획득

### 3. 환경 변수 설정

`.env` 파일 생성 (`.env.example` 참고):

```env
# Qdrant 설정
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-api-key-here  # Cloud 사용 시에만 필요
QDRANT_COLLECTION=esg_tcfd_reports
RAG_MOCK_MODE=false
```

## 사용법

### 1. 보고서 업로드

#### 단일 파일 업로드:
```bash
python ai_agent/utils/scripts/upload_reports.py \
  --pdf reports/samsung_esg_2024.pdf \
  --company "Samsung Electronics" \
  --year 2024 \
  --type ESG
```

#### 배치 업로드 (디렉토리):
```bash
python ai_agent/utils/scripts/upload_reports.py \
  --dir reports/ \
  --batch
```

파일명 형식: `{company}_{year}_{type}.pdf`
예: `Samsung_2024_ESG.pdf`, `LGChem_2023_TCFD.pdf`

### 2. RAGEngine 사용

```python
from ai_agent.utils.rag_helpers import RAGEngine

# RAGEngine 초기화 (Qdrant 자동 연결)
rag = RAGEngine(source="benchmark")

# 검색 수행
results = rag.query(
    query_text="climate governance strategy",
    top_k=5
)

# 결과 확인
for result in results:
    print(f"Company: {result['metadata']['company_name']}")
    print(f"Score: {result['score']}")
    print(f"Text: {result['text'][:200]}...")
```

### 3. ReportAnalysisAgent와 통합

ReportAnalysisAgent는 자동으로 RAGEngine을 사용합니다:

```python
# ai_agent/agents/sub_agents/report_generation/report_analysis_agent.py
rag_engine = RAGEngine(source="benchmark")
references = rag_engine.query(query_text, top_k=20)
```

## 테스트

### 빠른 테스트:
```bash
python ai_agent/utils/scripts/quick_test.py
```

### 전체 통합 테스트:
```bash
# Qdrant 서버 없이 테스트 (Mock 모드)
python ai_agent/utils/scripts/test_qdrant_integration.py --skip-connection-test

# Qdrant 서버 포함 전체 테스트
python ai_agent/utils/scripts/test_qdrant_integration.py
```

## 아키텍처

### 데이터 플로우:

```
PDF 보고서
    ↓
upload_reports.py (파싱, 청킹)
    ↓
QdrantVectorStore (벡터 저장)
    ↓
RAGEngine (검색 인터페이스)
    ↓
ReportAnalysisAgent (보고서 생성)
```

### 컬렉션 스키마:

```python
{
    "vector": [384d float],  # sentence-transformers 임베딩
    "payload": {
        "document_id": str,
        "company_name": str,
        "report_year": int,
        "report_type": str,  # "ESG" or "TCFD"
        "section_type": str,  # "governance", "strategy", etc.
        "content": str,
        "content_summary": str,
        "metadata": dict,
        "tags": [str]
    }
}
```

### 인덱스:
- `company_name` (keyword)
- `report_year` (integer)
- `section_type` (keyword)

## Mock 모드 vs Qdrant 모드

### Mock 모드 (`RAG_MOCK_MODE=true`):
- Qdrant 서버 불필요
- 더미 데이터 반환
- 개발/테스트용

### Qdrant 모드 (`RAG_MOCK_MODE=false`):
- Qdrant 서버 필요
- 실제 벡터 검색 수행
- 프로덕션 환경용

### 자동 Fallback:
Qdrant 연결 실패 시 자동으로 Mock 모드로 전환하여 서비스 안정성 보장

## 성능 목표

- **검색 속도**: < 500ms per query
- **임베딩 생성**: < 100ms per chunk
- **배치 업로드**: > 50 chunks/second

## 문제 해결

### Qdrant 연결 오류:
```
ConnectionError: Cannot connect to Qdrant
```
**해결책**: Qdrant 서버가 실행 중인지 확인
```bash
docker ps | grep qdrant
```

### 임베딩 모델 다운로드 느림:
첫 실행 시 모델 다운로드로 인해 시간이 걸릴 수 있습니다 (약 90MB).
이후 실행부터는 캐시된 모델을 사용합니다.

### 메모리 부족:
대량 업로드 시 `batch_size` 조정:
```python
store.add_documents(documents, batch_size=50)  # 기본값: 100
```

## 디렉토리 구조

```
ai_agent/
├── utils/
│   ├── qdrant_vector_store.py       # Qdrant 클라이언트 래퍼
│   ├── rag_helpers.py                # RAGEngine
│   └── scripts/
│       ├── upload_reports.py         # 보고서 업로드 스크립트
│       ├── test_qdrant_integration.py # 통합 테스트
│       ├── quick_test.py             # 빠른 테스트
│       └── README_QDRANT.md          # 이 문서
└── config/
    └── settings.py                   # RAG_CONFIG 설정
```

## 다음 단계

1. **초기 데이터 마이그레이션**: 기존 ESG/TCFD 보고서 3-5개 업로드
2. **프로덕션 배포**: CD 파이프라인에 Qdrant 환경 변수 추가
3. **모니터링**: 검색 성능 및 품질 메트릭 수집
4. **최적화**: 필요시 임베딩 모델 업그레이드 또는 청킹 전략 개선

## 참고 자료

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Sentence Transformers](https://www.sbert.net/)
- [RAG Pattern](https://python.langchain.com/docs/use_cases/question_answering/)
