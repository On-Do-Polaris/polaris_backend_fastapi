#!/bin/bash

# =============================================================================
# Docker Deploy Script for Polaris Backend FastAPI
# =============================================================================

set -e

# Configuration
REGISTRY="${REGISTRY:-}"
OCIR_NAMESPACE="${OCIR_NAMESPACE:-}"
IMAGE_NAME="${IMAGE_NAME:-polaris-backend-fastapi}"
CONTAINER_NAME="${CONTAINER_NAME:-polaris-backend-fastapi}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
PORT="${PORT:-8000}"
ENV_FILE=".env"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    log_info "Docker is running"
}

# Login to registry (for pulling from OCIR)
login() {
    if [ -z "${REGISTRY}" ]; then
        log_warn "No REGISTRY set. Skipping registry login."
        return 0
    fi

    if [ -z "${REGISTRY_USERNAME}" ] || [ -z "${REGISTRY_PASSWORD}" ]; then
        log_warn "REGISTRY_USERNAME or REGISTRY_PASSWORD not set. Skipping login."
        return 0
    fi

    log_info "Logging in to ${REGISTRY}..."
    echo "${REGISTRY_PASSWORD}" | docker login ${REGISTRY} -u "${REGISTRY_USERNAME}" --password-stdin
    log_info "Login successful"
}

# Pull latest image from registry
pull() {
    # Determine full image path
    if [ -n "${REGISTRY}" ] && [ -n "${OCIR_NAMESPACE}" ]; then
        local full_image="${REGISTRY}/${OCIR_NAMESPACE}/${IMAGE_NAME}:${IMAGE_TAG}"
    else
        local full_image="${IMAGE_NAME}:${IMAGE_TAG}"
    fi

    log_info "Pulling latest image: ${full_image}..."
    docker pull ${full_image}
    log_info "Pull completed successfully"
}

# Build Docker image (local build fallback)
build() {
    log_info "Building Docker image locally: ${IMAGE_NAME}..."
    docker build -t ${IMAGE_NAME}:latest .
    log_info "Build completed successfully"
}

# Stop and remove existing container
stop() {
    if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        log_info "Stopping existing container: ${CONTAINER_NAME}..."
        docker stop ${CONTAINER_NAME} 2>/dev/null || true
        docker rm ${CONTAINER_NAME} 2>/dev/null || true
        log_info "Container stopped and removed"
    else
        log_info "No existing container found"
    fi
}

# Run container
run() {
    log_info "Starting container: ${CONTAINER_NAME}..."

    # Determine full image path
    if [ -n "${REGISTRY}" ] && [ -n "${OCIR_NAMESPACE}" ]; then
        local full_image="${REGISTRY}/${OCIR_NAMESPACE}/${IMAGE_NAME}:${IMAGE_TAG}"
    else
        local full_image="${IMAGE_NAME}:${IMAGE_TAG}"
    fi

    # Check if .env file exists
    ENV_OPTION=""
    if [ -f "${ENV_FILE}" ]; then
        ENV_OPTION="--env-file ${ENV_FILE}"
        log_info "Using environment file: ${ENV_FILE}"
    else
        log_warn "No .env file found. Running without environment file."
    fi

    # Determine network and port configuration
    NETWORK_OPTION=""
    PORT_OPTION=""

    if [ "${USE_WEB_NETWORK}" = "true" ]; then
        # web 네트워크 사용 (포트 포워딩 없이 직접 연결)
        NETWORK_OPTION="--network web"
        log_info "Using web network (no port forwarding)"
    else
        # 기본 포트 포워딩
        PORT_OPTION="-p ${PORT}:8000"
        log_info "Using port forwarding: ${PORT}:8000"
    fi

    docker run -d \
        --name ${CONTAINER_NAME} \
        ${NETWORK_OPTION} \
        ${PORT_OPTION} \
        ${ENV_OPTION} \
        --restart unless-stopped \
        ${full_image}

    log_info "Container started: ${CONTAINER_NAME}"
}

# Show logs
logs() {
    log_info "Showing logs for ${CONTAINER_NAME}..."
    docker logs -f ${CONTAINER_NAME}
}

