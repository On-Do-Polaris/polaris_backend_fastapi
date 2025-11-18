from fastapi import Header, HTTPException, status

from .config import settings


async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    """API Key 검증"""
    if x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return x_api_key
