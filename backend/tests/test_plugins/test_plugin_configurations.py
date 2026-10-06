"""Test plugin configurations"""

import json
import logging
from typing import cast

import pytest

from crypto import decrypt, encrypt
from plugins.plugin_configurations import CONFIG_FIELD_REGISTRY, PluginConfig, PluginConfigData, PluginConfigKey

logger = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "config, required_keys, expected",
    (
        pytest.param(
            {
                PluginConfigKey.AUTH_API_KEY: "qn51SAi25QCtcWKPN_wI7jfhra_wMAYj",
                PluginConfigKey.HOSTNAME: "192.168.1.1",
                PluginConfigKey.PORT: 8443,
            },
            [PluginConfigKey.AUTH_API_KEY, PluginConfigKey.HOSTNAME, PluginConfigKey.PORT, PluginConfigKey.URL],
            ValueError,
            id="missing timeout",
        ),
        pytest.param(
            {
                PluginConfigKey.AUTH_API_KEY: "qn51SAi25QCtcWKPN_wI7jfhra_wMAYj",
                PluginConfigKey.HOSTNAME: "192.168.1.1",
                PluginConfigKey.PORT: 8443,
                PluginConfigKey.URL: "https://192.168.1.1:8443",
            },
            [PluginConfigKey.AUTH_API_KEY, PluginConfigKey.HOSTNAME, PluginConfigKey.PORT, PluginConfigKey.URL],
            None,
            id="valid config",
        ),
    ),
)
def test_plugin_config_required_keys(config, required_keys, expected):
    """Test plugin configurations"""

    if expected is None:
        _ = PluginConfig(config, required_keys)
    else:
        with pytest.raises(expected):
            _ = PluginConfig(config, required_keys)
    assert True


@pytest.mark.parametrize(
    "config, required_keys, expected",
    (
        pytest.param(
            {
                PluginConfigKey.AUTH_API_KEY: "qn51SAi25QCtcWKPN_wI7jfhra_wMAYj",
            },
            [PluginConfigKey.AUTH_API_KEY],
            None,
            id="AUTH_API_KEY valid",
        ),
        pytest.param(
            {
                PluginConfigKey.AUTH_API_KEY: "",
            },
            [PluginConfigKey.AUTH_API_KEY],
            ValueError,
            id="AUTH_API_KEY invalid",
        ),
        pytest.param(
            {
                PluginConfigKey.AUTH_USERNAME: "username",
            },
            [PluginConfigKey.AUTH_USERNAME],
            None,
            id="AUTH_USERNAME valid",
        ),
        pytest.param(
            {
                PluginConfigKey.AUTH_USERNAME: "",
            },
            [PluginConfigKey.AUTH_USERNAME],
            ValueError,
            id="AUTH_USERNAME invalid",
        ),
        pytest.param(
            {
                PluginConfigKey.AUTH_PASSWORD: "password",
            },
            [PluginConfigKey.AUTH_PASSWORD],
            None,
            id="AUTH_PASSWORD valid",
        ),
        pytest.param(
            {
                PluginConfigKey.AUTH_PASSWORD: "",
            },
            [PluginConfigKey.AUTH_PASSWORD],
            ValueError,
            id="AUTH_PASSWORD invalid",
        ),
        pytest.param(
            {
                PluginConfigKey.AUTH_TOKEN: "token",
            },
            [PluginConfigKey.AUTH_TOKEN],
            None,
            id="AUTH_TOKEN valid",
        ),
        pytest.param(
            {
                PluginConfigKey.AUTH_TOKEN: "",
            },
            [PluginConfigKey.AUTH_TOKEN],
            ValueError,
            id="AUTH_TOKEN invalid",
        ),
        pytest.param(
            {
                PluginConfigKey.HOSTNAME: "192.168.1.1",
            },
            [PluginConfigKey.HOSTNAME],
            None,
            id="HOSTNAME valid",
        ),
        pytest.param(
            {
                PluginConfigKey.HOSTNAME: "",
            },
            [PluginConfigKey.HOSTNAME],
            ValueError,
            id="HOSTNAME invalid",
        ),
        pytest.param(
            {
                PluginConfigKey.PORT: 443,
            },
            [PluginConfigKey.PORT],
            None,
            id="PORT valid",
        ),
        pytest.param(
            {
                PluginConfigKey.PORT: "string",
            },
            [PluginConfigKey.PORT],
            ValueError,
            id="PORT invalid - string",
        ),
        pytest.param(
            {
                PluginConfigKey.PORT: 100000,
            },
            [PluginConfigKey.PORT],
            ValueError,
            id="PORT invalid - out of range max",
        ),
        pytest.param(
            {
                PluginConfigKey.PORT: -100000,
            },
            [PluginConfigKey.PORT],
            ValueError,
            id="PORT invalid - out of range min",
        ),
        pytest.param(
            {
                PluginConfigKey.URL: "http://something.something.darkside",
            },
            [PluginConfigKey.URL],
            None,
            id="URL valid",
        ),
        pytest.param(
            {
                PluginConfigKey.URL: "",
            },
            [PluginConfigKey.URL],
            ValueError,
            id="URL invalid",
        ),
        pytest.param(
            {
                PluginConfigKey.TIMEOUT: 50,
            },
            [PluginConfigKey.TIMEOUT],
            None,
            id="TIMEOUT valid",
        ),
        pytest.param(
            {
                PluginConfigKey.TIMEOUT: "asdfasdf",
            },
            [PluginConfigKey.TIMEOUT],
            ValueError,
            id="TIMEOUT invalid - string",
        ),
        pytest.param(
            {
                PluginConfigKey.TIMEOUT: -1,
            },
            [PluginConfigKey.TIMEOUT],
            ValueError,
            id="TIMEOUT invalid - out of range min",
        ),
        pytest.param(
            {
                PluginConfigKey.TIMEOUT: 2700,
            },
            [PluginConfigKey.TIMEOUT],
            ValueError,
            id="TIMEOUT invalid - out of range max",
        ),
        pytest.param(
            {},
            [PluginConfigKey.TIMEOUT],
            None,
            id="TIMEOUT default override",
        ),
    ),
)
def test_plugin_config_validation(config, required_keys, expected):
    """Test plugin configurations validation"""

    if expected is None:
        _validated: PluginConfig = PluginConfig(config, required_keys)
        if PluginConfigKey.TIMEOUT in config:
            assert _validated.validated_config.timeout == config[PluginConfigKey.TIMEOUT]
        else:
            assert _validated.validated_config.timeout == CONFIG_FIELD_REGISTRY[PluginConfigKey.TIMEOUT].default

    else:
        with pytest.raises(expected):
            _ = PluginConfig(config, required_keys)
    assert True


