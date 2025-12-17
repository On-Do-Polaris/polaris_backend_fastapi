"""
Production Utilities for GCP Deployment
GCP 배포를 위한 프로덕션 유틸리티 모음

작성일: 2025-12-17
버전: v1.0

포함 기능:
1. Structured Logging (JSON 형식)
2. Health Check
3. Retry with Exponential Backoff
4. Rate Limit Handler
5. Graceful Shutdown
6. LangSmith 통합 트레이싱
"""

import os
import sys
import json
import time
import signal
import asyncio
import logging
import functools
from datetime import datetime
from typing import Any, Callable, Dict, Optional, TypeVar, Union
from enum import Enum

# Type variable for generic retry decorator
T = TypeVar('T')


# =============================================================================
# 1. Structured Logging (JSON 형식 - Cloud Logging 호환)
# =============================================================================

class LogLevel(Enum):
    """Cloud Logging 호환 로그 레벨"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class StructuredLogger:
    """
    GCP Cloud Logging 호환 JSON 로거

    Usage:
        logger = StructuredLogger("tcfd_report")
        logger.info("Processing started", site_count=8, user_id="123")
    """

    def __init__(self, service_name: str = "ai_agent", environment: str = None):
        self.service_name = service_name
        self.environment = environment or os.getenv("ENVIRONMENT", "development")
        self.logger = logging.getLogger(service_name)

        # 프로덕션에서는 JSON 포맷, 개발에서는 일반 포맷
        if self.environment == "production":
            self._setup_json_handler()
        else:
            self._setup_console_handler()

    def _setup_json_handler(self):
        """JSON 형식 핸들러 설정 (GCP Cloud Logging 호환)"""
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter(self.service_name))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def _setup_console_handler(self):
        """콘솔 핸들러 설정 (개발 환경)"""
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)

    def _log(self, level: LogLevel, message: str, **kwargs):
        """로그 메시지 출력"""
        extra = {
            "service": self.service_name,
            "environment": self.environment,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            **kwargs
        }

        log_method = getattr(self.logger, level.value.lower())
        log_method(message, extra={"structured_data": extra})

    def debug(self, message: str, **kwargs):
        self._log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        self._log(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        self._log(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, error: Exception = None, **kwargs):
        if error:
            kwargs["error_type"] = type(error).__name__
            kwargs["error_message"] = str(error)
        self._log(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        self._log(LogLevel.CRITICAL, message, **kwargs)


class JsonFormatter(logging.Formatter):
    """GCP Cloud Logging 호환 JSON 포매터"""

    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "serviceContext": {
                "service": self.service_name
            }
        }

        # 추가 구조화 데이터 병합
        if hasattr(record, "structured_data"):
            log_entry.update(record.structured_data)

        return json.dumps(log_entry, ensure_ascii=False)


# 전역 로거 인스턴스
_logger: Optional[StructuredLogger] = None


def get_logger(service_name: str = "tcfd_report") -> StructuredLogger:
    """전역 로거 인스턴스 반환"""
    global _logger
    if _logger is None:
        _logger = StructuredLogger(service_name)
    return _logger


# =============================================================================
# 2. Retry with Exponential Backoff
# =============================================================================

class RetryConfig:
    """재시도 설정"""
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        retryable_exceptions: tuple = (Exception,)
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retryable_exceptions = retryable_exceptions


def retry_with_backoff(config: RetryConfig = None):
    """
    Exponential Backoff 재시도 데코레이터

    Usage:
        @retry_with_backoff(RetryConfig(max_retries=3))
        async def call_llm():
            ...
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            logger = get_logger()
            last_exception = None

            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except config.retryable_exceptions as e:
                    last_exception = e

                    if attempt < config.max_retries:
                        delay = min(
                            config.base_delay * (config.exponential_base ** attempt),
                            config.max_delay
                        )
                        logger.warning(
                            f"Retry {attempt + 1}/{config.max_retries}",
                            function=func.__name__,
                            error=str(e),
                            delay_seconds=delay
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"Max retries exceeded",
                            function=func.__name__,
                            error=e
                        )

            raise last_exception

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            logger = get_logger()
            last_exception = None

            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except config.retryable_exceptions as e:
                    last_exception = e

                    if attempt < config.max_retries:
                        delay = min(
                            config.base_delay * (config.exponential_base ** attempt),
                            config.max_delay
                        )
                        logger.warning(
                            f"Retry {attempt + 1}/{config.max_retries}",
                            function=func.__name__,
                            error=str(e),
                            delay_seconds=delay
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"Max retries exceeded",
                            function=func.__name__,
                            error=e
                        )

            raise last_exception

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# =============================================================================
# 3. Rate Limit Handler (OpenAI API 등)
# =============================================================================

