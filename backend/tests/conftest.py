"""Conftest.py fixtures"""

from collections import defaultdict
from collections.abc import Awaitable, Callable, Generator
from typing import override
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from environment import Settings
from main import app

client = TestClient(app)


@pytest.fixture()
def settings():
    """Settings Fixture"""

    return Settings(
        environment="pytest",
        log_level="DEBUG",
        version="1.0.0",
        # Encryption
        # Database Credentials
        db_url="sqlite:///",
        sql_echo=True,
        sqlalchemy_pool_size=5,
        # API Configuration
        api_host="api_host=0.0.0.0",
        api_port=8002,
        api_reload=True,
        api_workers=1,
        ping_engine_host="0.0.0.0",
        ping_engine_port=8100,
    )


@pytest.fixture
def patched_settings(settings) -> Generator[Settings]:
    """Patched Settings Fixture"""

    patches = [
        patch("main.get_settings", return_value=settings),
        patch("db.get_settings", return_value=settings),
        # patch("streaming.actors.bar_actor.get_settings", return_value=settings),
        patch("plugins.plugin_configurations.get_settings", return_value=settings),
    ]

    for p in patches:
        p.start()
    yield settings
    for p in patches:
        p.stop()


class InMemoryBus:
    """InMemoryBus class"""

    def __init__(self):
        self.subscribers: dict[str, list[Callable[[bytes]]]] = defaultdict(list)

    async def publish(self, subject: str, data: bytes):

        if subject not in self.subscribers:
            return

        for handler in self.subscribers[subject]:
            await handler(data)

    async def subscribe(self, subject: str, handler: Callable[[bytes]]):
        self.subscribers[subject].append(handler)

    @staticmethod
    async def connect(connect: str):
        return InMemoryBus


@pytest.fixture
def nats_patch():
    """NATS InMemoryBus fixture"""

    nats = InMemoryBus

    patches = [
        patch("tests.test_collector_service.nats", return_value=nats),
    ]

    for p in patches:
        p.start()
    yield nats
    for p in patches:
        p.stop()