def test_plugin_config_data(patched_settings):
    """Test plugin configurations data"""
    settings = patched_settings
    config = {
        PluginConfigKey.AUTH_API_KEY: encrypt("auth_api_key", settings.encryption_key),
        PluginConfigKey.HOSTNAME: "192.168.1.1",
        PluginConfigKey.PORT: 8443,
        PluginConfigKey.URL: "https://something.something.darkside",
        PluginConfigKey.TIMEOUT: 50,
        PluginConfigKey.AUTH_USERNAME: "auth_username",
        PluginConfigKey.AUTH_PASSWORD: encrypt("auth_password", settings.encryption_key),
        PluginConfigKey.AUTH_TOKEN: encrypt("auth_token", settings.encryption_key),
    }

    required_keys = [
        PluginConfigKey.AUTH_API_KEY,
        PluginConfigKey.HOSTNAME,
        PluginConfigKey.PORT,
        PluginConfigKey.URL,
        PluginConfigKey.TIMEOUT,
        PluginConfigKey.AUTH_USERNAME,
        PluginConfigKey.AUTH_PASSWORD,
        PluginConfigKey.AUTH_TOKEN,
    ]

    actual = PluginConfig(config, required_keys)
    assert actual.validated_config.auth_api_key == decrypt(config[PluginConfigKey.AUTH_API_KEY], settings.encryption_key)
    assert actual.validated_config.hostname == config[PluginConfigKey.HOSTNAME]
    assert actual.validated_config.port == config[PluginConfigKey.PORT]
    assert actual.validated_config.url == config[PluginConfigKey.URL]
    assert actual.validated_config.timeout == config[PluginConfigKey.TIMEOUT]
    assert actual.validated_config.auth_username == config[PluginConfigKey.AUTH_USERNAME]
    assert actual.validated_config.auth_password == decrypt(config[PluginConfigKey.AUTH_PASSWORD], settings.encryption_key)
    assert actual.validated_config.auth_token == decrypt(config[PluginConfigKey.AUTH_TOKEN], settings.encryption_key)

    logger.info(actual.validated_config.model_dump_json())
    assert True


def test_plugin_configurations_read_config(patched_settings):
    settings = patched_settings
    config = {
        "auth_api_key": encrypt("auth_api_key", settings.encryption_key),
        "auth_username": "auth_username",
        "auth_password": encrypt("auth_password", settings.encryption_key),
        "auth_token": encrypt("auth_token", settings.encryption_key),
        "hostname": "192.168.1.1",
        "port": 8443,
        "timeout": 500,
        "url": "https://something.something.darkside",
    }

    required = []
    actual = PluginConfig(config, required)  # pyright: ignore[reportArgumentType]
    logger.info(actual.validated_config.auth_token)
    logger.info(actual.validated_config.model_dump_json())


