"""Location Zones Enum"""

import enum


class LocationZonesEnum(enum.Enum):
    LAN = "LAN"
    VPN = "VPN"
    GATEWAY = "GATEWAY"
    PROVIDER_DNS = "PROVIDER_DNS"
    INTERNET = "INTERNET"
