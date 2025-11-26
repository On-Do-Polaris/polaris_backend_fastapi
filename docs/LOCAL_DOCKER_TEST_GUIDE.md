# 로컬 Docker 환경 CI/CD 테스트 가이드

> Polaris Backend FastAPI - 로컬에서 Docker 빌드/배포 테스트
>
> 최종 수정일: 2025-11-24
> 버전: v01.0

---

## 📋 목차

1. [개요](#개요)
2. [사전 준비](#사전-준비)
3. [로컬 환경 설정](#로컬-환경-설정)
4. [Docker 빌드 테스트](#docker-빌드-테스트)
5. [Docker 배포 테스트](#docker-배포-테스트)
6. [CI/CD 시뮬레이션](#cicd-시뮬레이션)
7. [문제 해결](#문제-해결)

---

## 개요

이 문서는 실제 GitHub Actions CI/CD를 실행하기 전에 **로컬 환경에서 Docker 빌드 및 배포를 테스트**하는 방법을 안내합니다.

### 테스트 목적

- Docker 이미지 빌드 정상 작동 확인
- 컨테이너 실행 및 애플리케이션 동작 확인
- GitHub Actions 실행 전 사전 검증
- 빠른 디버깅 및 수정

---

## 사전 준비

### 1. 필수 소프트웨어 설치

#### Windows

```powershell
# Docker Desktop 설치
# https://www.docker.com/products/docker-desktop 에서 다운로드 및 설치

# 설치 확인
docker --version
docker-compose --version
```

#### macOS

```bash
# Homebrew로 설치
brew install --cask docker

# 또는 Docker Desktop 직접 설치
# https://www.docker.com/products/docker-desktop

# 설치 확인
docker --version
docker-compose --version
```

#### Linux (Ubuntu)

```bash
# Docker 설치
sudo apt-get update
sudo apt-get install -y docker.io docker-compose

# Docker 서비스 시작
sudo systemctl start docker
sudo systemctl enable docker

# 현재 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER
newgrp docker

# 설치 확인
docker --version
docker-compose --version
```

### 2. 프로젝트 클론

```bash
# 프로젝트 클론
git clone https://github.com/On-Do-Polaris/backend_team.git
cd backend_team
```

---

## 로컬 환경 설정

### 1. .env 파일 생성

프로젝트 루트에 `.env` 파일 생성:

```bash
# .env 파일 생성
touch .env

# 또는 Windows
type nul > .env
```

`.env` 파일 내용 (개발용):

```bash
# =============================================================================
# Local Development Environment
# =============================================================================

# App Settings
DEBUG=True
USE_MOCK_DATA=True

# API Authentication
API_KEY=local-test-api-key-12345

# CORS (로컬 Spring Boot + 프론트엔드 허용)
# host.docker.internal: Docker 컨테이너에서 호스트의 localhost 접근용
CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080,http://host.docker.internal:8080,http://localhost:3000

# Database (로컬 PostgreSQL - port 5433)
# 주의: 로컬에 PostgreSQL이 설치되어 있어야 함
DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:5433/skala_datawarehouse

# OpenAI API (테스트용 - 실제 키 사용 시 주의)
OPENAI_API_KEY=sk-test-fake-key-for-local-testing
LLM_MODEL=gpt-4

# Agent Settings
AGENT_TIMEOUT=300
```

**주의사항:**
- `host.docker.internal`: Docker 컨테이너에서 호스트 머신의 localhost 접근 시 사용
- 실제 데이터베이스가 없다면 `USE_MOCK_DATA=True`로 설정하여 Mock 데이터 사용
- Spring Boot가 호스트에서 실행 중이라면 `http://host.docker.internal:8080` 추가

### 2. 로컬 PostgreSQL 설정 (선택)

실제 DB 연동 테스트를 원한다면:

```bash
# Docker로 PostgreSQL 실행 (port 5433)
docker run -d \
  --name polaris-postgres-test \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=skala_datawarehouse \
  -p 5433:5432 \
  postgis/postgis:16-3.4

# 연결 확인
psql -h localhost -p 5433 -U postgres -d skala_datawarehouse
```

---

## Docker 빌드 테스트

### 1. 수동 빌드 (기본)

```bash
# 이미지 빌드
docker build -t polaris-backend-fastapi:test .

# 빌드 성공 확인
docker images | grep polaris-backend-fastapi
```

**예상 출력:**
```
polaris-backend-fastapi   test    abc123def456   2 minutes ago   250MB
```

### 2. docker-build.sh 스크립트 사용

#### Linux/macOS

```bash
# 실행 권한 부여
chmod +x docker-build.sh

# 로컬 모드로 빌드 (Registry Push 없이)
./docker-build.sh build

# 또는 전체 CI 시뮬레이션 (로그인 + 빌드 + Push)
# 주의: ghcr.io 로그인 필요
export REGISTRY=ghcr.io
export REGISTRY_USERNAME=your-github-username
export REGISTRY_PASSWORD=your-github-token
export TAG=local-test
./docker-build.sh ci
```

#### Windows (PowerShell)

```powershell
# Git Bash 사용 권장
bash docker-build.sh build

# 또는 Docker 명령어 직접 실행
docker build -t polaris-backend-fastapi:test .
```

### 3. 빌드 로그 확인

```bash
# 빌드 과정에서 에러 확인
docker build -t polaris-backend-fastapi:test . 2>&1 | tee build.log

# build.log 파일에서 에러 검색
grep -i error build.log
grep -i fail build.log
```

---

## Docker 배포 테스트

### 1. 컨테이너 실행

#### 방법 1: docker run 직접 실행

```bash
# 컨테이너 실행
docker run -d \
  --name polaris-backend-test \
  -p 8000:8000 \
  --env-file .env \
  --restart unless-stopped \
  polaris-backend-fastapi:test

# 실행 확인
docker ps | grep polaris-backend-test
```

#### 방법 2: docker-deploy.sh 스크립트 사용

```bash
# 실행 권한 부여
chmod +x docker-deploy.sh

# 전체 배포 (빌드 + 실행)
./docker-deploy.sh deploy

# 또는 개별 명령어
./docker-deploy.sh build   # 빌드만
./docker-deploy.sh stop    # 중지 및 삭제
./docker-deploy.sh run     # 실행만
./docker-deploy.sh status  # 상태 확인
```

### 2. 애플리케이션 동작 확인

#### Health Check

```bash
# Health 엔드포인트 확인
curl http://localhost:8000/health

# 예상 응답
{"status":"ok"}
```

#### API 문서 확인

브라우저에서 접속:
```
http://localhost:8000/docs
```

Swagger UI가 정상적으로 표시되어야 합니다.

#### API 테스트

```bash
# API Key 없이 요청 (401 에러 예상)
curl http://localhost:8000/api/v1/analysis/physical-risk

# API Key 포함 요청
curl -H "X-API-Key: local-test-api-key-12345" \
  http://localhost:8000/api/v1/analysis/physical-risk
```

### 3. 로그 확인

```bash
# 실시간 로그 보기
docker logs -f polaris-backend-test

# 최근 100줄 로그
docker logs --tail 100 polaris-backend-test

# 에러만 필터링
docker logs polaris-backend-test 2>&1 | grep -i error
```

### 4. 컨테이너 내부 접속

```bash
# Bash 쉘 접속
docker exec -it polaris-backend-test bash

# 내부에서 확인
ls -la
cat /app/main.py
env | grep DATABASE_URL
exit
```

---

## CI/CD 시뮬레이션

### 1. CI (Continuous Integration) 시뮬레이션

GitHub Actions의 `ci_python.yaml`을 로컬에서 재현:

```bash
# 1. Lint 및 포맷 체크
pip install ruff
ruff check .

# 2. 테스트 실행 (pytest 설치 필요)
pip install pytest pytest-asyncio
pytest tests/ -v

# 3. Docker 이미지 빌드
docker build -t polaris-backend-fastapi:ci-test .

# 4. 이미지 태그 확인
docker images | grep polaris-backend-fastapi

# 5. (선택) ghcr.io에 Push
docker tag polaris-backend-fastapi:ci-test ghcr.io/on-do-polaris/backend_team/polaris-backend-fastapi:latest
docker login ghcr.io -u YOUR_USERNAME -p YOUR_TOKEN
docker push ghcr.io/on-do-polaris/backend_team/polaris-backend-fastapi:latest
```

### 2. CD (Continuous Deployment) 시뮬레이션

GitHub Actions의 `cd_python.yaml`을 로컬에서 재현:

```bash
# 1. 기존 컨테이너 중지
docker stop polaris-backend-test 2>/dev/null || true
docker rm polaris-backend-test 2>/dev/null || true

# 2. 최신 이미지 Pull (Registry 사용 시)
docker pull ghcr.io/on-do-polaris/backend_team/polaris-backend-fastapi:latest

# 3. 새 컨테이너 실행
docker run -d \
  --name polaris-backend-test \
  -p 8000:8000 \
  --env-file .env \
  --restart unless-stopped \
  ghcr.io/on-do-polaris/backend_team/polaris-backend-fastapi:latest

# 4. 배포 확인
curl http://localhost:8000/health
docker logs --tail 50 polaris-backend-test
```

### 3. 전체 파이프라인 테스트 스크립트

`test-cicd.sh` 파일 생성:

```bash
#!/bin/bash

set -e

echo "========================================="
echo "CI/CD 로컬 테스트 시작"
echo "========================================="

# 1. 환경 변수 체크
if [ ! -f .env ]; then
    echo "❌ .env 파일이 없습니다."
    exit 1
fi
echo "✅ .env 파일 확인"

# 2. Docker 실행 확인
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker가 실행되지 않았습니다."
    exit 1
fi
echo "✅ Docker 실행 확인"

# 3. 이미지 빌드
echo "🔨 Docker 이미지 빌드 중..."
docker build -t polaris-backend-fastapi:test .
echo "✅ 빌드 완료"

# 4. 기존 컨테이너 정리
echo "🧹 기존 컨테이너 정리 중..."
docker stop polaris-backend-test 2>/dev/null || true
docker rm polaris-backend-test 2>/dev/null || true
echo "✅ 정리 완료"

# 5. 컨테이너 실행
echo "🚀 컨테이너 실행 중..."
docker run -d \
  --name polaris-backend-test \
  -p 8000:8000 \
  --env-file .env \
  --restart unless-stopped \
  polaris-backend-fastapi:test
echo "✅ 컨테이너 실행 완료"

# 6. Health Check
echo "🏥 Health Check 중..."
sleep 5
HEALTH_STATUS=$(curl -s http://localhost:8000/health | grep -o '"status":"ok"' || true)
if [ -z "$HEALTH_STATUS" ]; then
    echo "❌ Health Check 실패"
    docker logs polaris-backend-test
    exit 1
fi
echo "✅ Health Check 성공"

# 7. 로그 확인
echo "📋 컨테이너 로그:"
docker logs --tail 20 polaris-backend-test

echo "========================================="
echo "✅ 모든 테스트 통과!"
echo "========================================="
echo ""
echo "다음 명령어로 확인 가능:"
echo "  - API 문서: http://localhost:8000/docs"
echo "  - 로그 보기: docker logs -f polaris-backend-test"
echo "  - 컨테이너 중지: docker stop polaris-backend-test"
```

실행:

```bash
chmod +x test-cicd.sh
./test-cicd.sh
```

---

## 문제 해결

### 1. 빌드 실패

#### 문제: "no such file or directory: pyproject.toml"

```bash
# 원인: 잘못된 디렉토리에서 빌드
# 해결: 프로젝트 루트에서 실행
cd /path/to/backend_team
docker build -t polaris-backend-fastapi:test .
```

#### 문제: "failed to solve with frontend dockerfile.v0"

```bash
# 원인: Dockerfile 문법 오류
# 해결: Dockerfile 확인 및 수정
cat Dockerfile

# Docker BuildKit 비활성화 후 재시도
DOCKER_BUILDKIT=0 docker build -t polaris-backend-fastapi:test .
```

### 2. 컨테이너 실행 실패

#### 문제: "port is already allocated"

```bash
# 원인: 포트 8000이 이미 사용 중
# 해결 1: 다른 포트 사용
docker run -d --name polaris-backend-test -p 9000:8000 --env-file .env polaris-backend-fastapi:test

# 해결 2: 기존 프로세스 종료
# Linux/macOS
lsof -ti:8000 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

#### 문제: 컨테이너가 바로 종료됨

```bash
# 원인 확인: 로그 보기
docker logs polaris-backend-test

# 일반적인 원인
# 1. .env 파일 없음 → --env-file 옵션 확인
# 2. 필수 환경변수 누락 → .env 파일 확인
# 3. Python 에러 → 로그에서 traceback 확인
```

### 3. 애플리케이션 에러

#### 문제: "DATABASE_URL is not set"

```bash
# 원인: 환경변수 누락
# 해결: .env 파일 확인
cat .env | grep DATABASE_URL

# 컨테이너 내부에서 확인
docker exec polaris-backend-test env | grep DATABASE_URL
```

#### 문제: Health Check 실패

```bash
# 디버깅
docker logs polaris-backend-test

# 애플리케이션이 시작되지 않았다면
# 1. Python 에러 확인
# 2. 포트 바인딩 확인 (0.0.0.0:8000)
# 3. Uvicorn 실행 확인

# 컨테이너 내부에서 직접 확인
docker exec -it polaris-backend-test bash
curl http://localhost:8000/health
```

### 4. 네트워크 문제

#### 문제: 컨테이너에서 호스트 DB 접근 불가

```bash
# Linux: host.docker.internal 대신 실제 IP 사용
ip addr show docker0

# .env 파일 수정
DATABASE_URL=postgresql://postgres:postgres@172.17.0.1:5433/skala_datawarehouse

# 또는 Docker 네트워크 생성
docker network create polaris-network
docker run --network polaris-network ...
```

### 5. 권한 문제 (Linux)

```bash
# Docker 명령어 실행 시 permission denied
# 해결: docker 그룹에 사용자 추가
sudo usermod -aG docker $USER
newgrp docker

# 또는 sudo 사용
sudo docker build -t polaris-backend-fastapi:test .
```

---

## 체크리스트

### 빌드 전

- [ ] Docker Desktop 실행 중
- [ ] 프로젝트 루트 디렉토리 확인
- [ ] `.env` 파일 생성 및 설정
- [ ] `Dockerfile` 존재 확인
- [ ] 필요한 경우 PostgreSQL 실행

### 빌드 테스트

- [ ] `docker build` 성공
- [ ] 이미지 생성 확인 (`docker images`)
- [ ] 빌드 로그에 에러 없음

### 배포 테스트

- [ ] 컨테이너 실행 성공
- [ ] `docker ps`에서 컨테이너 확인
- [ ] Health Check 성공 (`curl http://localhost:8000/health`)
- [ ] API 문서 접속 가능 (`http://localhost:8000/docs`)
- [ ] 로그에 에러 없음

### CI/CD 시뮬레이션

- [ ] 전체 빌드-배포 파이프라인 성공
- [ ] 기존 컨테이너 교체 성공
- [ ] 무중단 배포 확인

---

## 다음 단계

로컬 테스트가 성공했다면:

1. **GitHub에 Push**
   ```bash
   git add .
   git commit -m "feat: Docker CI/CD 설정"
   git push origin feature/docker-setup
   ```

2. **Pull Request 생성**
   - GitHub에서 PR 생성
   - CI Workflow 자동 실행 확인

3. **Main 브랜치 Merge**
   - PR 승인 및 Merge
   - CD Workflow 자동 실행 확인

4. **실제 서버 배포 확인**
   - [배포 가이드](./ORACLE_SERVER_DEPLOY_GUIDE.md) 참조

---

**문서 작성**: Polaris Backend Team
**최종 수정**: 2025-11-24
**버전**: v01.0
