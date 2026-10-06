"""Database Module"""

import logging
import threading
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from environment import get_settings

from . import models  # noqa: F401
from .base import Base

logger = logging.getLogger(__name__)


class Database:
    """Database Class"""

    _engine: Engine
    _session_local: sessionmaker
    _base: type[DeclarativeBase]
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    logger.info("Setting up and Creating database")
                    instance = super().__new__(cls)
                    settings = get_settings()
                    instance._engine = create_engine(settings.db_url, pool_pre_ping=True, echo=settings.sql_echo, pool_size=settings.sqlalchemy_pool_size)
                    instance._session_local = sessionmaker(
                        bind=instance._engine,
                        autoflush=False,
                        autocommit=False,
                    )
                    instance._base = Base
                    instance._base.metadata.create_all(instance._engine)
                    cls._instance = instance
        return cls._instance

    @contextmanager
    def session_context_write(self):
        """Session Context Manager"""
        session = self._session_local()
        yield session
        session.commit()
        session.close()

    @contextmanager
    def session_context_read(self):
        """Session Context Manager"""
        session = self._session_local()
        yield session

        session.close()

    @property
    def engine(self):
        """Return the engine"""
        return self._engine

    @property
    def base(self):
        """Return the base"""
        return self._base
