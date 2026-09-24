from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class Point(BaseModel):
    """2D Point coordinate in polygon."""
    model_config = ConfigDict(str_strip_whitespace=True)

    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")


class BoundingBox(BaseModel):
    """Bounding polygon or box for an extracted element."""
    model_config = ConfigDict(str_strip_whitespace=True)

    page_number: int = Field(1, description="1-based page number")
    polygon: List[Point] = Field(default_factory=list, description="Polygon boundary points")


class ConfidenceScore(BaseModel):
    """Normalized confidence score."""
    model_config = ConfigDict(str_strip_whitespace=True)

    value: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")


class KeyValuePair(BaseModel):
    """Extracted key-value pair representation."""
    model_config = ConfigDict(str_strip_whitespace=True)

    key: str = Field(..., description="Key label")
    value: Optional[str] = Field(None, description="Extracted value string")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Extraction confidence score")
    bounding_box: Optional[BoundingBox] = Field(None, description="Key/Value location")
