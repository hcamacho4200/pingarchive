"""Plugin API schema"""

from datetime import datetime

from pydantic import BaseModel, Field


class PluginAPIDataBase(BaseModel):
    """Plugin API schema"""

    name: str = Field(description="Plugin Instance Name", default="")
    plugin_type: str = Field(description="Plugin Type", default="")
    config: str = Field(description="Plugin Configuration", default="{}")
    enabled: bool = Field(description="Plugin Enabled", default=True)


class PluginAPIDataRead(PluginAPIDataBase):
    """Plugin API schema"""

    id: int = Field(description="Plugin ID")
    created_at: datetime | None = Field(description="Plugin Created At")
    updated_at: datetime | None = Field(description="Plugin Updated At")


class PluginAPIDataWrite(PluginAPIDataBase):
    """Plugin API schema"""

    pass


class PluginAPIValidateRequest(BaseModel):
    """Plugin API schema"""

    config_key: str
    config_value: str | int | bool


class PluginAPIValidateResponse(BaseModel):
    """Plugin API schema"""

    config_key: str
    config_value: str | int | bool
    valid: bool
    message: str | None


class PluginAPIRequiredKeysResponse(BaseModel):
    """Plugin API schema"""

    config_key: str
    config_key_label: str
    display: bool = False
