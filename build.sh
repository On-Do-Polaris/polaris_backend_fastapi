#!/bin/bash

################################################################################
# Polaris Backend FastAPI 빌드 스크립트
#
# 사용법:
#   ./build.sh [--push]
#
# 옵션:
#   --push: 빌드 후 GCP Artifact Registry에 push
#
# 필수 환경변수 (push 시):
#   - ARTIFACT_REGISTRY_LOCATION
#   - GCP_PROJECT_ID
#   - ARTIFACT_REGISTRY_REPO
#   - GCP_SA_KEY
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

# 인자 파싱
PUSH_IMAGE=false

for arg in "$@"; do
    case $arg in
        --push)
            PUSH_IMAGE=true
            shift
            ;;
        *)
            log_error "알 수 없는 옵션: $arg"
            echo ""
            echo "사용법: ./build.sh [--push]"
            exit 1
            ;;
    esac
done

# 환경변수 파일 로드 (존재하는 경우)
if [ -f ".env.deploy" ]; then
    log_info "환경변수 파일 로드 중... (.env.deploy)"
    set -a
    source .env.deploy
    set +a
fi

# 변수 설정
IMAGE_NAME="polaris-backend-fastapi"

if [ "$PUSH_IMAGE" = true ]; then
    # Push 모드: GCP Artifact Registry 주소 사용
    if [ -z "$ARTIFACT_REGISTRY_LOCATION" ] || [ -z "$GCP_PROJECT_ID" ] || [ -z "$ARTIFACT_REGISTRY_REPO" ]; then
        log_error "Push 모드에는 다음 환경변수가 필요합니다:"
        echo "  - ARTIFACT_REGISTRY_LOCATION"
        echo "  - GCP_PROJECT_ID"
        echo "  - ARTIFACT_REGISTRY_REPO"
        exit 1
    fi

    REGISTRY="${ARTIFACT_REGISTRY_LOCATION}-docker.pkg.dev"
    PROJECT_ID="${GCP_PROJECT_ID}"
    REPO="${ARTIFACT_REGISTRY_REPO}"
    IMAGE_TAG="${REGISTRY}/${PROJECT_ID}/${REPO}/${IMAGE_NAME}:latest"
else
    # 로컬 빌드 모드
    IMAGE_TAG="${IMAGE_NAME}:latest"
fi

# 빌드 시작
echo "========================================="
echo "  Polaris Backend FastAPI 빌드"
echo "========================================="
echo ""
echo "이미지 태그: ${IMAGE_TAG}"
echo "Push 여부: ${PUSH_IMAGE}"
echo ""

# Docker 설치 확인
if ! command -v docker &> /dev/null; then
    log_error "Docker가 설치되어 있지 않습니다."
    exit 1
fi

# Dockerfile 존재 확인
if [ ! -f "Dockerfile" ]; then
    log_error "Dockerfile이 현재 디렉토리에 없습니다."
    exit 1
fi

# 빌드 시작 시간 기록
START_TIME=$(date +%s)

# 1. Docker 이미지 빌드
log_info "Docker 이미지 빌드 중..."
docker build \
    --platform linux/amd64 \
    --tag "${IMAGE_TAG}" \
    --file Dockerfile \
    .

log_success "이미지 빌드 완료"

# 빌드 완료 시간 기록
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

log_info "빌드 소요 시간: ${DURATION}초"

# 2. 이미지 정보 출력
log_info "빌드된 이미지 정보:"
docker images "${IMAGE_TAG}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

# 3. Push (옵션)
if [ "$PUSH_IMAGE" = true ]; then
    echo ""
    log_info "GCP Artifact Registry에 Push 시작..."

    # GCP 인증 확인
    if [ -z "$GCP_SA_KEY" ]; then
        log_error "GCP_SA_KEY 환경변수가 설정되지 않았습니다."
        exit 1
    fi

    # GCP Artifact Registry 인증
    log_info "GCP Artifact Registry 인증 중..."
    echo "${GCP_SA_KEY}" | docker login -u _json_key --password-stdin "https://${ARTIFACT_REGISTRY_LOCATION}-docker.pkg.dev"
    log_success "인증 완료"

    # Push 시작 시간 기록
    PUSH_START_TIME=$(date +%s)

    # 이미지 push
    log_info "이미지 Push 중..."
    docker push "${IMAGE_TAG}"
    log_success "이미지 Push 완료"

    # Push 완료 시간 기록
    PUSH_END_TIME=$(date +%s)
    PUSH_DURATION=$((PUSH_END_TIME - PUSH_START_TIME))

    log_info "Push 소요 시간: ${PUSH_DURATION}초"
fi

# 완료
echo ""
echo "========================================="
echo "  빌드 완료"
echo "========================================="
echo ""

if [ "$PUSH_IMAGE" = true ]; then
    log_success "빌드 및 Push가 성공적으로 완료되었습니다!"
    echo ""
    echo "이미지: ${IMAGE_TAG}"
    echo "총 소요 시간: $((END_TIME - START_TIME + PUSH_DURATION))초"
    echo ""
    echo "이제 배포 스크립트를 실행할 수 있습니다:"
    echo "  ./deploy.sh"
else
    log_success "빌드가 성공적으로 완료되었습니다!"
    echo ""
    echo "이미지: ${IMAGE_TAG}"
    echo "총 소요 시간: ${DURATION}초"
    echo ""
    echo "다음 단계:"
    echo "  1. GCP에 Push: ./build.sh --push"
    echo "  2. 로컬 테스트: docker run -p 8000:8000 ${IMAGE_TAG}"
fi
