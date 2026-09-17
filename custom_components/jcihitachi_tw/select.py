"""JciHitachi integration."""
import datetime
import logging

from homeassistant.components.select import SelectEntity
from homeassistant.util import dt as dt_util

from . import API, COORDINATOR, DOMAIN, JciHitachiEntity

_LOGGER = logging.getLogger(__name__)

# device types that have the monthly power sensors
MONTHLY_DEVICE_TYPES = ("AC", "DH")


async def _async_setup(hass, async_add):
    api = hass.data[DOMAIN][API]
    coordinator = hass.data[DOMAIN][COORDINATOR]

    for thing in api.things.values():
        if thing.type in MONTHLY_DEVICE_TYPES:
            async_add([JciHitachiMonthSelectEntity(thing, coordinator)])


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the select platform."""
    await _async_setup(hass, async_add_entities)


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the select platform from a config entry."""
    await _async_setup(hass, async_add_devices)


def _record_label(record: dict) -> str:
    """"YYYY-MM" of a monthly record; the cloud stamps each month at 00:00 UTC of its first day."""
    return datetime.datetime.fromtimestamp(
        record["Timestamp"] / 1000, tz=datetime.timezone.utc
    ).strftime("%Y-%m")


class JciHitachiMonthSelectEntity(JciHitachiEntity, SelectEntity):
    """Which month the monthly power sensors show; the options are the months the cloud returns.

    Observed 2026-09-17 on three air conditioners (an account in use for more than three years):
    `JciHitachiAWSAPI.refresh_monthly_data(n)` asks for the last n x 31 days and returns one record
    per calendar month, oldest first, with `Timestamp` at 00:00 UTC on the first day of the month.
    Asking for 13, 24, 36 or 60 months always returned the same 13 records (2025-09 to 2026-09),
    so the cloud keeps the current month and the 12 before it. The options are built from what
    the cloud returns rather than from that number, newest first, and default to today's month.

    Replaces the former 0-12 number "Month Selector", whose value was the n above: 1 was the
    current month, 8 showed the month seven months back, and 0 showed no data.

    The chosen record is put on the thing as its only monthly record, so the existing monthly
    power and month sensors work unchanged.
    """

    _attr_translation_key = "month_selector"
    _attr_icon = "mdi:calendar-month"

    # wider than the 13 months the cloud was seen to return; the options follow the answer
    MONTHS_REQUESTED = 24

    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)
        self._records: dict[str, dict] = {}
        self._selected: str | None = None

    @property
    def available(self) -> bool:
        # monthly data comes over HTTP and does not depend on the device's MQTT status
        return True

    @property
    def options(self) -> list[str]:
        if self._records:
            return sorted(self._records, reverse=True)
        return [self._today_label()]

    @property
    def current_option(self) -> str | None:
        return self._selected

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_monthly_data_month_select"

    @staticmethod
    def _today_label() -> str:
        return dt_util.now().strftime("%Y-%m")

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self._selected = self._today_label()
        self.hass.async_create_background_task(
            self._async_refresh(), f"{DOMAIN} monthly data {self._thing.name}"
        )

    async def async_select_option(self, option: str) -> None:
        self._selected = option
        await self._async_refresh()

    async def _async_refresh(self) -> None:
        await self.hass.async_add_executor_job(self._fetch)
        self.async_write_ha_state()
        # the monthly power and month sensors read thing.monthly_data
        self.coordinator.async_update_listeners()

    def _fetch(self) -> None:
        api = self.hass.data[DOMAIN][API]
        try:
            api.refresh_monthly_data(self.MONTHS_REQUESTED, self._thing.name)
        except Exception as err:  # noqa: BLE001 - keep the last good options
            _LOGGER.warning(f"Could not fetch monthly data for {self._thing.name}: {err}")
        else:
            self._records = {
                _record_label(record): record for record in self._thing.monthly_data or []
            }
        if self._selected not in self.options:
            self._selected = self.options[0]
        # right away, so the sensors never read the full list (they show its first record)
        self._thing.monthly_data = (
            [self._records[self._selected]] if self._selected in self._records else []
        )
