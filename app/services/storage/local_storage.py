import os
import uuid
import aiofiles
from app.core.config import Settings
from app.core.exceptions import StorageException
from app.services.storage.base import BaseStorageService


class LocalStorageService(BaseStorageService):
    """File storage implementation using local filesystem."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
        self.base_dir = os.path.abspath(self.settings.LOCAL_STORAGE_DIR)
        os.makedirs(self.base_dir, exist_ok=True)

    def _resolve_path(self, relative_path: str) -> str:
        """Resolves full path and guards against path traversal."""
        full_path = os.path.abspath(os.path.join(self.base_dir, relative_path))
        if not full_path.startswith(self.base_dir):
            raise StorageException(f"Invalid path traversal attempt: {relative_path}")
        return full_path

    async def save_file(self, file_name: str, data: bytes) -> str:
        """Saves file with unique prefix in local storage folder."""
        try:
            unique_name = f"{uuid.uuid4().hex[:8]}_{file_name}"
            target_path = self._resolve_path(unique_name)

            async with aiofiles.open(target_path, "wb") as f:
                await f.write(data)

            self.logger.info("File saved to local storage", path=target_path)
            return unique_name
        except Exception as e:
            self.logger.error("Failed to save file", error=str(e))
            raise StorageException(f"Failed to write file to local disk: {str(e)}") from e

    async def read_file(self, file_path: str) -> bytes:
        """Reads file bytes from storage."""
        target_path = self._resolve_path(file_path)
        if not os.path.isfile(target_path):
            raise StorageException(f"File not found: {file_path}")

        try:
            async with aiofiles.open(target_path, "rb") as f:
                return await f.read()
        except Exception as e:
            self.logger.error("Failed to read file", path=file_path, error=str(e))
            raise StorageException(f"Failed to read file: {str(e)}") from e

    async def delete_file(self, file_path: str) -> bool:
        """Deletes file from storage."""
        target_path = self._resolve_path(file_path)
        if not os.path.exists(target_path):
            return False

        try:
            os.remove(target_path)
            return True
        except Exception as e:
            self.logger.error("Failed to delete file", path=file_path, error=str(e))
            raise StorageException(f"Failed to delete file: {str(e)}") from e

    async def file_exists(self, file_path: str) -> bool:
        """Checks if file exists in storage."""
        target_path = self._resolve_path(file_path)
        return os.path.isfile(target_path)
