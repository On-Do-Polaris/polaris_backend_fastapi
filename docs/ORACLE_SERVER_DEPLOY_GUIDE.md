# Oracle 서버 배포 가이드 (GitHub Actions)

> Polaris Backend FastAPI - Oracle Cloud 서버에 GitHub Actions를 통한 자동 배포
>
> 최종 수정일: 2025-11-24
> 버전: v01.0

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

이 문서는 **GitHub Actions를 통해 Oracle Cloud 서버에 자동으로 배포**하는 방법을 안내합니다.

### 배포 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Actions                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  [Push to main] → CI Workflow                              │
│    ├─ Lint & Test                                          │
│    ├─ Docker Build                                          │
│    └─ Push to ghcr.io                                       │
│                                                             │
│  [CI Success] → CD Workflow                                │
│    ├─ SSH to Oracle Server                                 │
│    ├─ Pull latest code                                     │
│    ├─ Pull Docker image                                    │
│    └─ Deploy container                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │  Oracle Cloud     │
                    │  Compute Instance │
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

### 1. Oracle Cloud Compute Instance 생성

#### 1.1. 인스턴스 사양 (권장)

- **Shape**: VM.Standard.E2.1.Micro (Free Tier) 또는 상위
- **OS**: Ubuntu 22.04 LTS
- **CPU**: 1 vCPU 이상
- **RAM**: 1GB 이상 (권장: 2GB+)
- **Disk**: 50GB 이상

#### 1.2. 네트워크 설정

Oracle Cloud Console → Networking → Virtual Cloud Networks

**Ingress Rules (인바운드) 추가:**

```
Source CIDR: 0.0.0.0/0
IP Protocol: TCP
Destination Port: 22 (SSH)
Description: SSH access

Source CIDR: 0.0.0.0/0
IP Protocol: TCP
Destination Port: 8000 (FastAPI)
Description: FastAPI application

Source CIDR: 0.0.0.0/0
IP Protocol: TCP
Destination Port: 80 (HTTP, optional)
Description: HTTP redirect

Source CIDR: 0.0.0.0/0
IP Protocol: TCP
Destination Port: 443 (HTTPS, optional)
Description: HTTPS access
```

**서버 내부 방화벽 설정 (Ubuntu):**

```bash
# 방화벽 규칙 추가
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT

# 규칙 저장
sudo netfilter-persistent save

# 또는 ufw 사용
sudo ufw allow 8000/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. 서버 초기 설정

#### 2.1. SSH 접속

```bash
# SSH 키로 접속
ssh -i ~/.ssh/oracle_cloud_key.pem ubuntu@<ORACLE_SERVER_IP>
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

#### 2.4. 프로젝트 디렉토리 생성

```bash
# 배포 디렉토리 생성
mkdir -p ~/backend_team
cd ~/backend_team

# Git 초기화
git init
git remote add origin https://github.com/On-Do-Polaris/backend_team.git
git fetch
git checkout main
```

#### 2.5. 환경변수 파일 생성

```bash
# .env 파일 생성
vim ~/backend_team/.env
```

`.env` 파일 내용 (운영 환경):

```bash
# =============================================================================
# Polaris Backend FastAPI - Production Environment
# =============================================================================

# App Settings
DEBUG=False
USE_MOCK_DATA=False

# API Authentication (강력한 키로 변경 필수!)
API_KEY=<여기에_강력한_API_키_입력>

# CORS (같은 서버의 Spring Boot 허용)
# Spring Boot(8080)와 FastAPI(8000)가 같은 서버에서 통신
CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080

# Database (Datawarehouse - port 5433)
DATABASE_URL=postgresql://polaris_user:<DB_비밀번호>@<DB_HOST>:5433/skala_datawarehouse
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# OpenAI API
OPENAI_API_KEY=<실제_OpenAI_API_키>
LLM_MODEL=gpt-4-turbo

# Agent Settings
AGENT_TIMEOUT=600
```

**아키텍처 참고 (Oracle 서버 내부 통신):**

```
┌─────────────────────────────────────────────────────────────┐
│                    Oracle Cloud Server                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐       ┌─────────────────┐             │
│  │  Spring Boot    │ ───── │   FastAPI       │             │
│  │  (Port 8080)    │  API  │   (Port 8000)   │             │
│  │  backend_spring │ Call  │   backend_team  │             │
│  └─────────────────┘       └─────────────────┘             │
│         │                          │                        │
│         │    http://localhost:8000/api/v1/...               │
│         └──────────────────────────┘                        │
│                                                             │
│  Spring Boot → FastAPI 호출 예시:                            │
│  POST http://localhost:8000/api/v1/analysis/physical-risk   │
│  Header: X-API-Key: <API_KEY>                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**보안 설정:**

```bash
# .env 파일 권한 설정
chmod 600 ~/backend_team/.env

