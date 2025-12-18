# Polaris Backend FastAPI 배포 가이드

이 문서는 Shell Script를 사용한 수동 빌드 및 배포 방법을 설명합니다.

## 📋 목차

- [사전 준비](#사전-준비)
- [환경변수 설정](#환경변수-설정)
- [스크립트 사용법](#스크립트-사용법)
- [트러블슈팅](#트러블슈팅)

---

## 🔧 사전 준비

### 필수 소프트웨어

- Docker (20.10 이상)
- Bash Shell (Linux/Mac 기본 제공, Windows는 Git Bash 또는 WSL 사용)
- GCP Service Account Key (JSON 파일)

### 스크립트 파일

프로젝트에는 다음 배포 스크립트가 포함되어 있습니다:

- `build.sh` - Docker 이미지 빌드 및 Push
- `deploy.sh` - 서버 배포
- `build-and-deploy.sh` - 빌드 + 배포 통합 실행
- `.env.deploy.example` - 환경변수 설정 템플릿

---

## ⚙️ 환경변수 설정

### 1. 환경변수 파일 생성

```bash
# 템플릿 파일을 복사
cp .env.deploy.example .env.deploy
```

### 2. 환경변수 파일 수정

`.env.deploy` 파일을 열어 실제 값으로 수정합니다:

```bash
# GCP Artifact Registry 설정
ARTIFACT_REGISTRY_LOCATION=asia-northeast3
GCP_PROJECT_ID=your-gcp-project-id
ARTIFACT_REGISTRY_REPO=your-repo-name

# GCP Service Account Key (JSON 전체를 한 줄로)
GCP_SA_KEY='{"type":"service_account",...}'

# Application 환경변수
API_KEY=your-api-key
OPENAI_API_KEY=sk-...
DB_HOST=localhost
DB_PORT=5432
DB_NAME=polaris_db
DB_USER=polaris_user
DB_PASSWORD=your-db-password

# ... (나머지 환경변수)
```

### 3. 보안 설정

**중요**: `.env.deploy` 파일은 민감한 정보를 포함하므로 절대 Git에 커밋하지 마세요!

```bash
# .gitignore에 추가되어 있는지 확인
echo ".env.deploy" >> .gitignore
```

---

## 🚀 스크립트 사용법

### 방법 1: 빌드만 실행 (로컬 테스트용)

```bash
chmod +x build.sh
./build.sh
```

로컬에서만 이미지를 빌드합니다. Push하지 않습니다.

### 방법 2: 빌드 및 Push

```bash
chmod +x build.sh
./build.sh --push
```

이미지를 빌드하고 GCP Artifact Registry에 Push합니다.

### 방법 3: 배포만 실행

```bash
chmod +x deploy.sh
./deploy.sh
```

이미 Push된 최신 이미지를 서버에 배포합니다.

### 방법 4: 빌드 + 배포 한번에 실행 (권장)

```bash
chmod +x build-and-deploy.sh
./build-and-deploy.sh
```

빌드, Push, 배포를 한 번에 실행합니다.

---

## 📝 각 스크립트 상세 설명

### build.sh

**기능**:
- Docker 이미지 빌드
- (옵션) GCP Artifact Registry에 Push

**필수 환경변수**:
- Push 시: `ARTIFACT_REGISTRY_LOCATION`, `GCP_PROJECT_ID`, `ARTIFACT_REGISTRY_REPO`, `GCP_SA_KEY`

**출력 예시**:
```
=========================================
  Polaris Backend FastAPI 빌드
=========================================

이미지 태그: asia-northeast3-docker.pkg.dev/project-id/repo/polaris-backend-fastapi:latest
Push 여부: true

[INFO] Docker 이미지 빌드 중...
[SUCCESS] 이미지 빌드 완료
[INFO] 빌드 소요 시간: 45초
```

### deploy.sh

**기능**:
- GCP Artifact Registry 인증
- 최신 이미지 Pull
- 기존 컨테이너 중지 및 삭제
- 새 컨테이너 실행
- Health Check
- 미사용 이미지 정리

**필수 환경변수**:
- `ARTIFACT_REGISTRY_LOCATION`, `GCP_PROJECT_ID`, `ARTIFACT_REGISTRY_REPO`, `GCP_SA_KEY`
- Application 환경변수들 (API_KEY, DB_*, 등)

**배포 전략**:
- Recreate 방식 (기존 컨테이너 중지 → 새 컨테이너 실행)
- 약 1-5초 다운타임 발생 가능

**출력 예시**:
```
=========================================
  Polaris Backend FastAPI 배포 시작
=========================================

[INFO] GCP Artifact Registry 인증 중...
[SUCCESS] 인증 완료
[INFO] 최신 이미지 다운로드 중...
[SUCCESS] 이미지 다운로드 완료
[WARNING] 기존 컨테이너 발견, 중지 및 삭제 중...
[SUCCESS] 기존 컨테이너 삭제 완료
[INFO] 새 컨테이너 실행 중...
[SUCCESS] 컨테이너 실행 완료
[INFO] Health check 중...
[SUCCESS] 컨테이너 정상 동작 확인 (3초 경과)
[SUCCESS] 이미지 정리 완료

=========================================
  배포 완료
=========================================
```

### build-and-deploy.sh

**기능**:
- `build.sh --push` 실행
- `deploy.sh` 실행

**필수 환경변수**:
- 모든 환경변수 필요 (build.sh + deploy.sh)

---

## 🔍 트러블슈팅

### 문제 1: 환경변수를 찾을 수 없음

**에러**:
```
[ERROR] 필수 환경변수가 설정되지 않았습니다:
  - ARTIFACT_REGISTRY_LOCATION
  - GCP_PROJECT_ID
```

**해결**:
1. `.env.deploy` 파일이 존재하는지 확인
2. `.env.deploy` 파일에 해당 변수가 설정되어 있는지 확인
3. 또는 export로 직접 설정:
   ```bash
   export ARTIFACT_REGISTRY_LOCATION=asia-northeast3
   export GCP_PROJECT_ID=your-project-id
   ```

### 문제 2: Docker 로그인 실패

**에러**:
```
Error response from daemon: Get "https://...": unauthorized
```

**해결**:
1. GCP_SA_KEY 값이 올바른 JSON 형식인지 확인
2. Service Account에 Artifact Registry Writer 권한이 있는지 확인
3. Service Account Key가 만료되지 않았는지 확인

### 문제 3: Health Check 실패

**에러**:
```
[ERROR] Health check 실패 (30초 타임아웃)
```

**해결**:
1. 컨테이너 로그 확인:
   ```bash
   docker logs polaris-backend-fastapi
   ```
2. 환경변수가 올바르게 설정되었는지 확인
3. 포트 8000이 이미 사용 중인지 확인:
   ```bash
   lsof -i :8000  # Mac/Linux
   netstat -ano | findstr :8000  # Windows
   ```

### 문제 4: 권한 거부 (Permission Denied)

**에러**:
```
bash: ./build.sh: Permission denied
```

**해결**:
```bash
chmod +x build.sh
chmod +x deploy.sh
chmod +x build-and-deploy.sh
```

### 문제 5: Windows에서 스크립트 실행 실패

**해결**:
1. Git Bash 사용:
   - Git for Windows 설치
   - Git Bash에서 스크립트 실행

2. WSL (Windows Subsystem for Linux) 사용:
   ```powershell
   wsl --install
   ```

3. 줄바꿈 문자 변환:
   ```bash
   # Git Bash에서 실행
   dos2unix build.sh
   dos2unix deploy.sh
   dos2unix build-and-deploy.sh
   ```

---

## 📚 추가 명령어

### 컨테이너 로그 보기

```bash
# 실시간 로그
docker logs -f polaris-backend-fastapi

# 최근 100줄
docker logs polaris-backend-fastapi --tail 100
```

### 컨테이너 상태 확인

```bash
docker ps --filter name=polaris-backend-fastapi
```

### 컨테이너 내부 접속

```bash
docker exec -it polaris-backend-fastapi sh
```

### 컨테이너 중지 및 삭제

```bash
docker stop polaris-backend-fastapi
docker rm polaris-backend-fastapi
```

### 이미지 확인

```bash
docker images | grep polaris-backend-fastapi
```

---

## 🔐 보안 권장사항

1. **환경변수 파일 관리**
   - `.env.deploy`를 반드시 `.gitignore`에 추가
   - 민감한 정보는 암호화하여 보관

2. **GCP Service Account**
   - 최소 권한 원칙 적용 (Artifact Registry Reader/Writer만)
   - 정기적으로 Key Rotation

3. **서버 접근**
   - SSH Key 기반 인증 사용
   - 방화벽 설정으로 접근 제한

---

## 💡 팁

### 배포 자동화

cron을 사용하여 정기 배포 설정:

```bash
# crontab -e
# 매일 새벽 3시에 배포
0 3 * * * cd /path/to/project && ./build-and-deploy.sh >> /var/log/deploy.log 2>&1
```

### 빠른 배포

이미 빌드된 이미지가 있다면 `deploy.sh`만 실행하여 배포 시간 단축:

```bash
./deploy.sh  # 1-2분
```

전체 빌드부터 다시 하려면:

```bash
./build-and-deploy.sh  # 3-5분
```

---

## 📞 문의

배포 관련 문제가 발생하면 다음을 확인해주세요:

1. 스크립트 실행 로그
2. Docker 컨테이너 로그
3. GCP Artifact Registry 상태
4. 서버 리소스 상태 (CPU, 메모리, 디스크)
