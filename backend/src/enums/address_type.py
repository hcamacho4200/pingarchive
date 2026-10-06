"""Location Zones Enum"""

import enum


class AddressTypeEnum(enum.Enum):
    IPV4 = "IPV4"
    IPV6 = "IPV6"
    HOST = "HOST"