# .env 파일이 Git에 추가되지 않도록 확인
echo ".env" >> ~/backend_team/.gitignore
```

#### 2.6. PostgreSQL Datawarehouse 설정 (별도 서버)

PostgreSQL이 다른 서버에 있다면:

```bash
# 연결 테스트
psql -h <DB_HOST> -p 5433 -U polaris_user -d skala_datawarehouse

# 연결 성공 확인
\dt
\q
```

### 3. GitHub Container Registry 인증

```bash
# GitHub Personal Access Token 생성 필요
# Settings → Developer settings → Personal access tokens → Tokens (classic)
# Scopes: read:packages

# Docker 로그인
echo "<YOUR_GITHUB_TOKEN>" | docker login ghcr.io -u <YOUR_GITHUB_USERNAME> --password-stdin

# 로그인 확인
docker pull ghcr.io/on-do-polaris/backend_team/polaris-backend-fastapi:latest
```

---

## GitHub Secrets 설정

### 1. GitHub 리포지토리 설정 페이지

```
https://github.com/On-Do-Polaris/backend_team/settings/secrets/actions
```

### 2. 필수 Secrets 추가

| Secret Name | 값 | 예시 |
|------------|-----|------|
| `SERVER_HOST` | Oracle 서버 IP 또는 도메인 | `123.45.67.89` |
| `SERVER_USERNAME` | SSH 사용자명 | `ubuntu` |
| `SERVER_SSH_KEY` | SSH Private Key (전체) | `-----BEGIN RSA PRIVATE KEY-----\n...` |
| `SERVER_PORT` | SSH 포트 (선택, 기본 22) | `22` |
| `DEPLOY_PATH` | 배포 디렉토리 절대 경로 | `/home/ubuntu/backend_team` |

### 3. SSH Private Key 생성 및 등록

#### 3.1. 로컬에서 SSH 키 생성

```bash
# SSH 키 생성
ssh-keygen -t rsa -b 4096 -C "github-actions-deploy" -f ~/.ssh/github_actions_key

# Public Key 출력
cat ~/.ssh/github_actions_key.pub
```

#### 3.2. Oracle 서버에 Public Key 등록

```bash
# Oracle 서버에 접속
ssh -i ~/.ssh/oracle_cloud_key.pem ubuntu@<ORACLE_SERVER_IP>

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
ssh -i ~/.ssh/github_actions_key ubuntu@<ORACLE_SERVER_IP>
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

PR 생성 시 자동으로 CI Workflow 실행:
- ✅ Lint & Test
- ✅ Docker Build
- ✅ Push to ghcr.io

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
2. Oracle 서버에 SSH 접속
3. 최신 코드 Pull
4. Docker 이미지 Pull
5. 기존 컨테이너 중지 및 삭제
6. 새 컨테이너 실행

### 2. 수동 배포

#### 2.1. GitHub Actions 페이지

```
https://github.com/On-Do-Polaris/backend_team/actions
```

#### 2.2. Workflow 수동 실행

- `CD - Deploy` Workflow 선택
- `Run workflow` 버튼 클릭
- 브랜치 선택 (`main`)
- `Run workflow` 실행

### 3. 배포 프로세스 상세

#### CI Workflow (`.github/workflows/ci_python.yaml`)

```yaml
# 1. Lint & Test
- ruff check
- pytest (if exists)

# 2. Docker Build
- docker build -t ghcr.io/on-do-polaris/backend_team/polaris-backend-fastapi:$SHA .

# 3. Push to Registry
- docker login ghcr.io
- docker push ghcr.io/on-do-polaris/backend_team/polaris-backend-fastapi:$SHA
- docker push ghcr.io/on-do-polaris/backend_team/polaris-backend-fastapi:latest
```

#### CD Workflow (`.github/workflows/cd_python.yaml`)

```yaml
# 1. SSH to Oracle Server
- appleboy/ssh-action@v1.0.3

# 2. Server Commands
cd /home/ubuntu/backend_team
git pull origin main
chmod +x ./docker-deploy.sh

# 3. Deploy
export REGISTRY=ghcr.io
export REGISTRY_USERNAME=$GITHUB_ACTOR
export REGISTRY_PASSWORD=$GITHUB_TOKEN
export IMAGE_TAG=$SHA
./docker-deploy.sh deploy
```

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
ssh ubuntu@<ORACLE_SERVER_IP>

