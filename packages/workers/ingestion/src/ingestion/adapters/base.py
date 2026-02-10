from abc import ABC, abstractmethod

from ..models import Source, ToolResult


class ToolAdapter(ABC):
    """Base class for all ingestion tool adapters."""

    @abstractmethod
    async def extract(self, source: Source) -> ToolResult:
        """Extract texts from *source* and return a ToolResult."""
        ...
