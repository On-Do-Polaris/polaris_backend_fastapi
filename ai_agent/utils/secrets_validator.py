"""
Secrets Validator
시작 시 필수 환경변수/시크릿 검증 및 에러 메시지 제공

작성일: 2025-12-17
버전: v1.0

사용법:
    from ai_agent.utils.secrets_validator import validate_secrets, SecretConfig

    # 앱 시작 시 검증
    validation_result = validate_secrets()
    if not validation_result.is_valid:
        for error in validation_result.errors:
            print(f"ERROR: {error}")
        sys.exit(1)
"""

import os
from typing import List, Optional, NamedTuple
from enum import Enum
from dataclasses import dataclass


class SecretImportance(Enum):
    """시크릿 중요도"""
    REQUIRED = "required"      # 필수 - 없으면 앱 시작 불가
    RECOMMENDED = "recommended"  # 권장 - 없으면 경고
    OPTIONAL = "optional"      # 선택 - 없어도 무관


@dataclass
class SecretDefinition:
    """시크릿 정의"""
    name: str                           # 환경변수 이름
    importance: SecretImportance        # 중요도
    description: str                    # 설명
    example: str = ""                   # 예시 값
    default: Optional[str] = None       # 기본값 (OPTIONAL인 경우)


# 필수 환경변수 목록 정의
SECRET_DEFINITIONS: List[SecretDefinition] = [
    # === 필수 (REQUIRED) ===
    SecretDefinition(
        name="OPENAI_API_KEY",
        importance=SecretImportance.REQUIRED,
        description="OpenAI API 키 (LLM 호출용)",
        example="sk-..."
    ),
    SecretDefinition(
        name="APPLICATION_DATABASE_URL",
        importance=SecretImportance.REQUIRED,
        description="Application DB 연결 URL (PostgreSQL)",
        example="postgresql://user:password@host:5432/dbname"
    ),
    SecretDefinition(
        name="DATABASE_URL",
        importance=SecretImportance.REQUIRED,
        description="Data Warehouse DB 연결 URL (PostgreSQL)",
        example="postgresql://user:password@host:5432/dbname"
    ),

    # === 권장 (RECOMMENDED) ===
    SecretDefinition(
        name="QDRANT_URL",
        importance=SecretImportance.RECOMMENDED,
        description="Qdrant 벡터DB URL (RAG 검색용)",
        example="http://localhost:6333",
        default="http://localhost:6333"
    ),
    SecretDefinition(
        name="LANGSMITH_API_KEY",
        importance=SecretImportance.RECOMMENDED,
        description="LangSmith API 키 (LLM 트레이싱용)",
        example="ls__..."
    ),

    # === 선택 (OPTIONAL) ===
    SecretDefinition(
        name="LANGSMITH_ENABLED",
        importance=SecretImportance.OPTIONAL,
        description="LangSmith 활성화 여부",
        default="false"
    ),
    SecretDefinition(
        name="LANGSMITH_PROJECT",
        importance=SecretImportance.OPTIONAL,
        description="LangSmith 프로젝트 이름",
        default="tcfd-report"
    ),
    SecretDefinition(
        name="ENVIRONMENT",
        importance=SecretImportance.OPTIONAL,
        description="실행 환경 (development/production/test)",
        default="development"
    ),
    SecretDefinition(
        name="OPENAI_RPM",
        importance=SecretImportance.OPTIONAL,
        description="OpenAI 분당 요청 제한",
        default="60"
    ),
    SecretDefinition(
        name="OPENAI_TPM",
        importance=SecretImportance.OPTIONAL,
        description="OpenAI 분당 토큰 제한",
        default="150000"
    ),
    SecretDefinition(
        name="RAG_MOCK_MODE",
        importance=SecretImportance.OPTIONAL,
        description="RAG Mock 모드 (테스트용)",
        default="false"
    ),
]