# 컨테이너 실행 확인
docker ps | grep polaris-backend-fastapi

# 로그 확인
docker logs polaris-backend-fastapi
```

### 3. 애플리케이션 동작 확인

#### Health Check

```bash
# 서버 내부에서
curl http://localhost:8000/health

# 외부에서
curl http://<ORACLE_SERVER_IP>:8000/health
```

#### API 문서 접속

브라우저에서:
```
http://<ORACLE_SERVER_IP>:8000/docs
```

#### API 테스트

```bash
# API Key 없이 (401 에러 예상)
curl http://<ORACLE_SERVER_IP>:8000/api/v1/analysis/physical-risk

# API Key 포함
curl -H "X-API-Key: <YOUR_API_KEY>" \
  http://<ORACLE_SERVER_IP>:8000/api/v1/analysis/physical-risk
```

### 4. 배포 버전 확인

```bash
# 컨테이너 이미지 태그 확인
docker inspect polaris-backend-fastapi | grep Image

# GitHub Commit SHA 확인
docker inspect polaris-backend-fastapi | grep -A 10 Labels
```

### 5. Spring Boot ↔ FastAPI 통신 테스트

같은 Oracle 서버에서 Spring Boot와 FastAPI가 실행 중인 경우:

```bash
# 1. FastAPI 컨테이너 실행 확인
docker ps | grep polaris-backend-fastapi

# 2. FastAPI Health Check
curl http://localhost:8000/health
# 응답: {"status":"ok"}

# 3. Spring Boot에서 FastAPI 호출 테스트 (서버 내부에서)
curl -X POST http://localhost:8000/api/v1/analysis/physical-risk \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <YOUR_API_KEY>" \
  -d '{
    "site_id": "test-site-001",
    "latitude": 37.5665,
    "longitude": 126.9780,
    "analysis_params": {
      "start_year": 2020,
      "end_year": 2050,
      "scenario_id": 2
    }
  }'

# 4. CORS 확인 (Spring Boot 포트에서 호출 시뮬레이션)
curl -X OPTIONS http://localhost:8000/api/v1/analysis/physical-risk \
  -H "Origin: http://localhost:8080" \
  -H "Access-Control-Request-Method: POST" \
  -v

# 응답 헤더에 다음이 포함되어야 함:
# Access-Control-Allow-Origin: http://localhost:8080
```

**Spring Boot에서 FastAPI 호출 예시 (Java):**

```java
// RestTemplate 사용
RestTemplate restTemplate = new RestTemplate();

HttpHeaders headers = new HttpHeaders();
headers.setContentType(MediaType.APPLICATION_JSON);
headers.set("X-API-Key", apiKey);

Map<String, Object> requestBody = new HashMap<>();
requestBody.put("site_id", "site-001");
requestBody.put("latitude", 37.5665);
requestBody.put("longitude", 126.9780);

HttpEntity<Map<String, Object>> entity = new HttpEntity<>(requestBody, headers);

ResponseEntity<String> response = restTemplate.exchange(
    "http://localhost:8000/api/v1/analysis/physical-risk",
    HttpMethod.POST,
    entity,
    String.class
);
```

---

## 롤백 및 문제 해결

### 1. 이전 버전으로 롤백

#### 방법 1: 특정 이미지 태그로 배포

```bash
# Oracle 서버 접속
ssh ubuntu@<ORACLE_SERVER_IP>

# 사용 가능한 이미지 확인
docker images | grep polaris-backend-fastapi

# 특정 태그로 재배포
docker stop polaris-backend-fastapi
docker rm polaris-backend-fastapi

docker run -d \
  --name polaris-backend-fastapi \
  -p 8000:8000 \
  --env-file ~/backend_team/.env \
  --restart unless-stopped \
  ghcr.io/on-do-polaris/backend_team/polaris-backend-fastapi:<OLD_COMMIT_SHA>
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

1. **SSH 연결 실패**
   - Secrets의 `SERVER_SSH_KEY` 확인
   - 서버 방화벽 확인 (port 22)
   - SSH 키 권한 확인

2. **Docker 이미지 Pull 실패**
   - ghcr.io 로그인 확인
   - 이미지 태그 확인
   - 네트워크 연결 확인

3. **컨테이너 실행 실패**
   - `.env` 파일 확인
   - 포트 충돌 확인 (8000)
   - 로그 확인: `docker logs polaris-backend-fastapi`

