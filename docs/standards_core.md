요청하신 내용을 반영하여 **[2조.온도(On-Do)] Backend Core (FastAPI) 개발표준 정의서**를 업데이트했습니다.
기존 **8. 협업 표준** 항목을 삭제하고, 요청하신 \*\*커밋 메시지 규칙(Commit Convention)\*\*을 상세히 반영하여 재구성했습니다.

---

# [2조.온도(On-Do)] Backend Core (FastAPI) 개발표준 정의서

## 1\. 개요 및 기술 스택

본 문서는 AI 모델 서빙, 기후 데이터 처리, LLM 에이전트 구동을 담당하는 **Core Server** 개발 표준이다.

### 1.1 기술 스택

- **Language:** Python 3.11.10
- **Framework:** FastAPI 0.115.4 / Uvicorn 0.30.6
- **Package Manager:** uv 0.5.8
- **AI Stack:** LangChain 0.3.7, LangGraph 0.2.11, OpenAI GPT-4o-mini
- **Database:** PostgreSQL 16.x (Main), Qdrant 1.8.3 (Vector)
- **Role:** AI Worker (Management Server로부터 요청 수신, 내부망 통신)

---

## 2\. 프로젝트 구조 (Directory Structure)

```text
app/
├── main.py              # Entry Point (FastAPI 앱 실행)
├── api/
│   └── v1/
│       └── endpoints/   # 도메인별 라우터 (analysis.py, simulation.py)
├── core/                # 핵심 설정
│   ├── config.py        # 환경 변수(.env) 로드
│   └── security.py      # API Key 검증 미들웨어
├── db/                  # 데이터베이스
│   ├── session.py       # DB 세션(Engine) 설정
│   └── models/          # ORM 모델 정의 (SQLAlchemy)
├── services/            # 비즈니스 로직 (Service Layer)
├── agents/              # AI Agent (LangGraph)
│   ├── graphs/          # Workflow(StateGraph) 정의
│   ├── nodes/           # 그래프 노드 로직 (hazard, exposure)
│   ├── tools/           # 도구 (retriever, calculator)
│   └── prompts/         # 프롬프트 템플릿 파일 (.txt)
└── requirements.txt     # 의존성 목록
```

---

## 3\. 코딩 스타일 및 명명 규칙

### 3.1 명명 규칙 (Naming Convention)

- **패키지/모듈(.py):** `snake_case` (예: `risk_analysis.py`)
- **클래스:** `PascalCase` (예: `HazardAnalysisModel`)
- **함수/변수:** `snake_case` (예: `calculate_risk_score`)
- **상수:** `UPPER_CASE` (예: `DEFAULT_TIMEOUT_SEC`)
- **SQL 테이블:** `tb_` + `snake_case` (예: `tb_risk_report`)
- **Vector Collection:** `COL_` + `UPPER_SNAKE_CASE` (예: `COL_CLIMATE_DOCS`)

### 3.2 PEP 8 및 Type Hinting

- **스타일:** PEP 8 준수 (들여쓰기 공백 4칸).
- **Type Hinting:** 모든 함수 인자 및 반환값에 타입 명시 필수.
  ```python
  # Good
  async def analyze(data: Dict[str, Any]) -> AnalysisResult: ...
  # Bad
  def analyze(data): ...
  ```

---

## 4\. FastAPI 구현 표준

### 4.1 라우터 및 비동기 처리

- **URI Prefix:** `/api/v1/{domain}` (예: `/api/v1/analysis`)
- **Async 원칙:**
  - I/O 바운드(DB, 외부 API): `async def` + `await` 사용.
  - CPU 바운드(데이터 연산): `run_in_threadpool` 활용.
- **의존성 주입:** `Depends`를 사용하여 Service 및 DB Session 주입.

### 4.2 API 응답 포맷

Management Server와의 통신을 위해 아래 JSON 포맷을 엄격히 준수한다.

```json
{
  "timestamp": "2025-11-24T10:00:00",
  "status": 200,
  "code": "SUCCESS",
  "message": "처리 완료",
  "data": { ... } // 없을 경우 null
}
```

