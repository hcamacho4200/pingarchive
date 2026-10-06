"""Plugin Model"""

from typing import TYPE_CHECKING, Self

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.mixins.repr import ReprMixin
from db.models.mixins.timestamp import TimestampMixin

from ..base import Base

if TYPE_CHECKING:
    from .plugins_credential import PluginsCredentialModel


class PluginsModel(ReprMixin, TimestampMixin, Base):
    """Plugins model"""

    __tablename__ = "plugins"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    plugin_type: Mapped[str] = mapped_column(String(50))
    config: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    credentials: Mapped[list[PluginsCredentialModel]] = relationship(
        back_populates="plugins",
        cascade="all, delete-orphan",
    )

    @classmethod
    def get_by_id(cls, session, plugin_id) -> Self:
        """Get plugin by id"""
        return session.query(cls).filter_by(id=plugin_id).first()

    @classmethod
    def get_list(cls, session) -> list[Self]:
        """Get list of plugins"""
        return session.query(cls).all()

    @classmethod
    def delete(cls, session, plugin_id: int):
        """delete a plugin"""
        rec = cls.get_by_id(session, plugin_id)
        session.delete(rec)
        return rec

    @classmethod
    def insert(cls, session, **parms):
        """Insert a plugin"""

        plugin = cls(**parms)
        session.add(plugin)
        session.flush()
        session.refresh(plugin)
        return plugin

    @classmethod
    def update(cls, session, plugin_id: int, **parms):
        """Insert a plugin"""

        rec = cls.get_by_id(session, plugin_id)
        rec.name = parms.get("name", rec.name)
        rec.plugin_type = parms.get("plugin_type", rec.plugin_type)
        rec.config = parms.get("config", rec.config)
        rec.enabled = parms.get("enabled", rec.enabled)
        session.add(rec)
        session.flush()
        session.refresh(rec)
        return rec
