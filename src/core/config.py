from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # App
    APP_NAME: str = "SKAX Physical Risk AI Agent API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # API Key Authentication
    API_KEY: str = "your-secret-api-key"  # 환경변수로 설정

    # CORS Settings (프론트엔드 허용 도메인)
    CORS_ORIGINS: str = "*"  # 쉼표로 구분된 도메인 목록 또는 "*"
    # 예시: "http://localhost:3000,https://polaris.example.com"

    # Database (PostgreSQL Datawarehouse)
    # Default: Local development datawarehouse
    DATABASE_URL: Optional[str] = "postgresql://skala_dw_user:1234@localhost:5433/skala_datawarehouse"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    # LLM Settings
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4"

    # Agent Settings
    AGENT_TIMEOUT: int = 300  # 5분

    # Mock Data (개발/테스트용)
    USE_MOCK_DATA: bool = True  # False로 설정하면 실제 ai_agent 사용

    def get_cors_origins(self) -> List[str]:
        """CORS 허용 도메인 목록 반환"""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"  # 정의되지 않은 환경변수 무시
    }


settings = Settings()
