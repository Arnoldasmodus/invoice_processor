# Invoice Processor API

FastAPI service for invoice document processing, validation, and information extraction powered by Azure AI Document Intelligence.

## 🚀 Features

- **FastAPI Layered Architecture**: Modular structure dividing Presentation (API), Domain Models, Service Logic, and Core Utilities.
- **Azure Document Intelligence Integration**: Prebuilt models (`prebuilt-invoice`, `prebuilt-layout`, `prebuilt-read`) support.
- **Pydantic v2 Models**: Strict schemas with validation for request, response, and domain structures.
- **PDF Preprocessing**: PDF validation (size, page count, corruption check) and page splitting/batching.
- **Storage Layer**: Local filesystem and asynchronous Azure Blob Storage providers.
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
uvicorn app.main:app --reload --reload-dir app
```

### 3. Run with Docker Compose

PowerShell:

```powershell
Copy-Item .env.example .env
```

Set the Azure Document Intelligence endpoint and key in `.env`, then start both Docker
services:

```powershell
docker compose up --build -d
```

Open the Streamlit UI at `http://localhost:8501`; the API docs are at
`http://localhost:8000/docs`. Both ports are published only on this computer
(`127.0.0.1`). If either port is already in use, change `HOST_PORT` or `UI_HOST_PORT` in
`.env` and use the matching UI/API URL. To view logs and stop the services:

```powershell
docker compose logs -f
docker compose down
```

Uploaded data is kept in a Docker-managed volume when the container is recreated. The
`.env` file is excluded from Git and the Docker build context; do not put real keys in
`.env.example`. Because the API has no authentication, do not expose it beyond localhost
without adding an appropriate access-control layer.

The UI sends PDFs to the API over the private Compose network. The API does not require
authentication; both services are bound to localhost and should not be exposed beyond
this computer without adding an appropriate access-control layer.

### Azure Blob Storage

To use an existing Azure container, set the following values in `.env`:

```dotenv
STORAGE_TYPE=azure_blob
AZURE_STORAGE_ACCOUNT_NAME=your-storage-account
AZURE_STORAGE_ACCOUNT_KEY=your-storage-account-key
AZURE_STORAGE_CONTAINER_NAME=your-existing-container
```

Restart the application after changing configuration. The storage account key must allow
blob read, write, and delete operations. The service does not create the container.
Uploads use unique blob names; `STORAGE_TYPE=local` keeps filesystem storage enabled.
Document uploads are persisted when `save_to_storage=true` on the analyze or scan endpoint.
The dedicated invoice extraction endpoint does not save uploaded files.

Docker Compose loads `.env` into the container, so setting `STORAGE_TYPE=azure_blob` and
the Blob settings above is sufficient to enable Blob storage.
`AZURE_DOCUMENT_INTELLIGENCE_MODEL_ID` in `.env` is not currently used by the application.

---

## 🧪 Testing

```bash
pytest
```
