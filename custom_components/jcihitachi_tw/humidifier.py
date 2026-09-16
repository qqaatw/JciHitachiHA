"""JciHitachi integration."""
import logging

from homeassistant.components.humidifier import (HumidifierEntityFeature,
                                                 HumidifierDeviceClass,
                                                 HumidifierEntity)

from . import API, COORDINATOR, DOMAIN, UPDATED_DATA, JciHitachiEntity

_LOGGER = logging.getLogger(__name__)

MODE_AUTO = "auto"
MODE_CUSTOM = "custom"
MODE_CONTINUOUS = "continuous"
MODE_CLOTHES_DRY = "clothes_dry"
MODE_AIR_PURIFY = "air_purify"
MODE_MOLD_PREV = "mold_prev"
MODE_LOW_HUMIDITY = "low_humidity"
MODE_ECO_COMFORT = "eco_comfort"

AVAILABLE_MODES = [
    MODE_AUTO,
    MODE_CUSTOM,
    MODE_CONTINUOUS,
    MODE_CLOTHES_DRY,
    MODE_AIR_PURIFY,
    MODE_MOLD_PREV,
    "unsupported",
    "unsupported",
    MODE_LOW_HUMIDITY,
    MODE_ECO_COMFORT
]


async def _async_setup(hass, async_add):
    api = hass.data[DOMAIN][API]
    coordinator = hass.data[DOMAIN][COORDINATOR]

    for thing in api.things.values():
        if thing.type == "DH":
            status = hass.data[DOMAIN][UPDATED_DATA][thing.name]
            supported_features = JciHitachiDehumidifierEntity.calculate_supported_features(
                status
            )
            async_add(
                [JciHitachiDehumidifierEntity(
                    thing, coordinator, supported_features)],
                update_before_add=True
            )

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the humidifier platform."""
    await _async_setup(hass, async_add_entities)

async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the humidifier platform from a config entry."""
    await _async_setup(hass, async_add_devices)


class JciHitachiDehumidifierEntity(JciHitachiEntity, HumidifierEntity):
    def __init__(self, thing, coordinator, supported_features):
        super().__init__(thing, coordinator)
        self._supported_features = supported_features
        self._available_modes = [mode for i, mode in enumerate(AVAILABLE_MODES) if 2 ** i & self._thing.support_code.Mode != 0]
        self._attr_translation_key = "dehumidifier_humidifier"

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._supported_features

    @property
    def current_humidity(self):
        """Return the current humidity."""
        status = self.hass.data[DOMAIN][UPDATED_DATA][self._thing.name]
        if status:
            return status.indoor_humidity
        return None

    @property
    def target_humidity(self):
        """Return the target humidity."""
        status = self.hass.data[DOMAIN][UPDATED_DATA][self._thing.name]
        if status:
            return status.target_humidity
        return None

    @property
    def max_humidity(self):
        """Return the maximum humidity."""
        status = self.hass.data[DOMAIN][UPDATED_DATA][self._thing.name]
        return status.max_humidity

    @property
    def min_humidity(self):
        """Return the minimum humidity."""
        status = self.hass.data[DOMAIN][UPDATED_DATA][self._thing.name]
        return status.min_humidity

    @property
    def mode(self):
        status = self.hass.data[DOMAIN][UPDATED_DATA][self._thing.name]
        if status:
            return status.mode

        _LOGGER.error("Missing mode.")
        return None

    @property
    def available_modes(self):
        return self._available_modes

    @property
    def is_on(self):
        status = self.hass.data[DOMAIN][UPDATED_DATA][self._thing.name]
        if status:
            if status.power == "off":
                return False
            elif status.power == "on":
                return True
        
        _LOGGER.error("Missing is_on.")
        return None

    @property
    def device_class(self):
        return HumidifierDeviceClass.DEHUMIDIFIER

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_dehumidifier"

    @staticmethod
    def calculate_supported_features(status):
        support_flags = HumidifierEntityFeature.MODES
        return support_flags

    def set_mode(self, mode):
        """Set new target preset mode."""

        _LOGGER.debug(f"Set {self.name} mode to {mode}")

        if mode in [MODE_AUTO, MODE_CUSTOM, MODE_CONTINUOUS, MODE_CLOTHES_DRY,
                    MODE_AIR_PURIFY, MODE_MOLD_PREV, MODE_LOW_HUMIDITY, MODE_ECO_COMFORT]:
            self.put_queue(status_name="mode", status_str_value=mode)
        else:
            _LOGGER.error("Invalid mode.")
        self.update()

    def set_humidity(self, humidity):
        """Set new target humidity."""

        target_humidity = int(humidity)
        _LOGGER.debug(f"Set {self.name} humidity to {target_humidity}")

        self.put_queue(status_name="target_humidity", status_value=target_humidity)
        self.update()

    def turn_on(self, **kwargs):
        """Turn the device on."""
        _LOGGER.debug(f"Turn {self.name} on")
        self.put_queue(status_name="power", status_str_value="on")
        self.update()

    def turn_off(self, **kwargs):
        """Turn the device off."""
        _LOGGER.debug(f"Turn {self.name} off")
        self.put_queue(status_name="power", status_str_value="off")
        self.update()
