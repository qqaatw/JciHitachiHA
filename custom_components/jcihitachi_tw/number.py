"""JciHitachi integration."""
import logging

from homeassistant.components.number import NumberEntity
from homeassistant.const import UnitOfTime

from . import API, COORDINATOR, DOMAIN, UPDATED_DATA, JciHitachiEntity

_LOGGER = logging.getLogger(__name__)


async def _async_setup(hass, async_add):
    api = hass.data[DOMAIN][API]
    coordinator = hass.data[DOMAIN][COORDINATOR]

    for thing in api.things.values():
        entities = [JciHitachiMonthlyDataSelectorNumberEntity(thing, coordinator)]
        if thing.type == "AC" and \
                getattr(thing.support_code, "SleepModeRemainingTime", "unsupported") != "unsupported":
            entities.append(JciHitachiACSleepDurationNumberEntity(thing, coordinator))
        async_add(entities, update_before_add=True)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the number platform."""
    await _async_setup(hass, async_add_entities)

async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the number platform from a config entry."""
    await _async_setup(hass, async_add_devices)


class JciHitachiMonthlyDataSelectorNumberEntity(JciHitachiEntity, NumberEntity):
    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)
        self._value = 0

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._thing.name} Month Selector"
    
    @property
    def native_value(self):
        """Return the value of the entity."""
        return self._value

    @property
    def native_min_value(self):
        """Return the minimum month."""
        return 0

    @property
    def native_max_value(self):
        """Return the maximum month."""
        return 12

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_monthly_data_selector_number"

    def set_native_value(self, value):
        """Set new month."""
        _LOGGER.debug(f"Set {self.name} value to {value}")
        self._value = value

        api = self.hass.data[DOMAIN][API]
        api.refresh_monthly_data(int(self._value), self._thing.name)
        self.update()


class JciHitachiACSleepDurationNumberEntity(JciHitachiEntity, NumberEntity):
    """Sleep mode countdown duration of the air conditioner, in hours."""

    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)
        support = getattr(thing.support_code, "SleepModeRemainingTime", "unsupported")
        self._max_minutes = support if isinstance(support, int) and support > 0 else 24 * 60

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._thing.name} Sleep Duration"

    @property
    def native_value(self):
        """Return the current countdown in hours, None if sleep mode is off."""
        status = self.hass.data[DOMAIN][UPDATED_DATA].get(self._thing.name, None)
        if status and isinstance(status.sleep_timer, int) and status.sleep_timer > 0:
            return max(1, round(status.sleep_timer / 60))
        return None

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return UnitOfTime.HOURS

    @property
    def native_min_value(self):
        """Return the minimum duration."""
        return 1

    @property
    def native_max_value(self):
        """Return the maximum duration supported by the device."""
        return self._max_minutes // 60

    @property
    def native_step(self):
        """Return the step."""
        return 1

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_sleep_duration_number"

    def set_native_value(self, value):
        """Start sleep mode counting down for the given hours."""
        _LOGGER.debug(f"Set {self.name} to {value} hour(s)")
        self.put_queue(status_name="sleep_timer", status_value=int(value) * 60)
        self.update()