# Show status
status() {
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        log_info "Container ${CONTAINER_NAME} is running"
        docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.ID}}\t{{.Status}}\t{{.Ports}}"
    else
        log_warn "Container ${CONTAINER_NAME} is not running"
    fi
}

# Health check
health_check() {
    log_info "Performing health check..."

    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        # Try curl first, fallback to wget, then nc
        if docker exec ${CONTAINER_NAME} sh -c "curl -f -s http://localhost:8000/api/v1/health > /dev/null 2>&1 || wget --quiet --tries=1 --spider http://localhost:8000/api/v1/health 2>/dev/null || nc -z localhost 8000" 2>/dev/null; then
            log_info "✓ Container is healthy (${attempt}s elapsed)"
            return 0
        fi

        if [ $attempt -eq $max_attempts ]; then
            log_error "✗ Health check failed after ${max_attempts} attempts"
            log_info "Container logs:"
            docker logs ${CONTAINER_NAME} --tail 20
            return 1
        fi

        log_info "Waiting for container to be ready... (${attempt}/${max_attempts})"
        sleep 1
        attempt=$((attempt + 1))
    done
}

# Full deploy from registry (login + pull + stop + run + health check)
deploy() {
    log_info "Starting full deployment from registry..."
    check_docker
    login
    pull
    stop
    run
    health_check
    log_info "Deployment completed successfully!"
    status
}

# Full deploy with local build (build + stop + run)
deploy_local() {
    log_info "Starting local deployment..."
    check_docker
    build
    stop
    run
    health_check
    log_info "Local deployment completed successfully!"
    status
}

# Clean up unused images
cleanup() {
    log_info "Cleaning up unused Docker images..."
    docker image prune -f
    log_info "Cleanup completed"
}

# Show help
help() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  deploy        Full deployment from registry (login + pull + stop + run + health check)"
    echo "  deploy_local  Full deployment with local build (build + stop + run + health check)"
    echo "  login         Login to registry"
    echo "  pull          Pull image from registry"
    echo "  build         Build Docker image locally"
    echo "  stop          Stop and remove container"
    echo "  run           Run container"
    echo "  logs          Show container logs"
    echo "  status        Show container status"
    echo "  health        Perform health check on running container"
    echo "  cleanup       Remove unused Docker images"
    echo "  help          Show this help message"
    echo ""
    echo "Environment variables:"
    echo "  REGISTRY           Container registry (e.g., icn.ocir.io)"
    echo "  OCIR_NAMESPACE     OCIR namespace"
    echo "  IMAGE_NAME         Image name (default: polaris-backend-fastapi)"
    echo "  CONTAINER_NAME     Container name (default: polaris-backend-fastapi)"
    echo "  IMAGE_TAG          Image tag (default: latest)"
    echo "  PORT               Host port to expose (default: 8000, ignored if USE_WEB_NETWORK=true)"
    echo "  USE_WEB_NETWORK    Use 'web' network without port forwarding (default: false)"
    echo "  REGISTRY_USERNAME  Registry username"
    echo "  REGISTRY_PASSWORD  Registry password/token"
    echo ""
    echo "Examples:"
    echo "  # Deploy from OCIR"
    echo "  REGISTRY=icn.ocir.io OCIR_NAMESPACE=myns IMAGE_TAG=main-abc123 USE_WEB_NETWORK=true $0 deploy"
    echo ""
    echo "  # Local build and deploy"
    echo "  $0 deploy_local"
    echo ""
    echo "  # Deploy with port forwarding"
    echo "  PORT=9000 $0 deploy"
}

# Main
case "${1:-deploy}" in
    deploy)
        deploy
        ;;
    deploy_local)
        deploy_local
        ;;
    login)
        check_docker
        login
        ;;
    pull)
        check_docker
        pull
        ;;
    build)
        check_docker
        build
        ;;
    stop)
        check_docker
        stop
        ;;
    run)
        check_docker
        run
        ;;
    logs)
        logs
        ;;
    status)
        status
        ;;
    health)
        check_docker
        health_check
        ;;
    cleanup)
        check_docker
        cleanup
        ;;
    help|--help|-h)
        help
        ;;
    *)
        log_error "Unknown command: $1"
        help
        exit 1
        ;;
esac
