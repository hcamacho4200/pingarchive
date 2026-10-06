"""Create and Update Fields"""

from datetime import datetime

from pydantic import BaseModel, Field


class CreateUpdateFields(BaseModel):
    """PingDestinations API schema"""

    created_at: datetime | None = Field(description="Plugin Created At")
    updated_at: datetime | None = Field(description="Plugin Updated At")
