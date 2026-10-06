"""Models to handle UTC datetime data"""

from datetime import UTC, datetime

from sqlalchemy.types import DateTime, TypeDecorator


class UTCDateTime(TypeDecorator):
    """Represents datetime objects that are always stored/returned in UTC"""

    impl = DateTime
    cache_ok = True
    python_type = datetime  # pyright: ignore[reportAssignmentType, reportIncompatibleMethodOverride]

    def process_bind_param(self, value, dialect):
        if value is not None:
            if value.tzinfo is None:
                raise ValueError("Naive datetime not allowed")
            return value.astimezone(UTC).replace(tzinfo=None)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return value.replace(tzinfo=UTC)
        return value

    def process_literal_param(self, value, dialect):  # pyright: ignore[reportIncompatibleMethodOverride]
        if value is not None:
            if value.tzinfo is None:
                raise ValueError("Naive datetime not allowed")
            return value.astimezone(UTC).replace(tzinfo=None)
        return value
