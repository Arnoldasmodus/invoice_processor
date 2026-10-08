from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from azure.core.exceptions import AzureError, ResourceNotFoundError
from app.api.dependencies import get_storage_service
from app.core.config import Settings
from app.core.exceptions import StorageException
from app.services.storage.azure_blob_storage import AzureBlobStorageService
from app.services.storage.local_storage import LocalStorageService


@pytest.fixture
def blob_settings():
    return Settings(
        _env_file=None,
        STORAGE_TYPE="azure_blob",
        AZURE_STORAGE_ACCOUNT_NAME="testaccount",
        AZURE_STORAGE_ACCOUNT_KEY="test-key",
        AZURE_STORAGE_CONTAINER_NAME="invoices",
    )


@pytest.fixture
def blob_client():
    with patch(
        "app.services.storage.azure_blob_storage.BlobServiceClient"
    ) as factory:
        client = factory.return_value
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=False)
        blob = MagicMock()
        blob.upload_blob = AsyncMock()
        blob.download_blob = AsyncMock()
        blob.delete_blob = AsyncMock()
        blob.exists = AsyncMock(return_value=True)
        client.get_blob_client.return_value = blob
        yield factory, client, blob


@pytest.mark.asyncio
async def test_save_file(blob_settings, blob_client):
    factory, client, blob = blob_client
    service = AzureBlobStorageService(blob_settings)

    storage_key = await service.save_file("invoice.pdf", b"pdf-data")
    second_key = await service.save_file("invoice.pdf", b"pdf-data")

    assert storage_key.endswith("_invoice.pdf")
    assert storage_key != second_key
    factory.assert_called_with(
        account_url="https://testaccount.blob.core.windows.net", credential="test-key"
    )
    client.get_blob_client.assert_any_call("invoices", storage_key)
    blob.upload_blob.assert_awaited_with(b"pdf-data", overwrite=False)
    assert client.__aexit__.await_count == 2


@pytest.mark.asyncio
async def test_read_file(blob_settings, blob_client):
    _, client, blob = blob_client
    download = MagicMock()
    download.readall = AsyncMock(return_value=b"pdf-data")
    blob.download_blob.return_value = download

    assert await AzureBlobStorageService(blob_settings).read_file("invoice.pdf") == b"pdf-data"
    client.get_blob_client.assert_called_once_with("invoices", "invoice.pdf")
    client.__aexit__.assert_awaited_once()


@pytest.mark.asyncio
async def test_read_missing_file(blob_settings, blob_client):
    _, _, blob = blob_client
    blob.download_blob.side_effect = ResourceNotFoundError("missing")

    with pytest.raises(StorageException, match="not found"):
        await AzureBlobStorageService(blob_settings).read_file("missing.pdf")


@pytest.mark.asyncio
async def test_delete_file(blob_settings, blob_client):
    _, _, blob = blob_client
    service = AzureBlobStorageService(blob_settings)

    assert await service.delete_file("invoice.pdf") is True
    blob.delete_blob.assert_awaited_once_with(delete_snapshots="include")
    blob.delete_blob.side_effect = ResourceNotFoundError("missing")
    assert await service.delete_file("missing.pdf") is False


@pytest.mark.asyncio
@pytest.mark.parametrize("exists", [True, False])
async def test_file_exists(blob_settings, blob_client, exists):
    _, _, blob = blob_client
    blob.exists.return_value = exists

    assert await AzureBlobStorageService(blob_settings).file_exists("invoice.pdf") is exists


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method, sdk_method, arguments",
    [
        ("save_file", "upload_blob", ("invoice.pdf", b"data")),
        ("read_file", "download_blob", ("invoice.pdf",)),
        ("delete_file", "delete_blob", ("invoice.pdf",)),
        ("file_exists", "exists", ("invoice.pdf",)),
    ],
)
async def test_azure_error_wrapped(blob_settings, blob_client, method, sdk_method, arguments):
    _, client, blob = blob_client
    getattr(blob, sdk_method).side_effect = AzureError("sensitive error details")

    with pytest.raises(StorageException) as error:
        await getattr(AzureBlobStorageService(blob_settings), method)(*arguments)

    assert "sensitive error details" not in str(error.value)
    client.__aexit__.assert_awaited_once()


@pytest.mark.parametrize(
    "setting",
    ["AZURE_STORAGE_ACCOUNT_NAME", "AZURE_STORAGE_ACCOUNT_KEY", "AZURE_STORAGE_CONTAINER_NAME"],
)
def test_missing_settings(blob_settings, setting):
    setattr(blob_settings, setting, "")
    with pytest.raises(StorageException, match=setting):
        AzureBlobStorageService(blob_settings)


def test_blob_storage_selection(blob_settings):
    assert isinstance(get_storage_service(blob_settings), AzureBlobStorageService)


def test_local_storage_selection(blob_settings, tmp_path):
    blob_settings.STORAGE_TYPE = "local"
    blob_settings.LOCAL_STORAGE_DIR = str(tmp_path)
    assert isinstance(get_storage_service(blob_settings), LocalStorageService)


def test_unsupported_storage_selection(blob_settings):
    blob_settings.STORAGE_TYPE = "unknown"
    with pytest.raises(StorageException, match="Unsupported STORAGE_TYPE"):
        get_storage_service(blob_settings)