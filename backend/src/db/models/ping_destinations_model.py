"""Plugin Credential Model"""

from typing import Self

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum,
    String,
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

    @classmethod
    def get_by_id(cls, session, destination_id: int) -> Self | None:
        """Get a ping destination by ID."""
        return session.query(cls).filter_by(id=destination_id).first()

    @classmethod
    def insert(cls, session, **params) -> Self:
        """Insert a ping destination."""
        destination = cls(**params)
        session.add(destination)
        session.flush()
        session.refresh(destination)
        return destination

    @classmethod
    def update(cls, session, destination_id: int, **params) -> Self:
        """Update a ping destination."""
        destination = cls.get_by_id(session, destination_id)
        if destination is None:
            raise ValueError(f"Ping destination {destination_id} was not found")

        for field in ("name", "ipv4", "ipv6", "host", "location_zone", "address_type", "ping_interval", "enabled"):
            if field in params:
                setattr(destination, field, params[field])

        session.add(destination)
        session.flush()
        session.refresh(destination)
        return destination

    @classmethod
    def delete(cls, session, destination_id: int) -> Self:
        """Delete a ping destination."""
        destination = cls.get_by_id(session, destination_id)
        if destination is None:
            raise ValueError(f"Ping destination {destination_id} was not found")
        session.delete(destination)
        return destination
