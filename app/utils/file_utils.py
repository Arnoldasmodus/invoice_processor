import os
import re
import tempfile
from contextlib import asynccontextmanager
from typing import AsyncGenerator, BinaryIO
import aiofiles


@asynccontextmanager
async def get_temp_file(suffix: str = ".pdf") -> AsyncGenerator[str, None]:
    """Provides a temporary file path that is automatically cleaned up on exit."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    try:
        yield path
    finally:
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass


def sanitize_filename(filename: str) -> str:
    """Sanitizes a filename to prevent directory traversal and unsafe characters."""
    clean = os.path.basename(filename)
    clean = re.sub(r"[^a-zA-Z0-9_.-]", "_", clean)
    return clean or "unnamed_document.pdf"


async def save_upload_to_file(stream: BinaryIO, target_path: str, chunk_size: int = 1024 * 1024) -> int:
    """Asynchronously writes a stream to a target file path, returning total bytes written."""
    total_bytes = 0
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    async with aiofiles.open(target_path, "wb") as out_file:
        while chunk := stream.read(chunk_size):
            await out_file.write(chunk)
            total_bytes += len(chunk)
    return total_bytes


async def read_file_chunks(file_path: str, chunk_size: int = 1024 * 1024) -> AsyncGenerator[bytes, None]:
    """Yields chunks of a file asynchronously."""
    async with aiofiles.open(file_path, "rb") as f:
        while chunk := await f.read(chunk_size):
            yield chunk
