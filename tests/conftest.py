import io
from typing import AsyncGenerator
import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from pypdf import PdfWriter
from app.core.config import Settings
from app.main import create_application


@pytest.fixture
def test_settings() -> Settings:
    """Provides test settings."""
    return Settings(
        APP_NAME="Test Invoice Processor",
        DEBUG=True,
        AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="https://test.cognitiveservices.azure.com/",
        AZURE_DOCUMENT_INTELLIGENCE_KEY="test-key",
        MAX_FILE_SIZE_MB=10,
        MAX_PAGE_COUNT=20,
    )


@pytest.fixture
def app(test_settings: Settings) -> FastAPI:
    """Creates a FastAPI test application instance."""
    return create_application()


@pytest.fixture
async def async_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Provides an async HTTP test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def valid_pdf_bytes() -> bytes:
    """Generates a minimal valid 1-page PDF file in memory."""
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    stream = io.BytesIO()
    writer.write(stream)
    return stream.getvalue()


@pytest.fixture
def multi_page_pdf_bytes() -> bytes:
    """Generates a minimal valid 3-page PDF file in memory."""
    writer = PdfWriter()
    for _ in range(3):
        writer.add_blank_page(width=200, height=200)
    stream = io.BytesIO()
    writer.write(stream)
    return stream.getvalue()
