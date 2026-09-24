from abc import ABC
import structlog
from app.core.config import Settings


class BaseService(ABC):
    """Abstract base class for domain services."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.logger = structlog.get_logger(self.__class__.__name__)
