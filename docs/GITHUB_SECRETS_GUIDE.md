# GitHub Secrets 설정 가이드

> Polaris Backend FastAPI - CI/CD 및 배포를 위한 GitHub Secrets 설정
>
> 최종 수정일: 2025-11-24
> 버전: v01.0

---

## 📋 목차

1. [개요](#개요)
2. [GitHub Secrets 설정 방법](#github-secrets-설정-방법)
3. [필수 환경변수 목록](#필수-환경변수-목록)
4. [환경변수 상세 설명](#환경변수-상세-설명)
5. [.env 파일 예시](#env-파일-예시)

---

## 개요

이 문서는 Polaris Backend FastAPI 프로젝트의 CI/CD 파이프라인 및 배포에 필요한 GitHub Secrets 설정 방법을 안내합니다.

### GitHub Secrets 사용 위치

- **CI Workflow** (`.github/workflows/ci_python.yaml`): Docker 이미지 빌드 및 Push
- **CD Workflow** (`.github/workflows/cd_python.yaml`): 서버 배포
- **Runtime** (서버의 `.env` 파일): 애플리케이션 실행 환경변수

---

## GitHub Secrets 설정 방법

### 1. GitHub 리포지토리 설정 페이지 접속

```
https://github.com/On-Do-Polaris/backend_team/settings/secrets/actions
```

또는:

1. GitHub 리포지토리 페이지 → `Settings` 탭
2. 좌측 메뉴 → `Secrets and variables` → `Actions`
3. `New repository secret` 버튼 클릭

### 2. Secret 추가

각 환경변수를 아래 형식으로 추가:

- **Name**: 환경변수 이름 (대문자)
- **Secret**: 환경변수 값

---

## 필수 환경변수 목록

### CI/CD 배포용 Secrets (GitHub Actions)

| Secret 이름 | 필수 여부 | 용도 | 예시 값 |
|------------|---------|------|--------|
| `SERVER_HOST` | ✅ 필수 | 배포 대상 서버 IP 또는 도메인 | `123.45.67.89` 또는 `api.polaris.com` |
| `SERVER_USERNAME` | ✅ 필수 | SSH 접속 사용자명 | `ubuntu` 또는 `root` |
| `SERVER_SSH_KEY` | ✅ 필수 | SSH Private Key (전체 내용) | `-----BEGIN RSA PRIVATE KEY-----\n...` |
| `SERVER_PORT` | ⚠️ 선택 | SSH 포트 (기본값: 22) | `22` |
| `DEPLOY_PATH` | ✅ 필수 | 서버에서 프로젝트 경로 | `/home/ubuntu/backend_team` |

### 애플리케이션 환경변수 (서버 .env 파일)

| 환경변수 | 필수 여부 | 용도 | 예시 값 |
|---------|---------|------|--------|
| `API_KEY` | ✅ 필수 | FastAPI 인증 키 | `your-secret-api-key-here` |
| `DATABASE_URL` | ✅ 필수 | Datawarehouse PostgreSQL 연결 URL (port 5433) | `postgresql://user:pass@localhost:5433/skala_datawarehouse` |
| `OPENAI_API_KEY` | ✅ 필수 | OpenAI API 키 (LLM Agent용) | `sk-proj-...` |
| `CORS_ORIGINS` | ✅ 필수 | 프론트엔드 허용 도메인 (쉼표 구분) | `http://localhost:3000,https://polaris.example.com` |
| `DEBUG` | ⚠️ 선택 | 디버그 모드 (운영환경: False) | `False` |
| `LLM_MODEL` | ⚠️ 선택 | 사용할 LLM 모델 | `gpt-4` 또는 `gpt-4-turbo` |
| `USE_MOCK_DATA` | ⚠️ 선택 | Mock 데이터 사용 여부 (운영환경: False) | `False` |
| `DATABASE_POOL_SIZE` | ⚠️ 선택 | DB 연결 풀 크기 | `5` |
| `DATABASE_MAX_OVERFLOW` | ⚠️ 선택 | DB 연결 풀 최대 오버플로우 | `10` |
| `AGENT_TIMEOUT` | ⚠️ 선택 | Agent 실행 타임아웃 (초) | `300` |

---

## 환경변수 상세 설명

### 1. CI/CD 배포용 Secrets

#### `SERVER_HOST`
- **용도**: SSH 접속 대상 서버 주소
- **형식**: IP 주소 또는 도메인
- **예시**:
  ```
  123.45.67.89
  api.polaris.com
  ```

#### `SERVER_USERNAME`
- **용도**: SSH 접속 사용자명
- **형식**: Linux 사용자명
- **예시**:
  ```
  ubuntu
  ec2-user
  root
  ```

#### `SERVER_SSH_KEY`
- **용도**: SSH Private Key (passwordless 인증)
- **형식**: RSA/ED25519 Private Key 전체 내용
- **생성 방법**:
  ```bash
  # 1. 로컬에서 SSH 키 생성
  ssh-keygen -t rsa -b 4096 -C "github-actions-deploy"

  # 2. Public Key를 서버에 등록
  ssh-copy-id -i ~/.ssh/id_rsa.pub user@server

  # 3. Private Key 내용 복사
  cat ~/.ssh/id_rsa
  ```
- **GitHub Secret 등록 시 주의**:
  - `-----BEGIN RSA PRIVATE KEY-----`부터 `-----END RSA PRIVATE KEY-----`까지 **전체 복사**
  - 줄바꿈 포함해서 그대로 붙여넣기

#### `SERVER_PORT`
- **용도**: SSH 접속 포트
- **기본값**: `22`
- **예시**: `22`, `2222`

#### `DEPLOY_PATH`
- **용도**: 서버에서 프로젝트가 위치한 절대 경로
- **형식**: Linux 절대 경로
- **예시**:
  ```
  /home/ubuntu/backend_team
  /var/www/polaris-backend
  ```

### 2. 애플리케이션 환경변수

#### `API_KEY`
- **용도**: Spring Boot ↔ FastAPI 통신 인증 키
- **형식**: 임의의 강력한 문자열
- **생성 예시**:
  ```bash
  # Python으로 생성
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
- **사용 위치**: `src/core/auth.py`에서 X-API-Key 헤더 검증

#### `DATABASE_URL`
- **용도**: PostgreSQL Datawarehouse 연결 URL
- **형식**: `postgresql://user:password@host:port/database`
- **주의사항**:
  - ⚠️ **Port 5433** 사용 (Datawarehouse)
  - ⚠️ Application DB(5432)와 다름
- **예시**:
  ```
  # psycopg2 (동기)
  postgresql://polaris_user:secure_password@localhost:5433/skala_datawarehouse

  # asyncpg (비동기) - FastAPI에서는 사용 안함
  postgresql+asyncpg://polaris_user:secure_password@localhost:5433/skala_datawarehouse
  ```

#### `OPENAI_API_KEY`
- **용도**: OpenAI API 호출 (LLM Agent 동작)
- **형식**: `sk-proj-...` 또는 `sk-...`
- **발급 위치**: [OpenAI Platform](https://platform.openai.com/api-keys)
- **주의사항**:
  - 절대 GitHub에 직접 커밋하지 말 것
  - 사용량 모니터링 권장

#### `CORS_ORIGINS`
- **용도**: CORS 허용 도메인 설정 (Spring Boot 백엔드, 프론트엔드 등)
- **형식**: 쉼표로 구분된 도메인 목록 또는 `*` (전체 허용)
- **주의사항**:
  - ⚠️ 운영환경에서는 반드시 특정 도메인만 허용
  - `*` 사용 시 보안 취약점 발생 가능
- **예시**:
  ```bash
  # 개발환경 (전체 허용)
  CORS_ORIGINS=*

  # 운영환경 - Oracle 서버 내부 통신 (Spring Boot ↔ FastAPI)
  # 같은 서버에서 Spring Boot(8080)와 FastAPI(8000)가 통신하는 경우
  CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080

  # 운영환경 - 외부 프론트엔드도 허용하는 경우
  CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080,https://polaris.example.com
  ```
- **아키텍처 참고**:
  ```
  ┌─────────────────────────────────────────────────────────┐
  │                    Oracle Cloud Server                  │
  ├─────────────────────────────────────────────────────────┤
  │  ┌─────────────────┐       ┌─────────────────┐         │
  │  │  Spring Boot    │ ───── │   FastAPI       │         │
  │  │  (Port 8080)    │  API  │   (Port 8000)   │         │
  │  └─────────────────┘ Call  └─────────────────┘         │
  │                                                         │
  │  내부 통신: http://localhost:8080 → http://localhost:8000
  └─────────────────────────────────────────────────────────┘
  ```

#### `DEBUG`
- **용도**: FastAPI 디버그 모드 활성화
- **형식**: `True` 또는 `False`
- **권장값**:
  - 개발환경: `True`
  - 운영환경: `False`

#### `LLM_MODEL`
- **용도**: 사용할 OpenAI 모델 지정
- **형식**: 모델명 문자열
- **예시**:
  ```
  gpt-4
  gpt-4-turbo
  gpt-4o
  gpt-3.5-turbo
  ```

#### `USE_MOCK_DATA`
- **용도**: Mock 데이터 사용 여부 (개발/테스트용)
- **형식**: `True` 또는 `False`
- **권장값**:
  - 개발환경: `True` (실제 AI Agent 호출 안함)
  - 운영환경: `False` (실제 AI Agent 동작)

---

## .env 파일 예시

서버에 배포 후 `/home/ubuntu/backend_team/.env` 파일을 생성하세요:

### 개발 환경 (.env.dev)

```bash
# =============================================================================
# Polaris Backend FastAPI - Development Environment
# =============================================================================

# App Settings
DEBUG=True
USE_MOCK_DATA=True

# API Authentication
API_KEY=dev-test-api-key-12345

# CORS (Spring Boot + 프론트엔드 허용)
CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080,http://localhost:3000

# Database (Datawarehouse - port 5433)
DATABASE_URL=postgresql://polaris_user:dev_password@localhost:5433/skala_datawarehouse
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# OpenAI API (개발용)
OPENAI_API_KEY=sk-proj-dev-test-key
LLM_MODEL=gpt-4

# Agent Settings
AGENT_TIMEOUT=300
```

### 운영 환경 (.env.prod)

```bash
# =============================================================================
# Polaris Backend FastAPI - Production Environment
# =============================================================================

# App Settings
DEBUG=False
USE_MOCK_DATA=False

# API Authentication
API_KEY=<강력한_랜덤_API_키>

# CORS (Oracle 서버 내부 통신 - Spring Boot ↔ FastAPI)
CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080

# Database (Datawarehouse - port 5433)
DATABASE_URL=postgresql://polaris_user:<강력한_패스워드>@10.0.1.100:5433/skala_datawarehouse
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# OpenAI API (운영용)
OPENAI_API_KEY=<실제_OpenAI_API_키>
LLM_MODEL=gpt-4-turbo

# Agent Settings
AGENT_TIMEOUT=600
```

---

## 설정 체크리스트

### GitHub Secrets 설정 (필수 5개)

- [ ] `SERVER_HOST` - 서버 IP/도메인
- [ ] `SERVER_USERNAME` - SSH 사용자명
- [ ] `SERVER_SSH_KEY` - SSH Private Key
- [ ] `SERVER_PORT` - SSH 포트 (선택, 기본값 22)
- [ ] `DEPLOY_PATH` - 배포 경로

### 서버 .env 파일 설정 (필수 4개)

- [ ] `API_KEY` - API 인증 키
- [ ] `CORS_ORIGINS` - 프론트엔드 허용 도메인
- [ ] `DATABASE_URL` - Datawarehouse 연결 URL (port 5433)
- [ ] `OPENAI_API_KEY` - OpenAI API 키

### 배포 전 확인사항

- [ ] 서버에 SSH 접속 가능 확인
  ```bash
  ssh -i ~/.ssh/id_rsa user@server
  ```
- [ ] 서버에 Docker 설치 확인
  ```bash
  docker --version
  ```
- [ ] 서버에 `.env` 파일 생성 확인
  ```bash
  ls -la /home/ubuntu/backend_team/.env
  ```
- [ ] PostgreSQL Datawarehouse 접속 확인 (port 5433)
  ```bash
  psql -h localhost -p 5433 -U polaris_user -d skala_datawarehouse
  ```

---

## 보안 주의사항

### ⚠️ 절대 하지 말아야 할 것

1. **GitHub에 직접 커밋 금지**
   - `.env` 파일
   - API 키, 비밀번호
   - SSH Private Key

2. **Public 저장소 주의**
   - Secrets가 노출되지 않도록 Private 저장소 권장
   - Public 저장소라면 Secrets 더블 체크

3. **강력한 비밀번호 사용**
   - `API_KEY`: 최소 32자 이상 랜덤 문자열
   - `DATABASE_URL` 비밀번호: 대소문자, 숫자, 특수문자 조합

### ✅ 권장 사항

1. **Secrets 정기적 교체**
   - API 키: 6개월마다 교체
   - SSH 키: 1년마다 교체

2. **.gitignore 확인**
   ```gitignore
   .env
   .env.*
   *.pem
   *.key
   ```

3. **접근 권한 제한**
   - GitHub Secrets는 Repository Admin만 수정 가능하도록 설정
   - SSH Private Key는 서버 관리자만 접근 가능

---

## 문제 해결

### CI/CD 실패 시

1. **GitHub Actions 로그 확인**
   - Actions 탭 → 실패한 workflow 클릭 → 로그 확인

2. **Secrets 확인**
   ```bash
   # GitHub Secrets 이름 오타 확인
   SERVER_HOST (O)
   server_host (X)
   ```

3. **SSH 연결 테스트**
   ```bash
   ssh -i ~/.ssh/id_rsa user@server "echo 'SSH OK'"
   ```

### 애플리케이션 실행 실패 시

1. **환경변수 확인**
   ```bash
   # 서버에서 확인
   docker logs polaris-backend-fastapi
   ```

2. **Database 연결 확인**
   ```bash
   # Port 5433 확인 (Datawarehouse)
   psql -h localhost -p 5433 -U polaris_user -d skala_datawarehouse
   ```

3. **OpenAI API 키 확인**
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

---

**문서 작성**: Polaris Backend Team
**최종 수정**: 2025-11-24
**버전**: v01.0
