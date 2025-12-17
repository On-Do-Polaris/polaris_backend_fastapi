"""
Error Handlers
TCFD Report Agent 에러 처리 유틸리티

작성일: 2025-12-17
버전: v1.0

주요 기능:
1. 공통 에러 타입 정의
2. LLM 에러 처리 (Rate Limit, Timeout 등)
3. DB 에러 처리
4. 노드 실행 에러 래퍼
"""

import asyncio
import functools
import traceback
from typing import Any, Callable, Dict, Optional, TypeVar, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

T = TypeVar('T')


# =============================================================================
# 에러 타입 정의
# =============================================================================

class ErrorCategory(Enum):
    """에러 카테고리"""
    LLM_ERROR = "llm_error"           # LLM 호출 에러
    DB_ERROR = "db_error"             # DB 연결/쿼리 에러
    RAG_ERROR = "rag_error"           # RAG 검색 에러
    VALIDATION_ERROR = "validation"   # 검증 에러
    TIMEOUT_ERROR = "timeout"         # 타임아웃
    RATE_LIMIT_ERROR = "rate_limit"   # Rate Limit
    CONFIG_ERROR = "config"           # 설정 에러
    UNKNOWN_ERROR = "unknown"         # 알 수 없는 에러


class ErrorSeverity(Enum):
    """에러 심각도"""
    LOW = "low"           # 낮음 - 재시도로 해결 가능
    MEDIUM = "medium"     # 중간 - 대체 로직으로 처리
    HIGH = "high"         # 높음 - 노드 재실행 필요
    CRITICAL = "critical" # 치명적 - 워크플로우 중단


@dataclass
class TCFDError:
    """TCFD 에러 정보"""
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    node_name: Optional[str] = None
    original_error: Optional[Exception] = None
    timestamp: str = ""
    retry_recommended: bool = False
    fallback_available: bool = False
    context: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat() + "Z"

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "node_name": self.node_name,
            "timestamp": self.timestamp,
            "retry_recommended": self.retry_recommended,
            "fallback_available": self.fallback_available,
            "context": self.context
        }


# =============================================================================
# 에러 분류 함수
# =============================================================================

def classify_error(error: Exception, node_name: str = None) -> TCFDError:
    """
    에러를 분류하고 TCFDError 객체 반환

    Args:
        error: 원본 예외
        node_name: 에러 발생 노드 이름

    Returns:
        TCFDError: 분류된 에러 정보
    """
    error_str = str(error).lower()
    error_type = type(error).__name__

    # Rate Limit 에러
    if "rate_limit" in error_str or "429" in error_str or "too many requests" in error_str:
        return TCFDError(
            category=ErrorCategory.RATE_LIMIT_ERROR,
            severity=ErrorSeverity.LOW,
            message=f"Rate limit exceeded: {error}",
            node_name=node_name,
            original_error=error,
            retry_recommended=True,
            fallback_available=False,
            context={"wait_time_recommended": 60}
        )

    # Timeout 에러
    if isinstance(error, asyncio.TimeoutError) or "timeout" in error_str:
        return TCFDError(
            category=ErrorCategory.TIMEOUT_ERROR,
            severity=ErrorSeverity.MEDIUM,
            message=f"Request timed out: {error}",
            node_name=node_name,
            original_error=error,
            retry_recommended=True,
            fallback_available=True
        )

    # LLM 서버 에러
    if "500" in error_str or "503" in error_str or "502" in error_str:
        return TCFDError(
            category=ErrorCategory.LLM_ERROR,
            severity=ErrorSeverity.MEDIUM,
            message=f"LLM server error: {error}",
            node_name=node_name,
            original_error=error,
            retry_recommended=True,
            fallback_available=True
        )

    # API 키 에러
    if "api_key" in error_str or "authentication" in error_str or "401" in error_str:
        return TCFDError(
            category=ErrorCategory.CONFIG_ERROR,
            severity=ErrorSeverity.CRITICAL,
            message=f"API authentication failed: {error}",
            node_name=node_name,
            original_error=error,
            retry_recommended=False,
            fallback_available=False
        )

    # DB 연결 에러
    if "connection" in error_str and ("database" in error_str or "postgresql" in error_str or "db" in error_str):
        return TCFDError(
            category=ErrorCategory.DB_ERROR,
            severity=ErrorSeverity.HIGH,
            message=f"Database connection error: {error}",
            node_name=node_name,
            original_error=error,
            retry_recommended=True,
            fallback_available=False
        )

    # Qdrant/RAG 에러
    if "qdrant" in error_str or "vector" in error_str:
        return TCFDError(
            category=ErrorCategory.RAG_ERROR,
            severity=ErrorSeverity.MEDIUM,
            message=f"RAG/Vector DB error: {error}",
            node_name=node_name,
            original_error=error,
            retry_recommended=True,
            fallback_available=True  # Mock 모드로 대체 가능
        )

    # JSON 파싱 에러
    if "json" in error_str or error_type == "JSONDecodeError":
        return TCFDError(
            category=ErrorCategory.VALIDATION_ERROR,
            severity=ErrorSeverity.MEDIUM,
            message=f"JSON parsing error: {error}",
            node_name=node_name,
            original_error=error,
            retry_recommended=True,
            fallback_available=True
        )

    # 알 수 없는 에러
    return TCFDError(
        category=ErrorCategory.UNKNOWN_ERROR,
        severity=ErrorSeverity.HIGH,
        message=f"Unexpected error: {error_type}: {error}",
        node_name=node_name,
        original_error=error,
        retry_recommended=False,
        fallback_available=False,
        context={"traceback": traceback.format_exc()}
    )


