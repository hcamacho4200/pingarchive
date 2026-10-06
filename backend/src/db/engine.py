from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from environment import get_settings

# engine = create_engine(
#     settings.db_url,
#     pool_pre_ping=True,
#     echo=settings.sql_echo,
# )

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Database:
    """Database Class"""

    def __init__(self):
        settings = get_settings()
        self.engine = create_engine(
            settings.db_url,
            pool_pre_ping=True,
            echo=settings.sql_echo,
        )
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
        )
        self.Base = Base


@lru_cache(maxsize=1)
def get_database():
    return Database()
