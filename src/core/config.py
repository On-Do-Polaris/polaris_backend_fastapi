from pydantic_settings import BaseSettings
from typing import Optional


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

    # Database (PostgreSQL)
    DATABASE_URL: Optional[str] = "postgresql+asyncpg://user:password@localhost:5432/polaris"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    # LLM Settings
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4"

    # Agent Settings
    AGENT_TIMEOUT: int = 300  # 5분

    # Mock Data (개발/테스트용)
    USE_MOCK_DATA: bool = True  # False로 설정하면 실제 ai_agent 사용

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # 정의되지 않은 환경변수 무시


settings = Settings()