def test_plugin_configurations_validate_entry():
    """Validate a single entry"""

    actual = PluginConfig.validate_config(cast(PluginConfigKey, "auth_api_key"), "qn51SAi25QCtcWKPN_wI7jfhra_wMAYj")
    assert actual

    with pytest.raises(ValueError):
        PluginConfig.validate_config(cast(PluginConfigKey, "auth_api_key"), "")


def test_plugin_configurations_wedges(patched_settings):
    settings = patched_settings

    config = {
        "auth_api_key": encrypt("auth_api_key", settings.encryption_key),
        "auth_username": "auth_username",
        "auth_password": encrypt("auth_password", settings.encryption_key),
        "auth_token": encrypt("auth_token", settings.encryption_key),
        "hostname": "192.168.1.1",
        "port": 8443,
        "timeout": 500,
        "url": "https://something.something.darkside",
    }
    actual = PluginConfig(cast(dict[PluginConfigKey, str | int | bool], config), [])
    dump = actual.validated_config.model_dump()
    assert dump["auth_api_key"] != "auth_api_key"
    assert dump["auth_username"] == "auth_username"
    assert dump["auth_password"] != "auth_password"
    assert dump["auth_token"] != "auth_token"
    assert dump["hostname"] == "192.168.1.1"
    assert dump["port"] == 8443
    assert dump["timeout"] == 500
    assert dump["url"] == "https://something.something.darkside"
    actual.validated_config.auth_api_key = "auth_api_key"
    actual.validated_config.auth_username = "auth_username"
    actual.validated_config.auth_password = "auth_password"
    actual.validated_config.auth_token = "auth_token"
    actual.validated_config.hostname = "192.168.1.1"
    actual.validated_config.port = 8443
    actual.validated_config.timeout = 500
    actual.validated_config.url = "https://something.something.darkside"

    actual.validated_config.auth_api_key = "new_auth_api_key"
    actual.validated_config.auth_password = "new_auth_password"
    actual.validated_config.auth_token = "new_auth_token"

    dump = actual.validated_config.model_dump()
    assert dump["auth_api_key"] != "new_auth_api_key"
    assert dump["auth_password"] != "new_auth_password"
    assert dump["auth_token"] != "new_auth_token"


def test_plugin_configurations_encrypt_seralize(patched_settings):
    """Check to make sure encrypted fields are filtered"""
    settings = patched_settings

    config = {
        "auth_api_key": encrypt("auth_api_key", settings.encryption_key),
        "hostname": "192.168.1.1",
        "port": 8443,
        "url": "https://something.something.darkside",
    }

    plugin_config = PluginConfig(cast(dict[PluginConfigKey, str | int | bool], config), [])
    assert plugin_config.validated_config.auth_api_key == "auth_api_key"
    assert plugin_config.validated_config.auth_token is None
    assert plugin_config.validated_config.auth_password is None
    model = json.loads(plugin_config.validated_config.model_dump_json())
    assert model["auth_api_key"] == "[ENCRYPTED]"
    assert model["auth_token"] is None
    assert model["auth_password"] is None
    logger.info(model)

    config = {
        "auth_api_key": encrypt("auth_api_key", settings.encryption_key),
        "auth_username": "auth_username",
        "auth_password": encrypt("auth_password", settings.encryption_key),
        "auth_token": encrypt("auth_token", settings.encryption_key),
        "hostname": "192.168.1.1",
        "port": 8443,
        "timeout": 500,
        "url": "https://something.something.darkside",
    }
    plugin_config = PluginConfig(cast(dict[PluginConfigKey, str | int | bool], config), [])
    assert plugin_config.validated_config.auth_api_key == "auth_api_key"
    assert plugin_config.validated_config.auth_token == "auth_token"
    assert plugin_config.validated_config.auth_password == "auth_password"
    model = json.loads(plugin_config.validated_config.model_dump_json())
    assert model["auth_api_key"] == "[ENCRYPTED]"
    assert model["auth_token"] == "[ENCRYPTED]"
    assert model["auth_password"] == "[ENCRYPTED]"
    logger.info(model)


def tester(patched_settings):

    config = {
        "auth_api_key": "auth_api_key",
        "auth_username": "auth_username",
        "hostname": "192.168.1.1",
        "port": 8443,
        "timeout": 500,
        "url": "https://something.something.darkside",
    }

    config_from_web = PluginConfigData()

    for key, value in config.items():
        setattr(config_from_web, key, value)

    logger.info(config_from_web)
    logger.info(config_from_web.model_dump_json())
    logger.info(config_from_web.model_dump(context={"redact_encrypted": False}))
    pass