# =============================================================================
# 노드 에러 핸들러 데코레이터
# =============================================================================

def handle_node_errors(
    node_name: str,
    fallback_func: Callable[..., T] = None,
    max_retries: int = 2,
    propagate_critical: bool = True
):
    """
    노드 실행 에러 핸들러 데코레이터

    Usage:
        @handle_node_errors("node_2a_scenario_analysis", fallback_func=get_fallback_scenarios)
        async def node_2a_func(state):
            ...

    Args:
        node_name: 노드 이름 (로깅용)
        fallback_func: 에러 시 호출할 fallback 함수
        max_retries: 최대 자동 재시도 횟수
        propagate_critical: CRITICAL 에러 시 예외 전파 여부
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_error: Optional[TCFDError] = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)

                except Exception as e:
                    # 에러 분류
                    tcfd_error = classify_error(e, node_name)
                    last_error = tcfd_error

                    # 로깅
                    print(f"\n⚠️ [{node_name}] Error (attempt {attempt + 1}/{max_retries + 1}):")
                    print(f"   Category: {tcfd_error.category.value}")
                    print(f"   Severity: {tcfd_error.severity.value}")
                    print(f"   Message: {tcfd_error.message}")

                    # CRITICAL 에러는 즉시 전파
                    if tcfd_error.severity == ErrorSeverity.CRITICAL and propagate_critical:
                        print(f"   ❌ Critical error - propagating immediately")
                        raise

                    # 재시도 가능하고 아직 시도 횟수가 남았으면 재시도
                    if tcfd_error.retry_recommended and attempt < max_retries:
                        wait_time = tcfd_error.context.get("wait_time_recommended", 2 ** attempt) if tcfd_error.context else 2 ** attempt
                        print(f"   🔄 Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue

                    # Fallback 사용 가능하면 실행
                    if tcfd_error.fallback_available and fallback_func:
                        print(f"   📋 Using fallback function...")
                        try:
                            if asyncio.iscoroutinefunction(fallback_func):
                                return await fallback_func(*args, **kwargs)
                            return fallback_func(*args, **kwargs)
                        except Exception as fallback_error:
                            print(f"   ❌ Fallback also failed: {fallback_error}")

                    # 모든 시도 실패
                    break

            # 최종 실패 - 에러 정보와 함께 예외 발생
            error_msg = f"Node {node_name} failed after {max_retries + 1} attempts"
            if last_error:
                error_msg += f": {last_error.message}"
            raise RuntimeError(error_msg)

        return wrapper
    return decorator


# =============================================================================
# 에러 수집기 (워크플로우 레벨)
# =============================================================================

class ErrorCollector:
    """
    워크플로우 실행 중 발생한 에러 수집

    Usage:
        collector = ErrorCollector()
        collector.add_error(tcfd_error)
        summary = collector.get_summary()
    """

    def __init__(self):
        self.errors: list[TCFDError] = []
        self.warnings: list[str] = []

    def add_error(self, error: TCFDError):
        """에러 추가"""
        self.errors.append(error)

    def add_warning(self, message: str):
        """경고 추가"""
        self.warnings.append(message)

    def has_critical_errors(self) -> bool:
        """치명적 에러 존재 여부"""
        return any(e.severity == ErrorSeverity.CRITICAL for e in self.errors)

    def get_error_count(self) -> Dict[ErrorCategory, int]:
        """카테고리별 에러 수"""
        counts = {}
        for error in self.errors:
            counts[error.category] = counts.get(error.category, 0) + 1
        return counts

    def get_summary(self) -> Dict[str, Any]:
        """에러 요약"""
        return {
            "total_errors": len(self.errors),
            "total_warnings": len(self.warnings),
            "has_critical": self.has_critical_errors(),
            "errors_by_category": {k.value: v for k, v in self.get_error_count().items()},
            "errors": [e.to_dict() for e in self.errors],
            "warnings": self.warnings
        }

    def clear(self):
        """에러 초기화"""
        self.errors.clear()
        self.warnings.clear()


# 전역 에러 수집기
_error_collector: Optional[ErrorCollector] = None


def get_error_collector() -> ErrorCollector:
    """전역 에러 수집기 반환"""
    global _error_collector
    if _error_collector is None:
        _error_collector = ErrorCollector()
    return _error_collector


def reset_error_collector():
    """에러 수집기 초기화"""
    global _error_collector
    _error_collector = ErrorCollector()