class RateLimitHandler:
    """
    API Rate Limit 핸들러

    Usage:
        rate_limiter = RateLimitHandler(requests_per_minute=60)
        await rate_limiter.acquire()
        response = await call_api()
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        tokens_per_minute: int = 150000
    ):
        self.requests_per_minute = requests_per_minute
        self.tokens_per_minute = tokens_per_minute
        self.request_times: list = []
        self.token_usage: list = []
        self._lock = asyncio.Lock()

    async def acquire(self, estimated_tokens: int = 0):
        """Rate limit 확인 및 대기"""
        async with self._lock:
            current_time = time.time()

            # 1분 이전 요청 제거
            self.request_times = [
                t for t in self.request_times
                if current_time - t < 60
            ]
            self.token_usage = [
                (t, tokens) for t, tokens in self.token_usage
                if current_time - t < 60
            ]

            # 요청 수 제한 확인
            if len(self.request_times) >= self.requests_per_minute:
                wait_time = 60 - (current_time - self.request_times[0])
                if wait_time > 0:
                    logger = get_logger()
                    logger.warning(
                        "Rate limit reached, waiting",
                        wait_seconds=wait_time,
                        requests_in_window=len(self.request_times)
                    )
                    await asyncio.sleep(wait_time)

            # 토큰 제한 확인
            total_tokens = sum(tokens for _, tokens in self.token_usage)
            if total_tokens + estimated_tokens > self.tokens_per_minute:
                wait_time = 60 - (current_time - self.token_usage[0][0])
                if wait_time > 0:
                    logger = get_logger()
                    logger.warning(
                        "Token limit reached, waiting",
                        wait_seconds=wait_time,
                        tokens_used=total_tokens
                    )
                    await asyncio.sleep(wait_time)

            # 현재 요청 기록
            self.request_times.append(time.time())
            if estimated_tokens > 0:
                self.token_usage.append((time.time(), estimated_tokens))

    def record_tokens(self, actual_tokens: int):
        """실제 사용 토큰 기록"""
        if self.token_usage:
            # 마지막 예상치를 실제 값으로 업데이트
            self.token_usage[-1] = (self.token_usage[-1][0], actual_tokens)


# 전역 Rate Limiter
_rate_limiter: Optional[RateLimitHandler] = None


def get_rate_limiter() -> RateLimitHandler:
    """전역 Rate Limiter 인스턴스 반환"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimitHandler(
            requests_per_minute=int(os.getenv("OPENAI_RPM", "60")),
            tokens_per_minute=int(os.getenv("OPENAI_TPM", "150000"))
        )
    return _rate_limiter


# =============================================================================
# 4. Health Check
# =============================================================================

class HealthStatus(Enum):
    """헬스 체크 상태"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthChecker:
    """
    서비스 헬스 체크

    Usage:
        health = HealthChecker()
        health.register_check("database", check_db_connection)
        status = await health.check_all()
    """

    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self.last_check_time: Optional[datetime] = None
        self.last_status: Optional[Dict] = None

    def register_check(self, name: str, check_func: Callable):
        """헬스 체크 함수 등록"""
        self.checks[name] = check_func

    async def check_all(self) -> Dict[str, Any]:
        """모든 헬스 체크 실행"""
        results = {}
        overall_status = HealthStatus.HEALTHY

        for name, check_func in self.checks.items():
            try:
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()

                results[name] = {
                    "status": "healthy",
                    "details": result
                }
            except Exception as e:
                results[name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                overall_status = HealthStatus.UNHEALTHY

        self.last_check_time = datetime.utcnow()
        self.last_status = {
            "status": overall_status.value,
            "timestamp": self.last_check_time.isoformat() + "Z",
            "checks": results
        }

        return self.last_status


# 전역 Health Checker
_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """전역 Health Checker 인스턴스 반환"""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


# =============================================================================
# 5. Graceful Shutdown Handler
# =============================================================================

class GracefulShutdown:
    """
    Graceful Shutdown 핸들러

    Usage:
        shutdown = GracefulShutdown()
        shutdown.register_cleanup(cleanup_db)
        shutdown.setup_signal_handlers()
    """

    def __init__(self):
        self.cleanup_handlers: list = []
        self.is_shutting_down = False
        self._shutdown_event = asyncio.Event() if asyncio.get_event_loop().is_running() else None

    def register_cleanup(self, handler: Callable):
        """정리 핸들러 등록"""
        self.cleanup_handlers.append(handler)

    def setup_signal_handlers(self):
        """시그널 핸들러 설정"""
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """시그널 핸들러"""
        logger = get_logger()
        logger.info(f"Received signal {signum}, initiating graceful shutdown")
        self.is_shutting_down = True

        # 정리 핸들러 실행
        for handler in self.cleanup_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    asyncio.create_task(handler())
                else:
                    handler()
            except Exception as e:
                logger.error("Cleanup handler failed", error=e)

        logger.info("Graceful shutdown complete")
        sys.exit(0)

    def check_shutdown(self) -> bool:
        """셧다운 상태 확인"""
        return self.is_shutting_down


# 전역 Shutdown Handler
_shutdown_handler: Optional[GracefulShutdown] = None


def get_shutdown_handler() -> GracefulShutdown:
    """전역 Shutdown Handler 인스턴스 반환"""
    global _shutdown_handler
    if _shutdown_handler is None:
        _shutdown_handler = GracefulShutdown()
    return _shutdown_handler


# =============================================================================
# 6. LangSmith 통합 트레이싱 래퍼
# =============================================================================

def trace_node(node_name: str, node_type: str = "workflow_node"):
    """
    노드 실행 트레이싱 데코레이터
    LangSmith + 로컬 로깅 통합

    Usage:
        @trace_node("node_2a_scenario_analysis")
        async def node_2a_func(state):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            logger = get_logger()
            start_time = time.time()

            # 시작 로그
            logger.info(
                f"Node started: {node_name}",
                node=node_name,
                node_type=node_type
            )

            try:
                result = await func(*args, **kwargs)

                # 성공 로그
                execution_time = time.time() - start_time
                logger.info(
                    f"Node completed: {node_name}",
                    node=node_name,
                    execution_time_seconds=round(execution_time, 2),
                    status="success"
                )

                return result

            except Exception as e:
                # 실패 로그
                execution_time = time.time() - start_time
                logger.error(
                    f"Node failed: {node_name}",
                    node=node_name,
                    execution_time_seconds=round(execution_time, 2),
                    status="failed",
                    error=e
                )
                raise

        return wrapper
    return decorator