class ValidationResult(NamedTuple):
    """검증 결과"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    info: List[str]


def validate_secrets(
    definitions: List[SecretDefinition] = None,
    fail_on_warning: bool = False
) -> ValidationResult:
    """
    환경변수/시크릿 검증

    Args:
        definitions: 검증할 시크릿 정의 목록 (None이면 기본 목록 사용)
        fail_on_warning: True이면 RECOMMENDED 누락 시도 에러로 처리

    Returns:
        ValidationResult: 검증 결과
    """
    if definitions is None:
        definitions = SECRET_DEFINITIONS

    errors: List[str] = []
    warnings: List[str] = []
    info: List[str] = []

    for secret in definitions:
        value = os.getenv(secret.name)

        if value is None or value == "":
            if secret.importance == SecretImportance.REQUIRED:
                errors.append(
                    f"[REQUIRED] {secret.name} is not set.\n"
                    f"  Description: {secret.description}\n"
                    f"  Example: {secret.example}"
                )
            elif secret.importance == SecretImportance.RECOMMENDED:
                msg = (
                    f"[RECOMMENDED] {secret.name} is not set.\n"
                    f"  Description: {secret.description}"
                )
                if secret.default:
                    msg += f"\n  Using default: {secret.default}"
                    # 기본값 설정
                    os.environ[secret.name] = secret.default

                if fail_on_warning:
                    errors.append(msg)
                else:
                    warnings.append(msg)
            else:  # OPTIONAL
                if secret.default:
                    # 기본값 설정
                    os.environ[secret.name] = secret.default
                    info.append(f"[OPTIONAL] {secret.name} using default: {secret.default}")
        else:
            # 값이 설정됨 - 마스킹하여 로그
            masked_value = _mask_secret(value)
            info.append(f"[OK] {secret.name} = {masked_value}")

    is_valid = len(errors) == 0

    return ValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        info=info
    )


def _mask_secret(value: str, visible_chars: int = 4) -> str:
    """시크릿 값 마스킹"""
    if len(value) <= visible_chars * 2:
        return "*" * len(value)
    return value[:visible_chars] + "*" * (len(value) - visible_chars * 2) + value[-visible_chars:]


def print_validation_result(result: ValidationResult, verbose: bool = False):
    """검증 결과 출력"""
    print("\n" + "=" * 60)
    print("🔐 Environment Variables Validation")
    print("=" * 60)

    if result.errors:
        print("\n❌ ERRORS (App cannot start):")
        for error in result.errors:
            print(f"\n  {error}")

    if result.warnings:
        print("\n⚠️  WARNINGS (Recommended to fix):")
        for warning in result.warnings:
            print(f"\n  {warning}")

    if verbose and result.info:
        print("\nℹ️  INFO:")
        for info in result.info:
            print(f"  {info}")

    print("\n" + "=" * 60)
    if result.is_valid:
        print("✅ Validation PASSED - All required secrets are set")
    else:
        print("❌ Validation FAILED - Please set the required secrets")
    print("=" * 60 + "\n")


def validate_and_exit_on_failure(verbose: bool = False):
    """
    시크릿 검증 후 실패 시 종료

    앱 시작 시 호출하여 필수 시크릿이 없으면 명확한 에러 메시지와 함께 종료

    Usage:
        from ai_agent.utils.secrets_validator import validate_and_exit_on_failure

        # main.py 시작 부분에서
        validate_and_exit_on_failure()
    """
    result = validate_secrets()
    print_validation_result(result, verbose=verbose)

    if not result.is_valid:
        print("\n💡 Tip: Set environment variables or use a .env file")
        print("   Copy .env.example to .env and fill in the values\n")
        import sys
        sys.exit(1)

    return result


# 환경변수 존재 확인 헬퍼 함수들
def get_required_env(name: str, description: str = "") -> str:
    """
    필수 환경변수 가져오기 (없으면 예외 발생)

    Usage:
        api_key = get_required_env("OPENAI_API_KEY", "OpenAI API Key")
    """
    value = os.getenv(name)
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{name}' is not set.\n"
            f"Description: {description}"
        )
    return value


def get_optional_env(name: str, default: str = "", description: str = "") -> str:
    """
    선택 환경변수 가져오기 (없으면 기본값 반환)

    Usage:
        env = get_optional_env("ENVIRONMENT", "development")
    """
    return os.getenv(name, default)
