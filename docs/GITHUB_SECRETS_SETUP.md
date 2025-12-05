# GitHub Secrets 설정 가이드

**작성일**: 2025-11-28
**버전**: v1.0

---

## 📋 필수 Secrets 목록

GitHub Repository → Settings → Secrets and variables → Actions → New repository secret

### 1. **GCP (Google Cloud Platform) 관련**

| Secret 이름 | 설명 | 예시 값 |
|------------|------|---------|
| `GCP_SA_KEY` | GCP Service Account JSON 키 | `{"type":"service_account",...}` (JSON 전체) |
| `GCP_PROJECT_ID` | GCP 프로젝트 ID | `your-gcp-project-id` |
| `ARTIFACT_REGISTRY_LOCATION` | Artifact Registry 위치 | `asia-northeast3` (서울) |
| `ARTIFACT_REGISTRY_REPO` | Artifact Registry 저장소 이름 | `polaris-containers` |

**GCP Service Account 키 생성 방법**:
1. Google Cloud Console 접속 (https://console.cloud.google.com)
2. IAM & Admin → Service Accounts
3. Create Service Account
   - Name: `github-actions-deployer`
   - Roles:
     - Artifact Registry Writer
     - Artifact Registry Reader
4. Keys → Add Key → Create new key → JSON
5. JSON 파일 전체 내용을 `GCP_SA_KEY`로 등록

**Artifact Registry 생성 방법**:
1. Artifact Registry → Repositories → Create Repository
2. Format: Docker
3. Location type: Region
4. Region: asia-northeast3 (Seoul)
5. Repository name: polaris-containers

---

### 2. **서버 배포 관련**

| Secret 이름 | 설명 | 예시 값 |
|------------|------|---------|
| `SERVER_HOST` | 배포 서버 IP 또는 도메인 | `123.456.789.0` |
| `SERVER_USER` | SSH 사용자명 | `ubuntu` 또는 `opc` |
| `SERVER_SSH_KEY` | SSH Private Key (전체 내용) | `-----BEGIN RSA PRIVATE KEY-----\n...` |

**SSH Key 생성 방법** (서버가 없는 경우):
```bash
# 로컬에서 키 생성
ssh-keygen -t rsa -b 4096 -C "deploy-key"

# Public Key를 서버에 등록
ssh-copy-id -i ~/.ssh/id_rsa.pub user@server-ip

# Private Key 내용 복사 (GitHub Secret에 등록)
cat ~/.ssh/id_rsa
```

---

### 3. **애플리케이션 환경변수**

| Secret 이름 | 설명 | 예시 값 | 필수 여부 |
|------------|------|---------|----------|
| `USE_MOCK_DATA` | Mock 데이터 사용 여부 | `true` (개발) / `false` (운영) | ✅ 필수 |
| `API_KEY` | FastAPI 인증 키 | `your-secret-api-key-here` | ✅ 필수 |
| `OPENAI_API_KEY` | OpenAI API 키 | `sk-proj-...` | AI Agent 사용 시 필수 |
| `DATABASE_URL` | PostgreSQL 연결 문자열 | `postgresql://user:pass@host:5432/db` | 실제 DB 사용 시 필수 |

**OpenAI API Key 발급 방법**:
1. https://platform.openai.com/api-keys 접속
2. Create new secret key
3. 키 복사 후 GitHub Secret에 등록

**DATABASE_URL 형식**:
```
postgresql://유저명:비밀번호@호스트:포트/데이터베이스명
```

예시:
```
postgresql://skala_user:password123@db.example.com:5432/skala_datawarehouse
```

---

### 4. **LangSmith 모니터링 (선택사항)**

LLM 호출 추적 및 모니터링을 위한 설정 (선택사항)

| Secret 이름 | 설명 | 예시 값 | 필수 여부 |
|------------|------|---------|----------|
| `LANGSMITH_ENABLED` | LangSmith 활성화 여부 | `true` / `false` | ⚪ 선택 |
| `LANGSMITH_API_KEY` | LangSmith API 키 | `lsv2_pt_...` | LangSmith 사용 시 필수 |
| `LANGSMITH_PROJECT` | LangSmith 프로젝트명 | `skax-physical-risk-prod` | ⚪ 선택 (기본값: `skax-physical-risk-dev`) |

**LangSmith 설정 방법**:
1. https://smith.langchain.com/ 접속
2. Settings → API Keys → Create API Key
3. 프로젝트 생성 및 이름 설정

---

## 🔧 Secrets 설정 순서

### Step 1: GCP 관련 설정 (이미지 저장소)

```bash
GCP_SA_KEY={"type":"service_account",...}  # JSON 전체
GCP_PROJECT_ID=your-gcp-project-id
ARTIFACT_REGISTRY_LOCATION=asia-northeast3
ARTIFACT_REGISTRY_REPO=polaris-containers
```

### Step 2: 서버 배포 설정

```bash
SERVER_HOST=123.456.789.0
SERVER_USER=ubuntu
SERVER_SSH_KEY=<SSH Private Key 전체 내용>
```

### Step 3: 애플리케이션 기본 설정

**Mock 모드로 시작** (AI Agent 없이 테스트):
```bash
USE_MOCK_DATA=true
API_KEY=test-api-key-change-in-production
```

**운영 모드** (실제 AI Agent 사용):
```bash
USE_MOCK_DATA=false
API_KEY=your-production-api-key
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
DATABASE_URL=postgresql://user:pass@host:5432/db
```

### Step 4: LangSmith 설정 (선택사항)

```bash
LANGSMITH_ENABLED=true
LANGSMITH_API_KEY=lsv2_pt_xxxxxxxxxxxxx
LANGSMITH_PROJECT=skax-physical-risk-prod
```

---

## ✅ 설정 확인 체크리스트

### GCP 및 배포 (필수)
- [ ] `GCP_SA_KEY` 설정됨
- [ ] `GCP_PROJECT_ID` 설정됨
- [ ] `ARTIFACT_REGISTRY_LOCATION` 설정됨
- [ ] `ARTIFACT_REGISTRY_REPO` 설정됨
- [ ] `SERVER_HOST` 설정됨
- [ ] `SERVER_USER` 설정됨
- [ ] `SERVER_SSH_KEY` 설정됨
- [ ] `SERVER_PORT` 설정됨 (선택)

### 애플리케이션 기본 (필수)
- [ ] `USE_MOCK_DATA` 설정됨
- [ ] `API_KEY` 설정됨

### AI Agent 운영 (USE_MOCK_DATA=false 시 필수)
- [ ] `OPENAI_API_KEY` 설정됨
- [ ] `DATABASE_URL` 설정됨

### 모니터링 (선택)
- [ ] `LANGSMITH_ENABLED` 설정됨 (사용 시)
- [ ] `LANGSMITH_API_KEY` 설정됨 (사용 시)
- [ ] `LANGSMITH_PROJECT` 설정됨 (사용 시)

---

## 🚀 배포 모드별 권장 설정

### 1. **개발/테스트 환경** (Mock 모드)

```bash
# 필수만 설정
USE_MOCK_DATA=true
API_KEY=dev-api-key

# AI Agent 관련은 설정 안 해도 됨
# OPENAI_API_KEY (설정 안 함)
# DATABASE_URL (설정 안 함)
```

**장점**:
- OpenAI API 비용 없음
- 데이터베이스 없이도 실행 가능
- 빠른 응답 속도

### 2. **스테이징 환경** (실제 AI 테스트)

```bash
USE_MOCK_DATA=false
API_KEY=staging-api-key
OPENAI_API_KEY=sk-proj-xxxxx
DATABASE_URL=postgresql://user:pass@staging-db:5432/db

# LangSmith로 AI 호출 모니터링
LANGSMITH_ENABLED=true
LANGSMITH_API_KEY=lsv2_pt_xxxxx
LANGSMITH_PROJECT=skax-physical-risk-staging
```

### 3. **운영 환경**

```bash
USE_MOCK_DATA=false
API_KEY=<강력한 랜덤 키>
OPENAI_API_KEY=sk-proj-xxxxx
DATABASE_URL=postgresql://user:pass@prod-db:5432/db

LANGSMITH_ENABLED=true
LANGSMITH_API_KEY=lsv2_pt_xxxxx
LANGSMITH_PROJECT=skax-physical-risk-prod
```

---

## 🔒 보안 주의사항

### ⚠️ 절대 하지 말아야 할 것

1. **Secrets을 코드에 직접 작성하지 마세요**
   ```python
   # ❌ 나쁜 예
   API_KEY = "my-secret-key-123"
   ```

2. **Secrets을 로그에 출력하지 마세요**
   ```bash
   # ❌ 나쁜 예
   echo "API Key: ${{ secrets.API_KEY }}"
   ```

3. **Public 레포지토리에 .env 파일을 커밋하지 마세요**
   ```bash
   # .gitignore에 추가되어 있는지 확인
   cat .gitignore | grep .env
   ```

### ✅ 권장 사항

1. **강력한 API Key 생성**
   ```bash
   # Linux/Mac
   openssl rand -base64 32

   # 결과 예시: gK8h3J9mN2pQ5rS7tU0vW1xY4zA6bC8d
   ```

2. **주기적인 키 교체**
   - API Key: 6개월마다
   - OCIR Token: 1년마다
   - SSH Key: 필요시 (보안 이슈 발생 시)

3. **최소 권한 원칙**
   - OCIR 사용자: 이미지 push/pull 권한만
   - SSH 사용자: 필요한 명령만 실행 가능하도록 제한
   - Database 사용자: 필요한 테이블만 접근 가능

---

## 📞 문제 해결

### CI/CD 파이프라인 실패 시

1. **GCP Artifact Registry 인증 실패**
   ```
   Error: Failed to authenticate with GCP
   ```
   → `GCP_SA_KEY` JSON 형식 확인 (전체 복사 필요)

2. **Artifact Registry push 실패**
   ```
   Error: unauthorized: access denied
   ```
   → Service Account에 Artifact Registry Writer 권한 확인

3. **SSH 연결 실패**
   ```
   Error: Permission denied (publickey)
   ```
   → `SERVER_SSH_KEY` 형식 확인 (전체 내용 포함되어야 함)

4. **컨테이너 실행 실패**
   ```
   Error: container exited with code 1
   ```
   → 서버에서 `docker logs polaris-backend-fastapi` 확인

### 환경변수 누락 확인

컨테이너 내부에서 환경변수 확인:
```bash
docker exec polaris-backend-fastapi env | grep -E "USE_MOCK_DATA|OPENAI_API_KEY|DATABASE_URL"
```

---

**작성자**: Backend Team
**최종 업데이트**: 2025-11-28
**문서 버전**: 1.0