# =============================================================================
# 7. LLM 호출 래퍼 (Rate Limit + Retry + Timeout)
# =============================================================================

async def call_llm_with_retry(
    llm_client,
    prompt: str,
    max_retries: int = 3,
    timeout_seconds: int = 120,
    estimated_tokens: int = 2000
) -> str:
    """
    LLM 호출 래퍼 (Rate Limit + Retry + Timeout 통합)

    Args:
        llm_client: LangChain LLM 클라이언트
        prompt: 프롬프트
        max_retries: 최대 재시도 횟수
        timeout_seconds: 타임아웃 (초)
        estimated_tokens: 예상 토큰 수

    Returns:
        str: LLM 응답 텍스트
    """
    logger = get_logger()
    rate_limiter = get_rate_limiter()

    for attempt in range(max_retries + 1):
        try:
            # Rate limit 확인
            await rate_limiter.acquire(estimated_tokens)

            # 타임아웃 설정하여 LLM 호출
            response = await asyncio.wait_for(
                llm_client.ainvoke(prompt),
                timeout=timeout_seconds
            )

            # 응답 텍스트 추출
            response_text = response.content if hasattr(response, 'content') else str(response)

            # 실제 토큰 수 기록 (응답에 포함된 경우)
            if hasattr(response, 'response_metadata'):
                token_usage = response.response_metadata.get('token_usage', {})
                total_tokens = token_usage.get('total_tokens', estimated_tokens)
                rate_limiter.record_tokens(total_tokens)

            return response_text

        except asyncio.TimeoutError:
            logger.warning(
                "LLM call timeout",
                attempt=attempt + 1,
                timeout_seconds=timeout_seconds
            )
            if attempt >= max_retries:
                raise TimeoutError(f"LLM call timed out after {max_retries + 1} attempts")

        except Exception as e:
            error_str = str(e).lower()

            # Rate limit 에러 처리
            if "rate_limit" in error_str or "429" in error_str:
                wait_time = 60  # 1분 대기
                logger.warning(
                    "Rate limit error, waiting",
                    wait_seconds=wait_time,
                    attempt=attempt + 1
                )
                await asyncio.sleep(wait_time)

            # 서버 에러 (재시도 가능)
            elif "500" in error_str or "503" in error_str:
                delay = min(2 ** attempt, 60)
                logger.warning(
                    "Server error, retrying",
                    delay_seconds=delay,
                    attempt=attempt + 1,
                    error=str(e)
                )
                await asyncio.sleep(delay)

            # 기타 에러
            else:
                if attempt >= max_retries:
                    logger.error("LLM call failed", error=e, attempts=attempt + 1)
                    raise

                delay = min(2 ** attempt, 30)
                await asyncio.sleep(delay)

    raise RuntimeError("LLM call failed after all retries")
