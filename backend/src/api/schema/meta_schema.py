"""Metadata schema for API response"""

from pydantic import BaseModel


class MetaAPIData(BaseModel):
    """Metadata for API response"""

    status: str
    status_code: int
    request_id: str
    start_time_epoch: float
    end_time_epoch: float
    duration_ms: float
