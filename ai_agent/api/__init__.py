"""
AI Agent API Module
GCP 배포를 위한 API 엔드포인트

작성일: 2025-12-17
"""

from .health_router import router as health_router

__all__ = ["health_router"]
