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

    # Database (필요시)
    DATABASE_URL: Optional[str] = None

    # Redis (작업 큐용, 필요시)
    REDIS_URL: Optional[str] = None

    # LLM Settings
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4"

    # Agent Settings
    AGENT_TIMEOUT: int = 300  # 5분

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
