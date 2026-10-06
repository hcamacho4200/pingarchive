"""Plugin Credential Model"""

from typing import TYPE_CHECKING, Self

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from db.models.mixins.repr import ReprMixin
from db.models.mixins.timestamp import TimestampMixin
from enums.address_type import AddressTypeEnum
from enums.location_zones import LocationZonesEnum
from enums.ping_interval import PingIntervalEnum

from ..base import Base


class PingDestinationsModel(ReprMixin, TimestampMixin, Base):
    """PingDestinations"""

    __tablename__ = "ping_destinations"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=True)
    ipv4: Mapped[str] = mapped_column(String(16), nullable=True)
    ipv6: Mapped[str] = mapped_column(String(40), nullable=True)
    host: Mapped[str] = mapped_column(String(100), nullable=True)
    location_zone: Mapped[Enum] = mapped_column(Enum(LocationZonesEnum), unique=False, default=AddressTypeEnum.HOST)
    address_type: Mapped[Enum] = mapped_column(Enum(AddressTypeEnum), unique=False, default=LocationZonesEnum.LAN)
    ping_interval: Mapped[int] = mapped_column(Enum(PingIntervalEnum), unique=False, default=PingIntervalEnum.SECOND_1)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=True)

    __table_args__ = (
        CheckConstraint(
            """
            (address_type = 'HOST' AND host IS NOT NULL) OR
            (address_type = 'IPV4' AND ipv4 IS NOT NULL AND ipv4 LIKE '%.%.%.%') OR
            (address_type = 'IPV6' AND ipv6 IS NOT NULL AND ipv6 LIKE '%:%')
            """,
            name="check_address_type_exclusivity",
        ),
    )

    @classmethod
    def get_list(cls, session) -> list[Self]:
        """Get list of plugins"""
        return session.query(cls).all()