#### 서버 로그 확인

```bash
# 컨테이너 로그
docker logs -f polaris-backend-fastapi

# 시스템 로그
sudo journalctl -u docker -n 100
```

### 3. 긴급 복구

#### 컨테이너 재시작

```bash
# 컨테이너 재시작
docker restart polaris-backend-fastapi

# 또는 전체 재배포
cd ~/backend_team
./docker-deploy.sh deploy
```

#### 서버 재부팅

```bash
# 재부팅 (주의: 모든 서비스 중단)
sudo reboot

# 재부팅 후 자동 시작 확인
docker ps | grep polaris-backend-fastapi
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
*/5 * * * * curl -f http://localhost:8000/health || echo "Health check failed" | mail -s "FastAPI Health Check Failed" admin@polaris.com
```

#### Systemd Service (선택)

`/etc/systemd/system/polaris-healthcheck.service`:

```ini
[Unit]
Description=Polaris FastAPI Health Check
After=docker.service

[Service]
Type=oneshot
ExecStart=/usr/bin/curl -f http://localhost:8000/health

[Install]
WantedBy=multi-user.target
```

```bash
# 타이머 설정
sudo systemctl enable polaris-healthcheck.timer
sudo systemctl start polaris-healthcheck.timer
```

### 3. 로그 관리

#### 로그 로테이션

```bash
# Docker 로그 크기 제한 설정
# /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}

# Docker 재시작
sudo systemctl restart docker
```

#### 로그 백업

```bash
# 매일 로그 백업 스크립트
cat > ~/backup-logs.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=~/logs-backup
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d)

docker logs polaris-backend-fastapi > $BACKUP_DIR/app-$DATE.log 2>&1

# 30일 이상 된 로그 삭제
find $BACKUP_DIR -name "app-*.log" -mtime +30 -delete
EOF

chmod +x ~/backup-logs.sh

# Cron Job 추가
crontab -e
# 매일 새벽 2시 실행
0 2 * * * ~/backup-logs.sh
```

### 4. 알림 설정 (선택)

#### Slack Webhook 통합

GitHub Actions에 Slack 알림 추가:

```yaml
# .github/workflows/cd_python.yaml
- name: Slack Notification
  if: always()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK_URL }}
```

---

## 베스트 프랙티스

### 1. 배포 전 체크리스트

- [ ] 로컬에서 테스트 완료
- [ ] PR 리뷰 완료
- [ ] CI 테스트 통과
- [ ] `.env` 파일 최신화
- [ ] Database migration 실행 (필요 시)
- [ ] 배포 시간 공지 (운영 중)

### 2. 배포 후 확인사항

- [ ] Health Check 성공
- [ ] API 문서 접속 확인
- [ ] 주요 API 테스트
- [ ] 로그 에러 확인
- [ ] 리소스 사용량 확인

### 3. 보안 권장사항

- [ ] SSH 포트 변경 (22 → 다른 포트)
- [ ] SSH 비밀번호 로그인 비활성화
- [ ] Fail2ban 설치
- [ ] UFW/iptables 방화벽 설정
- [ ] SSL/TLS 인증서 설치 (HTTPS)
- [ ] 정기적인 보안 업데이트

---

## 부록

### A. 전체 배포 플로우 요약

```
1. 개발자: 코드 수정 → feature 브랜치 Push
2. GitHub: CI Workflow 실행 (테스트, 빌드, Push)
3. 개발자: PR 생성 및 Merge to main
4. GitHub: CD Workflow 실행
5. Oracle 서버: 자동 배포 (Pull, Deploy)
6. 개발자: 배포 확인 (Health Check, 로그)
```

### B. 유용한 명령어 모음

```bash
# 컨테이너 관리
docker ps                           # 실행 중인 컨테이너
docker logs -f <container>          # 실시간 로그
docker exec -it <container> bash    # 컨테이너 접속
docker restart <container>          # 재시작
docker stop <container>             # 중지
docker rm <container>               # 삭제

# 이미지 관리
docker images                       # 이미지 목록
docker pull <image>                 # 이미지 다운로드
docker rmi <image>                  # 이미지 삭제
docker image prune -a               # 미사용 이미지 삭제

# 시스템
docker system df                    # 디스크 사용량
docker system prune                 # 전체 정리 (주의!)

# 네트워크
docker network ls                   # 네트워크 목록
netstat -tuln | grep 8000           # 포트 확인
```

---

**문서 작성**: Polaris Backend Team
**최종 수정**: 2025-11-24
**버전**: v01.0
