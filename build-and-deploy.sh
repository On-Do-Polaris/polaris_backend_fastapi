#!/bin/bash

################################################################################
# Polaris Backend FastAPI 통합 빌드 & 배포 스크립트
#
# 사용법:
#   ./build-and-deploy.sh
#
# 이 스크립트는 다음 작업을 순차적으로 수행합니다:
#   1. Docker 이미지 빌드
#   2. GCP Artifact Registry에 Push
#   3. 서버에 배포
################################################################################

set -e  # 에러 발생 시 즉시 종료

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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

log_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# 전체 시작 시간
TOTAL_START_TIME=$(date +%s)

echo "========================================="
echo "  Polaris Backend FastAPI"
echo "  통합 빌드 & 배포"
echo "========================================="
echo ""

# Step 1: 빌드 및 Push
log_step "1/2: Docker 이미지 빌드 및 Push"
echo ""

if [ -f "./build.sh" ]; then
    chmod +x ./build.sh
    ./build.sh --push
else
    log_error "build.sh 스크립트를 찾을 수 없습니다."
    exit 1
fi

echo ""
echo ""

# Step 2: 배포
log_step "2/2: 서버 배포"
echo ""

if [ -f "./deploy.sh" ]; then
    chmod +x ./deploy.sh
    ./deploy.sh
else
    log_error "deploy.sh 스크립트를 찾을 수 없습니다."
    exit 1
fi

# 전체 완료 시간
TOTAL_END_TIME=$(date +%s)
TOTAL_DURATION=$((TOTAL_END_TIME - TOTAL_START_TIME))

echo ""
echo ""
echo "========================================="
echo "  전체 작업 완료"
echo "========================================="
echo ""
log_success "빌드 및 배포가 성공적으로 완료되었습니다!"
echo ""
echo "총 소요 시간: ${TOTAL_DURATION}초"
echo ""
