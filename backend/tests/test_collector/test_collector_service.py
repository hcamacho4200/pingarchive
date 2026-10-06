import asyncio
from collections.abc import Callable
import importlib
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import nats
import pytest
from nats.aio.client import Client

from collector.collector_service import (
    CollectorServiceCommand,
    CollectorServiceControl,
    CollectorServiceMessage,
    CollectorServiceMessageType,
    CollectorServiceMode,
    CollectorServiceStatus,
)

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_CollectorServiceMessage():
    """Test CollectorServiceMessage"""

    actual = CollectorServiceMessage.build_command(CollectorServiceCommand.START)
    assert actual.message_type == CollectorServiceMessageType.COMMAND
    assert actual.message_id is not None
    assert actual.command == CollectorServiceCommand.START
    assert actual.message is None
    assert actual.status is None
    assert actual.mode == CollectorServiceMode.CLIENT
    assert actual.topic is None

    actual = CollectorServiceMessage.build_message(CollectorServiceStatus.STARTED, "message")
    assert actual.message_type == CollectorServiceMessageType.STATUS
    assert actual.message_id is not None
    assert actual.command is None
    assert actual.message == "message"
    assert actual.status == CollectorServiceStatus.STARTED
    assert actual.mode == CollectorServiceMode.PLUGIN
    assert actual.topic is None

    actual = CollectorServiceMessage.build_register("test_topic", mode=CollectorServiceMode.PLUGIN)
    assert actual.message_type == CollectorServiceMessageType.REGISTER
    assert actual.message_id is not None
    assert actual.command is None
    assert actual.message is None
    assert actual.status is None
    assert actual.mode == CollectorServiceMode.PLUGIN
    assert actual.topic == "test_topic"


@pytest.mark.asyncio
async def test_CollectorServiceControl():
    """Test CollectorServiceControl"""

    collector_service_control_client = CollectorServiceControl(mode=CollectorServiceMode.CLIENT)
    collector_service_control_plugin = CollectorServiceControl(mode=CollectorServiceMode.PLUGIN)

    await collector_service_control_client.start_pipeline()
    await collector_service_control_plugin.start_pipeline()

    await asyncio.sleep(1)
    await collector_service_control_client.cancel()
    await asyncio.sleep(2)


@pytest.mark.asyncio
async def test_nats(nats_patch):
    """Test nats"""

    async def cb(msg):
        logger.info(msg)

    nc = await nats.connect("nats://localhost:4222")
    await nc.subscribe("collector", cb=cb)
    await nc.publish("collector", b"hello")
    await nc.publish("collector", b"hello")
    await nc.publish("collector", b"hello")
    await nc.publish("collector", b"hello")
    await nc.publish("collector", b"hello")
    await nc.publish("collector", b"hello")
    await nc.publish("collector", b"hello")
    await nc.publish("collector", b"hello")
    await nc.publish("collector", b"hello")
    await nc.publish("collector", b"hello")
    await nc.publish("collector", b"hello")
    await nc.publish("collector", b"hello")
    await asyncio.sleep(2)
    await nc.close()


@pytest.mark.focus
@pytest.mark.asyncio
async def test_CollectorServiceControl_plugin():
    """Test CollectorServiceControl"""

    actual_client = CollectorServiceControl(mode=CollectorServiceMode.CLIENT)
    actual_client._nc = MagicMock()
    actual_client._nc.publish = AsyncMock()

    actual_plugin = CollectorServiceControl(mode=CollectorServiceMode.PLUGIN)
    actual_plugin._nc = MagicMock()
    actual_plugin._nc.publish = AsyncMock()

    assert actual_plugin.status == CollectorServiceStatus.INIT
    assert actual_plugin.run_collector.is_set() is False
    assert actual_plugin.cancel_collector.is_set() is False
    assert actual_plugin.status_counter == 0

    msg = await actual_plugin.send_start()
    assert msg.mode == CollectorServiceMode.PLUGIN
    assert msg.message_type == CollectorServiceMessageType.COMMAND
    assert msg.command == CollectorServiceCommand.START
    assert msg.message is None
    assert msg.status is None
    assert msg.topic is None
    assert msg.message_id is not None
    msg = await actual_plugin.recv_message(msg.model_dump_json())
    assert msg.mode == CollectorServiceMode.PLUGIN
    assert msg.message_type == CollectorServiceMessageType.COMMAND
    assert msg.command == CollectorServiceCommand.START
    assert msg.message is None
    assert msg.status is None
    assert msg.topic is None
    assert msg.message_id is not None
    assert False
    await actual_plugin.send_started()
    assert actual_plugin.status == CollectorServiceStatus.STARTED
    assert actual_plugin.run_collector.is_set() is True
    assert actual_plugin.cancel_collector.is_set() is False
    assert actual_plugin.status_counter == 2

    msg = await actual_client.send_pause()
    assert msg.mode == CollectorServiceMode.CLIENT
    assert msg.message_type == CollectorServiceMessageType.COMMAND
    assert msg.command == CollectorServiceCommand.PAUSE
    assert msg.message is None
    assert msg.status is None
    assert msg.topic is None
    assert msg.message_id is not None

    await actual_plugin.send_paused()
    assert actual_plugin.status == CollectorServiceStatus.PAUSED
    assert actual_plugin.run_collector.is_set() is False
    assert actual_plugin.cancel_collector.is_set() is False
    assert actual_plugin.status_counter == 3

    msg = await actual_client.send_resume()
    assert msg.mode == CollectorServiceMode.CLIENT
    assert msg.message_type == CollectorServiceMessageType.COMMAND
    assert msg.command == CollectorServiceCommand.RESUME
    assert msg.message is None
    assert msg.status is None
    assert msg.topic is None
    assert msg.message_id is not None

    await actual_plugin.send_resumed()
    assert actual_plugin.status == CollectorServiceStatus.RESUMED
    assert actual_plugin.run_collector.is_set() is True
    assert actual_plugin.cancel_collector.is_set() is False
    assert actual_plugin.status_counter == 4

    msg = await actual_client.send_cancel()
    assert msg.mode == CollectorServiceMode.CLIENT
    assert msg.message_type == CollectorServiceMessageType.COMMAND
    assert msg.command == CollectorServiceCommand.CANCEL
    assert msg.message is None
    assert msg.status is None
    assert msg.topic is None
    assert msg.message_id is not None

    await actual_plugin.send_canceled()
    assert actual.status == CollectorServiceStatus.CANCELED
    assert actual.run_collector.is_set() is True
    assert actual.cancel_collector.is_set() is True
    assert actual.status_counter == 8
