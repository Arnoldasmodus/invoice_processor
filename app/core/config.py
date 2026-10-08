from functools import lru_cache
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application settings
    APP_NAME: str = "Invoice Processor API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1

    # Azure Document Intelligence
    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT: str = ""
    AZURE_DOCUMENT_INTELLIGENCE_KEY: str = ""
    AZURE_DOCUMENT_INTELLIGENCE_API_VERSION: str = "2024-11-30"

    # PDF Processing constraints
    MAX_FILE_SIZE_MB: int = 20
    MAX_PAGE_COUNT: int = 50
    ALLOWED_MIME_TYPES: List[str] = Field(default_factory=lambda: ["application/pdf"])

    # Storage settings
    STORAGE_TYPE: str = "local"
    LOCAL_STORAGE_DIR: str = "./storage_data"
    AZURE_STORAGE_ACCOUNT_NAME: str = ""
    AZURE_STORAGE_ACCOUNT_KEY: str = ""
    AZURE_STORAGE_CONTAINER_NAME: str = ""

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
