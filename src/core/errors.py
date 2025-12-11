"""
파일명: errors.py
최종 수정일: 2025-12-01
버전: v01
파일 개요: 에러 코드 및 구조화된 에러 정보 정의
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class ErrorCode(str, Enum):
    """표준화된 에러 코드"""

    # Analysis 관련 (1xxx)
    ANALYSIS_FAILED = "ANALYSIS_1001"
    ANALYSIS_TIMEOUT = "ANALYSIS_1002"
    ANALYSIS_INVALID_INPUT = "ANALYSIS_1003"
    ANALYSIS_DATA_COLLECTION_FAILED = "ANALYSIS_1004"

    # Enhancement 관련 (2xxx)
    ENHANCEMENT_FAILED = "ENHANCEMENT_2001"
    ENHANCEMENT_CACHE_NOT_FOUND = "ENHANCEMENT_2002"
    ENHANCEMENT_GUIDELINE_FAILED = "ENHANCEMENT_2003"
    ENHANCEMENT_WORKFLOW_FAILED = "ENHANCEMENT_2004"

    # Workflow 관련 (3xxx)
    WORKFLOW_NODE_FAILED = "WORKFLOW_3001"
    WORKFLOW_VALIDATION_FAILED = "WORKFLOW_3002"
    WORKFLOW_RETRY_EXHAUSTED = "WORKFLOW_3003"
    WORKFLOW_STATE_CORRUPTED = "WORKFLOW_3004"

    # LLM 관련 (4xxx)
    LLM_API_ERROR = "LLM_4001"
    LLM_TIMEOUT = "LLM_4002"
    LLM_INVALID_RESPONSE = "LLM_4003"
    LLM_RATE_LIMIT = "LLM_4004"
    LLM_JSON_PARSE_ERROR = "LLM_4005"

    # Cache 관련 (5xxx)
    CACHE_MISS = "CACHE_5001"
    CACHE_WRITE_FAILED = "CACHE_5002"
    CACHE_READ_FAILED = "CACHE_5003"

    # ModelOps 관련 (6xxx)
    MODELOPS_API_ERROR = "MODELOPS_6001"
    MODELOPS_TIMEOUT = "MODELOPS_6002"
    MODELOPS_INVALID_DATA = "MODELOPS_6003"


class ErrorSeverity(str, Enum):
    """에러 심각도"""
    LOW = "low"  # 경고 수준
    MEDIUM = "medium"  # 재시도 가능
    HIGH = "high"  # 즉시 조치 필요
    CRITICAL = "critical"  # 시스템 중단


class ErrorDetail(BaseModel):
    """구조화된 에러 정보"""
    code: ErrorCode
    message: str  # 사용자 친화적 메시지
    detail: Optional[str] = None  # 개발자용 상세 메시지
    request_id: Optional[str] = None
    timestamp: Optional[str] = None
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    context: Optional[dict] = None  # 추가 컨텍스트 정보

    class Config:
        use_enum_values = True

    def __init__(self, **data):
        if 'timestamp' not in data or data['timestamp'] is None:
            data['timestamp'] = datetime.now().isoformat()
        super().__init__(**data)


# 에러 코드별 기본 메시지 매핑
ERROR_MESSAGES = {
    ErrorCode.ANALYSIS_FAILED: "분석 작업이 실패했습니다.",
    ErrorCode.ANALYSIS_TIMEOUT: "분석 작업 시간이 초과되었습니다.",
    ErrorCode.ANALYSIS_INVALID_INPUT: "입력 데이터가 유효하지 않습니다.",
    ErrorCode.ANALYSIS_DATA_COLLECTION_FAILED: "기후 데이터 수집에 실패했습니다.",

    ErrorCode.ENHANCEMENT_FAILED: "분석 향상 작업이 실패했습니다.",
    ErrorCode.ENHANCEMENT_CACHE_NOT_FOUND: "분석 결과를 찾을 수 없습니다. 기본 분석을 먼저 실행해주세요.",
    ErrorCode.ENHANCEMENT_GUIDELINE_FAILED: "추가 데이터 가이드라인 생성에 실패했습니다.",
    ErrorCode.ENHANCEMENT_WORKFLOW_FAILED: "향상 워크플로우 실행에 실패했습니다.",

    ErrorCode.WORKFLOW_NODE_FAILED: "워크플로우 노드 실행에 실패했습니다.",
    ErrorCode.WORKFLOW_VALIDATION_FAILED: "검증에 실패했습니다.",
    ErrorCode.WORKFLOW_RETRY_EXHAUSTED: "최대 재시도 횟수를 초과했습니다.",
    ErrorCode.WORKFLOW_STATE_CORRUPTED: "워크플로우 상태가 손상되었습니다.",

    ErrorCode.LLM_API_ERROR: "LLM API 호출에 실패했습니다.",
    ErrorCode.LLM_TIMEOUT: "LLM 응답 시간이 초과되었습니다.",
    ErrorCode.LLM_INVALID_RESPONSE: "LLM 응답이 유효하지 않습니다.",
    ErrorCode.LLM_RATE_LIMIT: "LLM API 호출 한도를 초과했습니다.",
    ErrorCode.LLM_JSON_PARSE_ERROR: "LLM 응답의 JSON 파싱에 실패했습니다.",

    ErrorCode.CACHE_MISS: "캐시에서 데이터를 찾을 수 없습니다.",
    ErrorCode.CACHE_WRITE_FAILED: "캐시 쓰기에 실패했습니다.",
    ErrorCode.CACHE_READ_FAILED: "캐시 읽기에 실패했습니다.",

    ErrorCode.MODELOPS_API_ERROR: "ModelOps API 호출에 실패했습니다.",
    ErrorCode.MODELOPS_TIMEOUT: "ModelOps 응답 시간이 초과되었습니다.",
    ErrorCode.MODELOPS_INVALID_DATA: "ModelOps 데이터가 유효하지 않습니다.",
}


def create_error_detail(
    code: ErrorCode,
    detail: Optional[str] = None,
    request_id: Optional[str] = None,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    context: Optional[dict] = None
) -> ErrorDetail:
    """
    ErrorDetail 생성 헬퍼 함수

    Args:
        code: 에러 코드
        detail: 개발자용 상세 메시지 (없으면 사용자 메시지와 동일)
        request_id: 요청 ID
        severity: 심각도
        context: 추가 컨텍스트

    Returns:
        ErrorDetail 인스턴스
    """
    message = ERROR_MESSAGES.get(code, "알 수 없는 오류가 발생했습니다.")

    return ErrorDetail(
        code=code,
        message=message,
        detail=detail or message,
        request_id=request_id,
        severity=severity,
        context=context
    )
