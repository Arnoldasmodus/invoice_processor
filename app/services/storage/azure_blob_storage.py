import uuid
from azure.core.exceptions import AzureError, ResourceNotFoundError
from azure.storage.blob.aio import BlobServiceClient
from app.core.config import Settings
from app.core.exceptions import StorageException
from app.services.storage.base import BaseStorageService


class AzureBlobStorageService(BaseStorageService):
    """Stores documents in an existing Azure Blob Storage container."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
        required_settings = (
            "AZURE_STORAGE_ACCOUNT_NAME",
            "AZURE_STORAGE_ACCOUNT_KEY",
            "AZURE_STORAGE_CONTAINER_NAME",
        )
        missing_settings = [
            name for name in required_settings if not getattr(settings, name).strip()
        ]
        if missing_settings:
            raise StorageException(
                f"Missing Azure Blob Storage settings: {', '.join(missing_settings)}"
            )
        self.account_url = (
            f"https://{settings.AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net"
        )
        self.container_name = settings.AZURE_STORAGE_CONTAINER_NAME

    def _create_client(self) -> BlobServiceClient:
        return BlobServiceClient(
            account_url=self.account_url,
            credential=self.settings.AZURE_STORAGE_ACCOUNT_KEY,
        )

    async def save_file(self, file_name: str, data: bytes) -> str:
        """Uploads bytes under a unique blob name and returns that name."""
        storage_key = f"{uuid.uuid4().hex}_{file_name}"
        try:
            async with self._create_client() as client:
                blob = client.get_blob_client(self.container_name, storage_key)
                await blob.upload_blob(data, overwrite=False)
            return storage_key
        except AzureError as error:
            raise StorageException("Failed to upload file to Azure Blob Storage.") from error

    async def read_file(self, file_path: str) -> bytes:
        """Downloads bytes by blob name."""
        try:
            async with self._create_client() as client:
                blob = client.get_blob_client(self.container_name, file_path)
                download = await blob.download_blob()
                return await download.readall()
        except ResourceNotFoundError as error:
            raise StorageException(f"File or container not found: {file_path}") from error
        except AzureError as error:
            raise StorageException("Failed to read file from Azure Blob Storage.") from error

    async def delete_file(self, file_path: str) -> bool:
        """Deletes a blob, returning False if the blob or container is absent."""
        try:
            async with self._create_client() as client:
                blob = client.get_blob_client(self.container_name, file_path)
                await blob.delete_blob(delete_snapshots="include")
            return True
        except ResourceNotFoundError:
            return False
        except AzureError as error:
            raise StorageException("Failed to delete file from Azure Blob Storage.") from error

    async def file_exists(self, file_path: str) -> bool:
        """Checks whether a blob exists."""
        try:
            async with self._create_client() as client:
                blob = client.get_blob_client(self.container_name, file_path)
                return await blob.exists()
        except AzureError as error:
            raise StorageException("Failed to check file in Azure Blob Storage.") from error