---

## 5\. AI Agent (LangGraph) 표준

- **StateGraph:** 분석 상태(State)를 정의하고 노드 간 데이터 전달에 사용.
- **Tools:** `app/agents/tools`에 정의하며, 계산(Calculator)과 검색(Retriever) 책임을 분리.
- **Prompt:** 코드가 아닌 `app/agents/prompts/*.txt` 파일로 격리하여 관리.
- **Tracing:** 실행 시 `tags=["user_id", "site_id"]` 메타데이터 포함 필수.

---

## 6\. 데이터베이스 및 파일 관리 표준

### 6.1 RDBMS (PostgreSQL)

- **PK:** 대리키(Surrogate Key) 사용 원칙.
- **JSONB:** AI 모델 메타데이터 등 비정형 속성은 JSONB 타입 사용.
- **공통 컬럼:** `created_at`, `updated_at`, `created_by` 필수 포함.

### 6.2 Vector DB (Qdrant)

- **Metric:** Cosine Similarity 사용.
- **Payload:** 문서 ID, 청크 번호, 타입 등을 JSON으로 저장하여 필터링 지원.

### 6.3 파일 관리

- **임시 경로:** `/tmp/upload/{uuid}` (Docker Volume 사용).
- **운영 경로:** `/ondo/attachments/{yyyy}/{mm}/{dd}`.
- **대용량 파일:** 비동기 처리(Task Queue) 및 스트리밍 방식 적용.

---

## 7\. 운영 지원 표준 (Logging & Exception)

### 7.1 로깅 (Logging)

- **Format:** JSON 구조화 로깅 (`timestamp`, `level`, `module`, `message`, `trace_id`).
- **Level:** DEBUG (개발) \< INFO (운영) \< ERROR (장애).
- **Exception:** ERROR 레벨 로그에는 반드시 `exc_info=True` 포함.

### 7.2 예외 처리 및 에러 코드

- **Global Handler:** 모든 예외는 핸들러에서 포착하여 공통 응답 포맷으로 변환.
- **Error Code:** `[TYPE]-[MODULE]-[CODE]` 형식 (예: `E-AI-001`).
  - **Type:** E (Error), W (Warning)
  - **Module:** AUTH, SITE, AI, COM

---

## 8\. 협업 표준 (Git)

### 8.1 브랜치 전략

- **Branch:** `{type}/{issue_no}-{description}`
  - 예: `feature/101-langgraph-setup`

### 8.2 커밋 메시지 규칙 (Commit Convention)

변경 이력의 명확한 관리를 위해 정의된 형식을 준수한다.

**기본 포맷:**
`[type] 파일명_수정내용`

**[표 8] Commit Type 정의**

| Type       | 설명                  | 사용 시점                      |
| :--------- | :-------------------- | :----------------------------- |
| **add**    | 새로운 파일/기능 추가 | 새 기능, 파일, 모듈 생성 시    |
| **update** | 기존 파일/기능 수정   | 기능 개선, 버그 수정, 리팩토링 |
| **delete** | 파일/기능 삭제        | 불필요한 코드, 파일 제거 시    |

> **참고:** 기존의 `fix`(버그 수정), `refactor`(구조 개선) 등의 타입은 \*\*`update`\*\*로 통합하여 관리한다.

**작성 규칙**

1.  **Atomic Commit:** `git add .` 금지. 파일 단위로 나누어 커밋한다.
2.  **Type 형식:** 반드시 대괄호 `[]`를 사용한다.
3.  **구분자:** 파일명과 수정내용 사이는 언더스코어 `_`로 구분한다.
4.  **내용 작성:** 최대 2문장, "무엇"을 "왜" 변경했는지 명시하며, 마침표(.) 사용을 금지한다.

**작성 예시**

- `[add] user_service_사용자조회기능구현`
- `[update] auth_service_토큰만료시간30분으로변경`
- `[delete] temp_file_테스트파일제거`
