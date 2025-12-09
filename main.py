from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

from src.core.config import settings
from src.core.logging_config import setup_logging
from src.core.middleware import RequestIDMiddleware
from src.routes import (
    analysis_router,
    reports_router,
    simulation_router,
    meta_router,
    recommendation_router,
    additional_data_router,
    disaster_history_router,
    dashboard_router
)
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
app.include_router(additional_data_router)
app.include_router(disaster_history_router)
app.include_router(dashboard_router)


@app.on_event("startup")
async def startup_event():
    """앱 시작 시 이벤트"""
    global report_service_instance, analysis_service_instance

    logger.info("Application starting up")
    logger.info(f"App Name: {settings.APP_NAME}")
    logger.info(f"App Version: {settings.APP_VERSION}")
    logger.info(f"CORS allowed origins: {settings.get_cors_origins()}")
    logger.info(f"Log level: {log_level}")

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
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
