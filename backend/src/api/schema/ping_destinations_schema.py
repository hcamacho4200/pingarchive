"""Plugin API schema"""

from pydantic import BaseModel, Field

from enums.address_type import AddressTypeEnum
from enums.location_zones import LocationZonesEnum
from enums.ping_interval import PingIntervalEnum

from .create_update import CreateUpdateFields


class PingDestinationsSchema(CreateUpdateFields, BaseModel):
    """PingDestinations API schema"""

    id: int = Field(description="Ping Destination ID")
    name: str = Field(description="Ping Destination Name")
    ipv4: str | None = Field(description="Ping Destination IPv4")
    ipv6: str | None = Field(description="Ping Destination IPv6")
    host: str | None = Field(description="Ping Destination Host")
    location_zone: LocationZonesEnum = Field(description="Ping Destination Localion Zones")
    address_type: AddressTypeEnum | None = Field(description="Ping Destination Address Type")
    ping_interval: PingIntervalEnum | None = Field(description="Ping Destination Ping Interval")
    enabled: bool = Field(description="Ping Destination Enabled")
