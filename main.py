from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import uvicorn
import logging
import httpx

from src.core.config import settings
from src.core.logging_config import setup_logging
from src.core.middleware import RequestIDMiddleware
from src.routes import (
    analysis_router,
    reports_router,
    simulation_router,
    meta_router,
    recommendation_router,
    dashboard_router,
    past_router
)

# Health Check Router (GCP 배포용)
try:
    from ai_agent.api.health_router import router as health_router
    HEALTH_ROUTER_AVAILABLE = True
except ImportError:
    HEALTH_ROUTER_AVAILABLE = False
    health_router = None

# Production Utilities (Graceful Shutdown)
try:
    from ai_agent.utils.production_utils import (
        get_shutdown_handler,
        get_logger as get_structured_logger
    )
    PRODUCTION_UTILS_AVAILABLE = True
except ImportError:
    PRODUCTION_UTILS_AVAILABLE = False
from src.services.report_service import ReportService
from src.services.analysis_service import AnalysisService

# 로깅 초기화 (앱 시작 시)
log_level = getattr(settings, 'LOG_LEVEL', 'INFO')
setup_logging(level=log_level)
logger = logging.getLogger("api")

# App-level service instances (singletons for resource management)
report_service_instance = None
analysis_service_instance = None

# FastAPI 앱 생성
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    사업장 기후 물리적 리스크 AI Agent 분석 시스템 API

    Spring Boot 서버로부터 요청을 받아 AI Agent를 통해 기후 리스크를 분석하고 결과를 반환합니다.

    주요 기능:
    - AI Agent 기반 물리적 리스크 분석
    - 비동기 작업 처리 및 상태 관리
    - 과거 재난 이력 분석
    - SSP 시나리오별 미래 리스크 전망
    - 재무 영향 분석 (AAL)
    - 취약성 평가
    - 사업장 이전 시뮬레이션
    - LLM 기반 리포트 생성
    - 사용자 제공 추가 데이터 관리
    """,
    docs_url="/docs",
    redoc_url="/redoc",
)

# 미들웨어 등록
# 1. RequestID 미들웨어 (로깅 및 추적용)
app.add_middleware(RequestIDMiddleware)

# 2. CORS 설정 (환경변수로 허용 도메인 설정)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(analysis_router)
app.include_router(reports_router)
app.include_router(simulation_router)
app.include_router(meta_router)
app.include_router(recommendation_router)
app.include_router(dashboard_router)
app.include_router(past_router)

# Health Check 라우터 등록 (GCP Cloud Run / Kubernetes용)
if HEALTH_ROUTER_AVAILABLE and health_router:
    app.include_router(health_router)
    logger.info("Health check router registered at /health")

# 정적 파일 서빙 (API 테스트 콘솔)
try:
    from fastapi.staticfiles import StaticFiles
    from pathlib import Path

    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
        logger.info(f"Static files mounted at /static from {static_dir}")
    else:
        logger.warning(f"Static directory not found: {static_dir}")
except Exception as e:
    logger.warning(f"Failed to mount static files: {e}")


@app.on_event("startup")
async def startup_event():
    """앱 시작 시 이벤트"""
    global report_service_instance, analysis_service_instance

    logger.info("Application starting up")
    logger.info(f"App Name: {settings.APP_NAME}")
    logger.info(f"App Version: {settings.APP_VERSION}")
    logger.info(f"CORS allowed origins: {settings.get_cors_origins()}")
    logger.info(f"Log level: {log_level}")

    # Graceful Shutdown 핸들러 설정 (GCP 배포용)
    if PRODUCTION_UTILS_AVAILABLE:
        shutdown_handler = get_shutdown_handler()
        shutdown_handler.setup_signal_handlers()
        logger.info("Graceful shutdown handler initialized")

    # Initialize app-level services (singletons for resource pooling)
    report_service_instance = ReportService()
    analysis_service_instance = AnalysisService()
    logger.info("App-level services initialized (ReportService, AnalysisService)")

    # Start scratch folder TTL cleanup scheduler
    try:
        from ai_agent.utils.ttl_cleaner import setup_background_cleanup
        from ai_agent.config.settings import load_config

        config = load_config()
        scratch_config = config.get('SCRATCH_SPACE', {})

        if scratch_config.get('auto_cleanup_enabled', True):
            setup_background_cleanup(
                interval_hours=scratch_config.get('cleanup_interval_hours', 1),
                base_path=scratch_config.get('base_path', './scratch')
            )
            logger.info(f"Scratch folder TTL cleanup started (interval: {scratch_config.get('cleanup_interval_hours', 1)}h)")
        else:
            logger.info("Scratch folder auto-cleanup is disabled")
    except Exception as e:
        logger.warning(f"Failed to start scratch folder cleanup: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """앱 종료 시 이벤트"""
    global report_service_instance, analysis_service_instance

    logger.info("Application shutting down")

    # Cleanup services (shutdown thread pools, close connections, etc.)
    if report_service_instance:
        report_service_instance.shutdown()
        logger.info("ReportService shutdown complete")

    if analysis_service_instance and hasattr(analysis_service_instance, 'shutdown'):
        analysis_service_instance.shutdown()
        logger.info("AnalysisService shutdown complete")

    logger.info("All services shut down successfully")


@app.get("/")
async def root():
    """루트 경로 - API 테스트 콘솔로 리다이렉트"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/index.html")


@app.api_route("/modelops-proxy/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def modelops_proxy(path: str, request: Request):
    """ModelOps API 프록시 엔드포인트"""
    import os

    # ModelOps 서버 URL 가져오기
    modelops_url = os.getenv('MODELOPS_BASE_URL', 'http://localhost:8001')
    target_url = f"{modelops_url}/{path}"

    # 쿼리 파라미터 포함
    if request.url.query:
        target_url = f"{target_url}?{request.url.query}"

    # 요청 본문 읽기
    body = await request.body()

    # 헤더 복사 (Host 제외)
    headers = dict(request.headers)
    headers.pop('host', None)

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
            )

            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
            )
        except httpx.RequestError as e:
            logger.error(f"ModelOps proxy error: {e}")
            return Response(
                content=f'{{"error": "Failed to connect to ModelOps server: {str(e)}"}}',
                status_code=503,
                media_type="application/json"
            )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
