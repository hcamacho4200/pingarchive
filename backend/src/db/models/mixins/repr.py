from sqlalchemy.inspection import inspect


class ReprMixin:
    """Mixin to add __repr__ to a SQLAlchemy model"""

    def __repr__(self) -> str:
        cls_name = self.__class__.__name__
        mapper = inspect(self.__class__)

        attrs = []
        if mapper:
            for column in mapper.columns:
                name = column.key
                value = getattr(self, name)
                attrs.append(f"{name}={value!r}")

            return f"{cls_name}({', '.join(attrs)})"
        return f"{cls_name}({self.__dict__})"
