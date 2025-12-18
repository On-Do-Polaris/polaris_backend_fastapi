#!/bin/bash

################################################################################
# Polaris Backend FastAPI 배포 스크립트
#
# 사용법:
#   ./deploy.sh
#
# 필수 환경변수 (서버에 미리 설정 또는 .env 파일로 관리):
#   - ARTIFACT_REGISTRY_LOCATION
#   - GCP_PROJECT_ID
#   - ARTIFACT_REGISTRY_REPO
#   - GCP_SA_KEY
#   - API_KEY, OPENAI_API_KEY, DB_* 등
################################################################################

set -e  # 에러 발생 시 즉시 종료

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 환경변수 파일 로드 (존재하는 경우)
if [ -f ".env.deploy" ]; then
    log_info "환경변수 파일 로드 중... (.env.deploy)"
    set -a
    source .env.deploy
    set +a
fi

# 필수 환경변수 체크
check_required_env() {
    local required_vars=(
        "ARTIFACT_REGISTRY_LOCATION"
        "GCP_PROJECT_ID"
        "ARTIFACT_REGISTRY_REPO"
        "GCP_SA_KEY"
    )

    local missing_vars=()

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -gt 0 ]; then
        log_error "필수 환경변수가 설정되지 않았습니다:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        echo ""
        echo "다음 중 하나의 방법으로 환경변수를 설정하세요:"
        echo "  1. .env.deploy 파일 생성"
        echo "  2. export 명령어로 환경변수 설정"
        exit 1
    fi
}

# 변수 설정
IMAGE_NAME="polaris-backend-fastapi"
CONTAINER_NAME="polaris-backend-fastapi"
REGISTRY="${ARTIFACT_REGISTRY_LOCATION}-docker.pkg.dev"
PROJECT_ID="${GCP_PROJECT_ID}"
REPO="${ARTIFACT_REGISTRY_REPO}"
IMAGE="${REGISTRY}/${PROJECT_ID}/${REPO}/${IMAGE_NAME}:latest"

# 배포 시작
echo "========================================="
echo "  Polaris Backend FastAPI 배포 시작"
echo "========================================="
echo ""
echo "이미지: ${IMAGE}"
echo "컨테이너: ${CONTAINER_NAME}"
echo ""

# 필수 환경변수 체크
check_required_env

# Docker 설치 확인
if ! command -v docker &> /dev/null; then
    log_error "Docker가 설치되어 있지 않습니다."
    exit 1
fi

# 1. 네트워크 생성 (필요시)
log_info "Docker 네트워크 확인 중..."
if ! docker network inspect web &> /dev/null; then
    log_info "Docker 네트워크 생성 중... (web)"
    docker network create web
else
    log_success "Docker 네트워크 존재 확인 (web)"
fi

# 2. GCP Artifact Registry 인증
log_info "GCP Artifact Registry 인증 중..."
echo "${GCP_SA_KEY}" | docker login -u _json_key --password-stdin "https://${ARTIFACT_REGISTRY_LOCATION}-docker.pkg.dev"
log_success "인증 완료"

# 3. 최신 이미지 pull
log_info "최신 이미지 다운로드 중..."
docker pull "${IMAGE}"
log_success "이미지 다운로드 완료"

# 4. 기존 컨테이너 확인 및 중지
log_info "기존 컨테이너 처리 중..."
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    log_warning "기존 컨테이너 발견, 중지 및 삭제 중..."
    docker stop "${CONTAINER_NAME}" || true
    docker rm "${CONTAINER_NAME}" || true
    log_success "기존 컨테이너 삭제 완료"
else
    log_info "기존 컨테이너 없음 (최초 배포)"
fi

# 5. 새 컨테이너 실행
log_info "새 컨테이너 실행 중... (이름: ${CONTAINER_NAME})"
docker run -d \
  --name "${CONTAINER_NAME}" \
  --network web \
  --restart unless-stopped \
  -p 8000:8000 \
  -e API_KEY="${API_KEY:-}" \
  -e OPENAI_API_KEY="${OPENAI_API_KEY:-}" \
  -e DB_HOST="${DB_HOST:-}" \
  -e DB_PORT="${DB_PORT:-}" \
  -e DB_NAME="${DB_NAME:-}" \
  -e DB_USER="${DB_USER:-}" \
  -e DB_PASSWORD="${DB_PASSWORD:-}" \
  -e USE_MOCK_DATA="${USE_MOCK_DATA:-false}" \
  -e WORKFLOW_MOCK_MODE="${WORKFLOW_MOCK_MODE:-false}" \
  -e LANGSMITH_ENABLED="${LANGSMITH_ENABLED:-false}" \
  -e LANGSMITH_API_KEY="${LANGSMITH_API_KEY:-}" \
  -e LANGSMITH_PROJECT="${LANGSMITH_PROJECT:-}" \
  -e MODELOPS_URL="${MODELOPS_URL:-}" \
  -e MODELOPS_BASE_URL="${MODELOPS_BASE_URL:-}" \
  -e SPRING_BOOT_BASE_URL="${SPRING_BOOT_BASE_URL:-}" \
  -e QDRANT_HOST="${QDRANT_HOST:-}" \
  -e QDRANT_PORT="${QDRANT_PORT:-}" \
  -e QDRANT_STORAGE_PATH="${QDRANT_STORAGE_PATH:-}" \
  -e APPLICATION_DB_HOST="${APPLICATION_DB_HOST:-}" \
  -e APPLICATION_DB_PORT="${APPLICATION_DB_PORT:-}" \
  -e APPLICATION_DB_NAME="${APPLICATION_DB_NAME:-}" \
  -e APPLICATION_DB_USER="${APPLICATION_DB_USER:-}" \
  -e APPLICATION_DB_PASSWORD="${APPLICATION_DB_PASSWORD:-}" \
  "${IMAGE}"

log_success "컨테이너 실행 완료"

# 6. Health check
log_info "Health check 중..."
HEALTH_CHECK_PASSED=false

for i in {1..30}; do
    # curl 우선 시도, 없으면 wget, 둘 다 없으면 nc 사용
    if docker exec "${CONTAINER_NAME}" sh -c "curl -f -s http://localhost:8000/api/v1/health > /dev/null 2>&1 || wget --quiet --tries=1 --spider http://localhost:8000/api/v1/health 2>/dev/null || nc -z localhost 8000" 2>/dev/null; then
        log_success "컨테이너 정상 동작 확인 (${i}초 경과)"
        HEALTH_CHECK_PASSED=true
        break
    fi

    if [ $i -eq 30 ]; then
        log_error "Health check 실패 (30초 타임아웃)"
        log_error "컨테이너 로그:"
        echo "----------------------------------------"
        docker logs "${CONTAINER_NAME}" --tail 20
        echo "----------------------------------------"
        exit 1
    fi

    echo "   대기 중... (${i}/30)"
    sleep 1
done

# 7. 미사용 이미지 정리
log_info "미사용 이미지 정리 중..."
docker image prune -af
log_success "이미지 정리 완료"

# 배포 완료
echo ""
echo "========================================="
echo "  배포 완료"
echo "========================================="
echo ""

# 컨테이너 정보 출력
log_info "컨테이너 정보:"
docker ps --filter name="${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
log_success "배포가 성공적으로 완료되었습니다!"
echo ""
echo "다음 명령어로 로그를 확인할 수 있습니다:"
echo "  docker logs -f ${CONTAINER_NAME}"
