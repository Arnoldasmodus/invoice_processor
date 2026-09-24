# Invoice Processor API

FastAPI service for invoice document processing, validation, and information extraction powered by Azure AI Document Intelligence.

## 🚀 Features

- **FastAPI Layered Architecture**: Modular structure dividing Presentation (API), Domain Models, Service Logic, and Core Utilities.
- **Azure Document Intelligence Integration**: Prebuilt models (`prebuilt-invoice`, `prebuilt-layout`, `prebuilt-read`) support.
- **Pydantic v2 Models**: Strict schemas with validation for request, response, and domain structures.
- **PDF Preprocessing**: PDF validation (size, page count, corruption check) and page splitting/batching.
- **Storage Layer**: Local storage interface with abstract base provider for cloud blob extensions.
- **Health Checks & Probes**: Readiness and liveness endpoints.
- **Container Ready**: Docker and Docker Compose setup.

---

## 🛠️ Project Structure

```
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
├── README.md
├── app/
│   ├── __init__.py
│   ├── main.py                          # App factory, lifespan management, middleware
│   │
│   ├── api/                             # API Presentation Layer
│   │   ├── __init__.py
│   │   ├── dependencies.py              # DI providers (Settings, Azure client, Services)
│   │   ├── router.py                    # Master router aggregating sub-routers
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── health.py                # Health checks & readiness probes
│   │       └── documents.py             # PDF upload, analyze, and extraction endpoints
│   │
│   ├── core/                            # Configuration & Global setup
│   │   ├── __init__.py
│   │   ├── config.py                    # Pydantic v2 Settings (BaseSettings)
│   │   ├── constants.py                 # Supported models, mime types, enums
│   │   ├── exceptions.py                # Custom exceptions and global handlers
│   │   ├── logging.py                   # Structured logging configuration
│   │   └── security.py                  # API key validation / JWT security
│   │
│   ├── models/                          # Pydantic Schemas (v2)
│   │   ├── __init__.py
│   │   ├── common.py                    # BoundingBox, KeyValuePair, ConfidenceScore
│   │   ├── request.py                   # Analysis options (model_id, pages, features)
│   │   ├── response.py                  # Standardized extraction output schemas
│   │   └── domain.py                    # Internal domain entities / table representations
│   │
│   ├── services/                        # Business Logic & Integrations
│   │   ├── __init__.py
│   │   ├── base.py                      # Base service abstract class
│   │   ├── document_intelligence/       # Azure Document Intelligence sub-package
│   │   │   ├── __init__.py
│   │   │   ├── client.py                # Async Azure DocumentIntelligenceClient lifecycle
│   │   │   ├── analyzer.py              # Analysis execution (prebuilt-layout, read, etc.)
│   │   │   ├── parser.py                # Maps Azure SDK response objects to Pydantic models
│   │   │   └── models.py                # Supported prebuilt model enum & features
│   │   ├── pdf/                         # PDF preprocessing & validation
│   │   │   ├── __init__.py
│   │   │   ├── validator.py             # PDF size, page limits, password/corruption checks
│   │   │   └── splitter.py              # Page extraction/batching for large PDFs
│   │   └── storage/                     # Blob / local storage for results/files
│   │       ├── __init__.py
│   │       ├── base.py
│   │       └── local_storage.py
│   │
│   └── utils/                           # Common helper utilities
│       ├── __init__.py
│       ├── file_utils.py                # Temp file managers, stream handling
│       └── formatting.py                # Markdown/JSON formatting utilities
│
└── tests/                               # Test Suite
    ├── __init__.py
    ├── conftest.py                      # Pytest fixtures & DI overrides
    ├── unit/
    │   ├── test_pdf_validator.py
    │   ├── test_response_parser.py
    │   └── test_config.py
    ├── integration/
    │   ├── test_api_documents.py
    │   └── test_azure_service.py
    └── sample_data/
        └── sample.pdf
```

---

## ⚡ Quick Start

### 1. Environment Setup

```bash
cp .env.example .env
# Fill in your Azure Document Intelligence Endpoint and Key in .env
```

### 2. Run with Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 3. Run with Docker Compose

```bash
docker-compose up --build
```

API docs will be available at `http://localhost:8000/docs`.

---

## 🧪 Testing

```bash
pytest
```
