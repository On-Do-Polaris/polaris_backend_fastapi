# GCP 서버 배포 가이드 (GitHub Actions)

> Polaris Backend FastAPI - GCP 서버에 GitHub Actions를 통한 자동 배포
>
> 최종 수정일: 2025-12-02
> 버전: v02.0

---

## 📋 목차

1. [개요](#개요)
2. [서버 사전 설정](#서버-사전-설정)
3. [GitHub Secrets 설정](#github-secrets-설정)
4. [배포 프로세스](#배포-프로세스)
5. [배포 확인](#배포-확인)
6. [롤백 및 문제 해결](#롤백-및-문제-해결)
7. [모니터링](#모니터링)

---

## 개요

이 문서는 **GitHub Actions를 통해 GCP 서버에 자동으로 배포**하는 방법을 안내합니다.

### 배포 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Actions                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [Push to main] → CI Workflow                              │
│    ├─ Lint & Test                                          │
│    ├─ Docker Build                                          │
│    └─ Push to GCP Artifact Registry                        │
│                                                             │
│  [CI Success] → CD Workflow                                │
│    ├─ SSH to GCP Server                                    │
│    ├─ Pull Docker image from Artifact Registry            │
│    └─ Deploy container with env vars from Secrets         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │  GCP Compute      │
                    │  Engine (VM)      │
                    ├───────────────────┤
                    │  Docker Container │
                    │  - FastAPI        │
                    │  - Port 8000      │
                    └───────────────────┘
```

### 배포 트리거

- **자동 배포**: `main` 브랜치에 Push 시
- **수동 배포**: GitHub Actions 페이지에서 수동 실행 가능

---

## 서버 사전 설정

### 1. GCP Compute Engine 인스턴스 생성

#### 1.1. 인스턴스 사양 (권장)

- **Machine type**: e2-small (2 vCPU, 2GB RAM) 또는 상위
- **OS**: Ubuntu 22.04 LTS
- **Boot disk**: 30GB 이상 (Balanced persistent disk)
- **Region**: asia-northeast3 (Seoul)
- **Zone**: asia-northeast3-a

#### 1.2. 네트워크 설정

GCP Console → VPC Network → Firewall

**Firewall Rules 추가:**

1. **SSH 접속 (tcp:22)**
   - Name: `allow-ssh`
   - Targets: All instances in the network
   - Source IP ranges: `0.0.0.0/0`
   - Protocols and ports: `tcp:22`

2. **FastAPI (tcp:8000)**
   - Name: `allow-fastapi`
   - Targets: All instances in the network
   - Source IP ranges: `0.0.0.0/0`
   - Protocols and ports: `tcp:8000`

3. **HTTP/HTTPS (선택)**
   - Name: `allow-http-https`
   - Targets: All instances in the network
   - Source IP ranges: `0.0.0.0/0`
   - Protocols and ports: `tcp:80,tcp:443`

### 2. 서버 초기 설정

#### 2.1. SSH 접속

```bash
# SSH 키로 접속
ssh -i ~/.ssh/gcp_key ubuntu@<GCP_EXTERNAL_IP>
```

#### 2.2. 시스템 업데이트

```bash
# 패키지 업데이트
sudo apt-get update
sudo apt-get upgrade -y

# 필수 패키지 설치
sudo apt-get install -y \
    git \
    curl \
    wget \
    vim \
    ca-certificates \
    gnupg \
    lsb-release
```

#### 2.3. Docker 설치

```bash
# Docker 공식 GPG 키 추가
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Docker 레포지토리 추가
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Docker 설치
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Docker 서비스 시작
sudo systemctl start docker
sudo systemctl enable docker

# ubuntu 사용자를 docker 그룹에 추가
sudo usermod -aG docker ubuntu
newgrp docker

# Docker 설치 확인
docker --version
docker compose version
```

#### 2.4. 네트워크 생성

```bash
# Docker 네트워크 생성 (Vue와 통신용)
docker network create web || true
```

#### 2.5. 환경변수 관리 방식

**중요**: 이 프로젝트는 서버에 `.env` 파일을 사용하지 않습니다.

모든 환경변수는 **GitHub Secrets에서 직접 컨테이너에 주입**됩니다.

**왜 서버 .env를 사용하지 않나요?**
- 보안: 민감한 정보가 서버 파일시스템에 저장되지 않음
- 중앙 관리: GitHub에서 환경변수 통합 관리
- 배포 일관성: CI/CD 파이프라인에서 자동으로 주입
- 변경 용이: GitHub Secrets 수정 후 재배포만 하면 됨

**필요한 환경변수 목록** (GitHub Secrets에 설정):
- `API_KEY`: FastAPI 인증 키
- `OPENAI_API_KEY`: OpenAI API 키
- `DATABASE_URL`: PostgreSQL 연결 문자열
- `USE_MOCK_DATA`: Mock 데이터 사용 여부 (true/false)
- `LANGSMITH_ENABLED`: LangSmith 활성화 (선택)
- `LANGSMITH_API_KEY`: LangSmith API 키 (선택)
- `LANGSMITH_PROJECT`: LangSmith 프로젝트명 (선택)

**수동으로 컨테이너 실행 시** (테스트/디버깅용):
```bash
docker run -d \
  --name polaris-backend-fastapi \
  -p 8000:8000 \
  --network web \
  --restart unless-stopped \
  -e API_KEY="your-api-key" \
  -e OPENAI_API_KEY="your-openai-key" \
  -e DATABASE_URL="postgresql://user:pass@host:5432/db" \
  -e USE_MOCK_DATA="false" \
  asia-northeast3-docker.pkg.dev/your-project/polaris-containers/polaris-backend-fastapi:latest
```

#### 2.6. GCP Artifact Registry 인증 설정

```bash
# GCP Service Account 키 파일 생성 (서버에 저장)
cat > ~/gcp-key.json << 'EOF'
{
  "type": "service_account",
  "project_id": "your-project",
  ...
}
EOF

chmod 600 ~/gcp-key.json

# Docker에 GCP Artifact Registry 인증
cat ~/gcp-key.json | docker login -u _json_key \
  --password-stdin https://asia-northeast3-docker.pkg.dev

# 인증 확인
docker pull asia-northeast3-docker.pkg.dev/your-project/polaris-containers/polaris-backend-fastapi:latest
```

---

## GitHub Secrets 설정

### 1. GitHub 리포지토리 설정 페이지

```
https://github.com/On-Do-Polaris/backend_team/settings/secrets/actions
```

### 2. 필수 Secrets 추가

#### GCP 관련
| Secret Name | 값 | 예시 |
|------------|-----|------|
| `GCP_SA_KEY` | Service Account JSON 키 (전체) | `{"type":"service_account",...}` |
| `GCP_PROJECT_ID` | GCP 프로젝트 ID | `your-gcp-project` |
| `ARTIFACT_REGISTRY_LOCATION` | Registry 위치 | `asia-northeast3` |
| `ARTIFACT_REGISTRY_REPO` | Repository 이름 | `polaris-containers` |

#### 서버 배포 관련
| Secret Name | 값 | 예시 |
|------------|-----|------|
| `SERVER_HOST` | GCP VM 외부 IP | `34.64.123.45` |
| `SERVER_USER` | SSH 사용자명 | `ubuntu` |
| `SERVER_SSH_KEY` | SSH Private Key (전체) | `-----BEGIN RSA PRIVATE KEY-----\n...` |
| `SERVER_PORT` | SSH 포트 (선택, 기본 22) | `22` |

#### 애플리케이션 환경변수
| Secret Name | 값 | 필수 여부 |
|------------|-----|----------|
| `API_KEY` | FastAPI 인증 키 | ✅ 필수 |
| `OPENAI_API_KEY` | OpenAI API 키 | ✅ 필수 (USE_MOCK_DATA=false 시) |
| `DATABASE_URL` | PostgreSQL URL | ✅ 필수 (USE_MOCK_DATA=false 시) |
| `USE_MOCK_DATA` | Mock 데이터 사용 | ✅ 필수 |
| `LANGSMITH_ENABLED` | LangSmith 활성화 | ⚪ 선택 |
| `LANGSMITH_API_KEY` | LangSmith API 키 | ⚪ 선택 |
| `LANGSMITH_PROJECT` | LangSmith 프로젝트명 | ⚪ 선택 |

### 3. SSH Private Key 생성 및 등록

#### 3.1. 로컬에서 SSH 키 생성

```bash
# SSH 키 생성
ssh-keygen -t rsa -b 4096 -C "github-actions-deploy" -f ~/.ssh/github_actions_key

# Public Key 출력
cat ~/.ssh/github_actions_key.pub
```

#### 3.2. GCP 서버에 Public Key 등록

```bash
# GCP 서버에 접속
ssh -i ~/.ssh/gcp_key ubuntu@<GCP_EXTERNAL_IP>

# authorized_keys에 추가
vim ~/.ssh/authorized_keys
# github_actions_key.pub 내용 붙여넣기

# 권한 설정
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

#### 3.3. GitHub Secrets에 Private Key 등록

```bash
# Private Key 출력 (전체 복사)
cat ~/.ssh/github_actions_key
```

GitHub Secrets에 `SERVER_SSH_KEY`로 등록:
- `-----BEGIN RSA PRIVATE KEY-----`부터 `-----END RSA PRIVATE KEY-----`까지 **전체 복사**

### 4. 연결 테스트

```bash
# 로컬에서 새로운 키로 접속 테스트
ssh -i ~/.ssh/github_actions_key ubuntu@<GCP_EXTERNAL_IP>
```

---

## 배포 프로세스

### 1. 자동 배포 (Push to main)

#### 1.1. 코드 수정 및 Push

```bash
# 기능 브랜치에서 작업
git checkout -b feature/new-feature
# ... 코드 수정 ...
git add .
git commit -m "feat: Add new feature"
git push origin feature/new-feature
```

#### 1.2. Pull Request 생성

GitHub에서 Pull Request 생성:
- `feature/new-feature` → `main`

#### 1.3. CI Workflow 자동 실행

PR 생성 또는 main에 push 시 자동으로 CI Workflow 실행:
- ✅ Lint & Test
- ✅ Docker Build
- ✅ Push to GCP Artifact Registry

#### 1.4. PR Merge

CI 성공 후 PR Merge:
```bash
# 또는 로컬에서 직접 Merge
git checkout main
git merge feature/new-feature
git push origin main
```

#### 1.5. CD Workflow 자동 실행

`main` 브랜치 Push 시 자동으로 CD Workflow 실행:
1. CI Workflow 성공 대기
2. GCP 서버에 SSH 접속
3. GCP Artifact Registry 인증
4. 최신 이미지 Pull
5. 기존 컨테이너 중지 및 삭제
6. 새 컨테이너 실행 (환경변수 자동 주입)
7. Health check

---

## 배포 확인

### 1. GitHub Actions 로그 확인

```
https://github.com/On-Do-Polaris/backend_team/actions
```

- ✅ 녹색 체크: 성공
- ❌ 빨간 X: 실패 (로그 확인)

### 2. 서버 접속 확인

```bash
# SSH 접속
ssh ubuntu@<GCP_EXTERNAL_IP>

# 컨테이너 실행 확인
docker ps | grep polaris-backend-fastapi

# 로그 확인
docker logs polaris-backend-fastapi --tail 50
```

### 3. 애플리케이션 동작 확인

#### Health Check

```bash
# 서버 내부에서
curl http://localhost:8000/api/v1/health

# 외부에서
curl http://<GCP_EXTERNAL_IP>:8000/api/v1/health
```

**예상 응답**:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-02T10:00:00Z"
}
```

#### API 문서 접속

브라우저에서:
```
http://<GCP_EXTERNAL_IP>:8000/docs
```

#### 환경변수 확인

```bash
# 컨테이너 내부 환경변수 확인
docker exec polaris-backend-fastapi env | grep -E "USE_MOCK_DATA|API_KEY"

# DATABASE_URL 설정 확인 (전체 출력 주의!)
docker exec polaris-backend-fastapi sh -c 'echo $DATABASE_URL | head -c 20'
```

---

## 롤백 및 문제 해결

### 1. 이전 버전으로 롤백

#### 방법 1: 특정 이미지 태그로 배포

```bash
# GCP 서버 접속
ssh ubuntu@<GCP_EXTERNAL_IP>

# 사용 가능한 이미지 확인
docker images | grep polaris-backend-fastapi

# 특정 태그로 재배포
docker stop polaris-backend-fastapi
docker rm polaris-backend-fastapi

docker run -d \
  --name polaris-backend-fastapi \
  -p 8000:8000 \
  --network web \
  --restart unless-stopped \
  -e API_KEY="your-key" \
  -e OPENAI_API_KEY="your-key" \
  -e DATABASE_URL="your-url" \
  -e USE_MOCK_DATA="true" \
  asia-northeast3-docker.pkg.dev/your-project/polaris-containers/polaris-backend-fastapi:<OLD_TAG>
```

#### 방법 2: Git Revert 후 재배포

```bash
# 로컬에서
git revert <COMMIT_SHA>
git push origin main

# CD Workflow가 자동으로 이전 버전 배포
```

### 2. 배포 실패 시 디버깅

#### GitHub Actions 로그 확인

```
https://github.com/On-Do-Polaris/backend_team/actions
```

**일반적인 에러:**

1. **GCP Artifact Registry 인증 실패**
   - Secrets의 `GCP_SA_KEY` JSON 확인
   - Service Account 권한 확인

2. **SSH 연결 실패**
   - Secrets의 `SERVER_SSH_KEY` 확인
   - 서버 방화벽 확인 (port 22)
   - SSH 키 권한 확인

3. **Docker 이미지 Pull 실패**
   - GCP Artifact Registry 인증 확인
   - 이미지 태그 확인
   - 네트워크 연결 확인

4. **컨테이너 실행 실패**
   - 환경변수 확인 (GitHub Secrets)
   - 포트 충돌 확인 (8000)
   - 로그 확인: `docker logs polaris-backend-fastapi`

#### 서버 로그 확인

```bash
# 컨테이너 로그
docker logs -f polaris-backend-fastapi

# 시스템 로그
sudo journalctl -u docker -n 100
```

---

## 모니터링

### 1. 실시간 모니터링

#### 컨테이너 상태

```bash
# 실시간 로그
docker logs -f polaris-backend-fastapi

# 리소스 사용량
docker stats polaris-backend-fastapi
```

#### 시스템 리소스

```bash
# CPU, 메모리
htop

# 디스크 사용량
df -h

# 네트워크 연결
netstat -tuln | grep 8000
```

### 2. Health Check 자동화

#### Cron Job 설정

```bash
# Cron Job 추가
crontab -e

# 매 5분마다 Health Check
*/5 * * * * curl -f http://localhost:8000/api/v1/health || echo "Health check failed" | mail -s "FastAPI Health Check Failed" admin@polaris.com
```

---

**문서 작성**: Polaris Backend Team
**최종 수정**: 2025-12-02
**버전**: v02.0
