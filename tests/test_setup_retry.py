"""Regression tests for transient failures during config-entry setup.

Test dependencies and Python version are pinned in .github/workflows/tests.yml.
Run ``python -m unittest discover -s tests -v``.
"""

from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, patch

import httpx
from homeassistant.exceptions import ConfigEntryNotReady

from custom_components import jcihitachi_tw as integration
from custom_components.jcihitachi_tw.const import (
    API,
    CONF_DEVICES,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_RETRY,
    DOMAIN,
)


class SetupRetryTests(IsolatedAsyncioTestCase):
    """Exercise the real setup entry point without contacting the cloud."""

    def setUp(self):
        self.hass = SimpleNamespace(
            data={},
            async_add_executor_job=AsyncMock(side_effect=lambda job: job()),
            config_entries=SimpleNamespace(async_forward_entry_setups=AsyncMock()),
        )
        self.entry = SimpleNamespace(
            data={
                DOMAIN: {
                    CONF_EMAIL: "test@example.com",
                    CONF_PASSWORD: "test-password",
                    CONF_DEVICES: None,
                    CONF_RETRY: 5,
                }
            }
        )
        self.api = Mock(things={})
        self.api.get_status.return_value = {}
        factory = patch.object(integration, "JciHitachiAWSAPI", return_value=self.api)
        factory.start()
        self.addCleanup(factory.stop)
        coordinator = patch.object(integration, "build_coordinator")
        coordinator.start()
        self.addCleanup(coordinator.stop)

    async def test_transport_failures_request_retry_without_partial_setup(self):
        for error_type in (
            httpx.ConnectError,
            httpx.ConnectTimeout,
            httpx.ReadTimeout,
            httpx.ReadError,
            TimeoutError,
        ):
            with self.subTest(error_type=error_type):
                error = error_type("temporary cloud connection failure")
                self.api.login.side_effect = error

                with self.assertRaises(ConfigEntryNotReady) as raised:
                    await integration.async_setup_entry(self.hass, self.entry)

                self.assertIs(raised.exception.__cause__, error)
                self.assertEqual(self.hass.data, {})
                self.hass.config_entries.async_forward_entry_setups.assert_not_awaited()

    async def test_setup_succeeds_when_connection_recovers(self):
        self.api.login.side_effect = [httpx.ConnectError("offline"), None]

        with self.assertRaises(ConfigEntryNotReady):
            await integration.async_setup_entry(self.hass, self.entry)

        self.assertTrue(await integration.async_setup_entry(self.hass, self.entry))
        self.assertIs(self.hass.data[DOMAIN][API], self.api)
        self.assertEqual(self.api.login.call_count, 2)
        self.hass.config_entries.async_forward_entry_setups.assert_awaited_once_with(
            self.entry, integration.PLATFORMS
        )

    async def test_existing_login_error_behavior_is_unchanged(self):
        for error_type in (RuntimeError, AssertionError):
            with self.subTest(error_type=error_type):
                self.api.login.side_effect = error_type("login rejected")
                self.assertFalse(
                    await integration.async_setup_entry(self.hass, self.entry)
                )
                self.assertEqual(self.hass.data, {})
                self.hass.config_entries.async_forward_entry_setups.assert_not_awaited()

    async def test_unrelated_errors_are_not_converted_to_retries(self):
        self.api.login.side_effect = ValueError("unexpected data")
        with self.assertRaises(ValueError):
            await integration.async_setup_entry(self.hass, self.entry)
        self.assertEqual(self.hass.data, {})

    async def test_existing_api_from_config_flow_is_reused(self):
        self.hass.data[DOMAIN] = {API: self.api}
        self.assertTrue(await integration.async_setup_entry(self.hass, self.entry))
        self.api.login.assert_not_called()
        self.hass.config_entries.async_forward_entry_setups.assert_awaited_once_with(
            self.entry, integration.PLATFORMS
        )
