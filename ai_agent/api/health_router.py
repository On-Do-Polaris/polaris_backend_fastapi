"""
Health Check API Router
GCP Cloud Run / Kubernetes 헬스체크용 엔드포인트

작성일: 2025-12-17
버전: v1.0

엔드포인트:
- GET /health          : 기본 헬스체크 (liveness)
- GET /health/ready    : 준비 상태 체크 (readiness)
- GET /health/detailed : 상세 헬스체크 (모든 의존성)
"""

import os
import asyncio
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

# 프로덕션 유틸리티
try:
    from ..utils.production_utils import (
        get_health_checker,
        get_logger,
        HealthChecker,
        HealthStatus
    )
except ImportError:
    # 개발 환경 fallback
    get_health_checker = None
    get_logger = None


router = APIRouter(prefix="/health", tags=["Health Check"])


# =============================================================================
# Response Models
# =============================================================================

class HealthResponse(BaseModel):
    """기본 헬스 응답"""
    status: str
    timestamp: str
    version: str = "2.1.0"


class DetailedHealthResponse(BaseModel):
    """상세 헬스 응답"""
    status: str
    timestamp: str
    version: str
    checks: Dict[str, Any]
    uptime_seconds: float


# =============================================================================
# Global State
# =============================================================================

_startup_time = datetime.utcnow()


# =============================================================================
# Health Check Functions
# =============================================================================

async def check_database() -> Dict[str, Any]:
    """DB 연결 상태 확인"""
    from sqlalchemy import create_engine, text

    app_db_url = os.getenv("APPLICATION_DATABASE_URL")
    if not app_db_url:
        return {"connected": False, "error": "DATABASE_URL not configured"}

    try:
        engine = create_engine(app_db_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        return {"connected": True, "type": "postgresql"}
    except Exception as e:
        return {"connected": False, "error": str(e)}


async def check_qdrant() -> Dict[str, Any]:
    """Qdrant 벡터DB 상태 확인"""
    qdrant_url = os.getenv("QDRANT_URL")
    if not qdrant_url:
        return {"connected": False, "error": "QDRANT_URL not configured"}

    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(url=qdrant_url)
        collections = client.get_collections()
        return {
            "connected": True,
            "collections_count": len(collections.collections)
        }
    except Exception as e:
        return {"connected": False, "error": str(e)}


async def check_openai() -> Dict[str, Any]:
    """OpenAI API 상태 확인"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"configured": False, "error": "OPENAI_API_KEY not configured"}

    try:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model="gpt-4o-mini", max_tokens=5)
        # 간단한 ping 테스트
        response = await asyncio.wait_for(
            llm.ainvoke("Hi"),
            timeout=10
        )
        return {"configured": True, "model": "gpt-4o-mini", "status": "operational"}
    except asyncio.TimeoutError:
        return {"configured": True, "status": "timeout"}
    except Exception as e:
        return {"configured": True, "status": "error", "error": str(e)}


async def check_langsmith() -> Dict[str, Any]:
    """LangSmith 상태 확인"""
    enabled = os.getenv("LANGSMITH_ENABLED", "false").lower() == "true"
    api_key = os.getenv("LANGSMITH_API_KEY")

    if not enabled:
        return {"enabled": False}

    if not api_key:
        return {"enabled": True, "configured": False, "error": "LANGSMITH_API_KEY not set"}

    return {
        "enabled": True,
        "configured": True,
        "project": os.getenv("LANGSMITH_PROJECT", "default")
    }


# =============================================================================
# API Endpoints
# =============================================================================

@router.get("", response_model=HealthResponse)
async def health_check():
    """
    기본 헬스체크 (Liveness Probe)

    GCP Cloud Run / Kubernetes liveness probe용
    서비스가 실행 중인지만 확인
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat() + "Z"
    )


@router.get("/ready", response_model=HealthResponse)
async def readiness_check():
    """
    준비 상태 체크 (Readiness Probe)

    필수 의존성(DB, OpenAI)이 준비되었는지 확인
    """
    # DB 체크
    db_status = await check_database()
    if not db_status.get("connected"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database not ready: {db_status.get('error')}"
        )

    # OpenAI 체크 (API 키만 확인)
    openai_status = await check_openai()
    if not openai_status.get("configured"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI API not configured"
        )

    return HealthResponse(
        status="ready",
        timestamp=datetime.utcnow().isoformat() + "Z"
    )


@router.get("/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check():
    """
    상세 헬스체크

    모든 의존성 상태를 상세히 반환
    모니터링 대시보드용
    """
    # 모든 체크 병렬 실행
    db_check, qdrant_check, openai_check, langsmith_check = await asyncio.gather(
        check_database(),
        check_qdrant(),
        check_openai(),
        check_langsmith(),
        return_exceptions=True
    )

    checks = {
        "database": db_check if not isinstance(db_check, Exception) else {"error": str(db_check)},
        "qdrant": qdrant_check if not isinstance(qdrant_check, Exception) else {"error": str(qdrant_check)},
        "openai": openai_check if not isinstance(openai_check, Exception) else {"error": str(openai_check)},
        "langsmith": langsmith_check if not isinstance(langsmith_check, Exception) else {"error": str(langsmith_check)}
    }

    # 전체 상태 결정
    all_healthy = all(
        check.get("connected", True) or check.get("configured", True) or check.get("enabled", True)
        for check in checks.values()
        if isinstance(check, dict)
    )

    # Uptime 계산
    uptime = (datetime.utcnow() - _startup_time).total_seconds()

    return DetailedHealthResponse(
        status="healthy" if all_healthy else "degraded",
        timestamp=datetime.utcnow().isoformat() + "Z",
        version="2.1.0",
        checks=checks,
        uptime_seconds=round(uptime, 2)
    )


@router.get("/live")
async def liveness():
    """
    간단한 liveness 체크 (GKE/Cloud Run용)
    """
    return {"status": "ok"}
