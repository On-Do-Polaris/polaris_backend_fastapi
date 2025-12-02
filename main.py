from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

from src.core.config import settings
from src.core.logging_config import setup_logging
from src.core.middleware import RequestIDMiddleware
from src.routes import analysis_router, reports_router, simulation_router, meta_router, recommendation_router, additional_data_router, disaster_history_router

# 로깅 초기화 (앱 시작 시)
log_level = getattr(settings, 'LOG_LEVEL', 'INFO')
setup_logging(level=log_level)
logger = logging.getLogger("api")

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


@app.on_event("startup")
async def startup_event():
    """앱 시작 시 이벤트"""
    logger.info("Application starting up")
    logger.info(f"App Name: {settings.APP_NAME}")
    logger.info(f"App Version: {settings.APP_VERSION}")
    logger.info(f"CORS allowed origins: {settings.get_cors_origins()}")
    logger.info(f"Log level: {log_level}")


@app.on_event("shutdown")
async def shutdown_event():
    """앱 종료 시 이벤트"""
    logger.info("Application shutting down")


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
