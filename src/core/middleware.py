"""
파일명: middleware.py
최종 수정일: 2025-12-01
버전: v01
파일 개요: FastAPI 미들웨어 (request_id 추적)
"""

import uuid
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("api")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    모든 요청에 request_id 추가 및 로깅

    기능:
    - 각 요청에 고유한 request_id 생성
    - 응답 헤더에 X-Request-ID 추가
    - 요청/응답 로깅 (실행 시간 포함)
    """

    async def dispatch(self, request: Request, call_next):
        # request_id 생성
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # 요청 시작 로깅
        logger.info(
            "Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent", "unknown")
            }
        )

        start_time = time.time()

        try:
            # 다음 미들웨어/핸들러 호출
            response = await call_next(request)
            process_time = time.time() - start_time

            # 응답 헤더에 request_id 추가
            response.headers["X-Request-ID"] = request_id

            # 요청 완료 로깅
            logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "process_time_ms": f"{process_time * 1000:.2f}",
                    "process_time_s": f"{process_time:.3f}"
                }
            )

            return response

        except Exception as e:
            process_time = time.time() - start_time

            # 요청 실패 로깅
            logger.error(
                f"Request failed: {str(e)}",
                extra={
                    "request_id": request_id,
                    "error_type": type(e).__name__,
                    "process_time_s": f"{process_time:.3f}"
                },
                exc_info=True
            )
            raise
