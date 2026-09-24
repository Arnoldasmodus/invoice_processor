from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from app.core.config import settings

api_key_header = APIKeyHeader(name=settings.API_KEY_HEADER_NAME, auto_error=False)


async def validate_api_key(api_key: str = Security(api_key_header)) -> str:
    """Validates the incoming API key header against configured API key."""
    if not settings.API_KEY:
        # If no API key configured, pass through (e.g. public dev mode)
        return ""

    if not api_key or api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
            headers={"WWW-Authenticate": settings.API_KEY_HEADER_NAME},
        )
    return api_key
