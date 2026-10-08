import os

import httpx
from pydantic import ValidationError

from app.core.config import settings
from app.models.response import InvoiceExtractionResponse


class InvoiceApiError(RuntimeError):
    """Raised when the invoice API cannot return a valid extraction response."""


def extract_invoice(file_name: str, file_bytes: bytes) -> InvoiceExtractionResponse:
    api_origin = os.getenv(
        "INVOICE_PROCESSOR_API_URL",
        f"http://127.0.0.1:{settings.PORT}",
    ).rstrip("/")
    api_prefix = settings.API_V1_PREFIX.rstrip("/")
    endpoint = f"{api_origin}{api_prefix}/documents/extract/invoice"

    try:
        response = httpx.post(
            endpoint,
            files={"file": (file_name, file_bytes, "application/pdf")},
            timeout=httpx.Timeout(180.0, connect=10.0),
        )
    except httpx.RequestError as exc:
        raise InvoiceApiError(
            "Nepavyko pasiekti dokumentų API. Patikrink, ar API serveris paleistas."
        ) from exc

    if response.is_error:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise InvoiceApiError(f"API klaida (HTTP {response.status_code}): {detail}")

    try:
        return InvoiceExtractionResponse.model_validate_json(response.content)
    except ValidationError as exc:
        raise InvoiceApiError("API grąžino neatpažįstamo formato atsakymą.") from exc