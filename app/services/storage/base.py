from abc import ABC, abstractmethod
from typing import BinaryIO, Optional
from app.services.base import BaseService


class BaseStorageService(BaseService, ABC):
    """Abstract interface for file and document persistence."""

    @abstractmethod
    async def save_file(self, file_name: str, data: bytes) -> str:
        """Saves file bytes and returns storage key or path."""
        pass

    @abstractmethod
    async def read_file(self, file_path: str) -> bytes:
        """Reads and returns file bytes."""
        pass

    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """Deletes file at path."""
        pass

    @abstractmethod
    async def file_exists(self, file_path: str) -> bool:
        """Checks if file exists at path."""
        pass
