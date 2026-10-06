"""Plugin Credential Model"""

from typing import TYPE_CHECKING

from sqlalchemy import (
    ForeignKey,
    LargeBinary,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.models.mixins.repr import ReprMixin
from db.models.mixins.timestamp import TimestampMixin

from ..base import Base

if TYPE_CHECKING:
    from .plugins import PluginsModel


class PluginsCredentialModel(ReprMixin, TimestampMixin, Base):
    """Plugins Credential Model"""

    __tablename__ = "plugin_credentials"
    id: Mapped[int] = mapped_column(primary_key=True)
    plugin_id: Mapped[int] = mapped_column(
        ForeignKey("plugins.id", ondelete="CASCADE"),
        index=True,
    )
    credential_name: Mapped[str] = mapped_column(String(100))
    encrypted_value: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
    )
    plugins: Mapped[PluginsModel] = relationship(back_populates="credentials")

    __table_args__ = (
        UniqueConstraint(
            "plugin_id",
            "credential_name",
            name="uq_plugin_credential",
        ),
    )
