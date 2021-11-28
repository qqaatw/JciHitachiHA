"""JciHitachi integration."""
import logging

from homeassistant.components.humidifier import HumidifierEntity
from homeassistant.components.humidifier.const import (
    SUPPORT_MODES,
    DEVICE_CLASS_DEHUMIDIFIER
)

from . import API, COORDINATOR, UPDATED_DATA, JciHitachiEntity

_LOGGER = logging.getLogger(__name__)

MODE_AUTO = "Auto"
MODE_CUSTOM = "Custom"
MODE_CONTINUOUS = "Continuous"
MODE_CLOTHES_DRY = "Clothes Dry"
MODE_AIR_PURIFY = "Air Purify"
MODE_MOLD_PREV = "Mold Prev"
MODE_LOW_HUMIDITY = "Low Humidity"
MODE_ECO_COMFORT = "Eco Comfort"

AVAILABLE_MODES = [
    MODE_AUTO,
    MODE_CUSTOM,
    MODE_CONTINUOUS,
    MODE_CLOTHES_DRY,
    MODE_AIR_PURIFY,
    MODE_MOLD_PREV,
    MODE_LOW_HUMIDITY,
    MODE_ECO_COMFORT
]


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the humidifier platform."""

    api = hass.data[API]
    coordinator = hass.data[COORDINATOR]

    for peripheral in api.peripherals.values():
        if peripheral.type == "DH":
            status = hass.data[UPDATED_DATA][peripheral.name]
            supported_features = JciHitachiDehumidifierEntity.calculate_supported_features(
                status
            )
            async_add_entities(
                [JciHitachiDehumidifierEntity(
                    peripheral, coordinator, supported_features)],
                update_before_add=True
            )


class JciHitachiDehumidifierEntity(JciHitachiEntity, HumidifierEntity):
    def __init__(self, peripheral, coordinator, supported_features):
        super().__init__(peripheral, coordinator)
        self._supported_features = supported_features
    
    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._supported_features
    
    @property
    def target_humidity(self):
        """Return the current temperature."""
        status = self.hass.data[UPDATED_DATA][self._peripheral.name]
        if status:
            return status.target_humidity
        return None
    
    @property
    def max_humidity(self):
        """Return the maximum humidity."""
        status = self.hass.data[UPDATED_DATA][self._peripheral.name]
        return status.max_humidity
    
    @property
    def min_humidity(self):
        """Return the minimum humidity."""
        status = self.hass.data[UPDATED_DATA][self._peripheral.name]
        return status.min_humidity
    
    @property
    def mode(self):
        status = self.hass.data[UPDATED_DATA][self._peripheral.name]
        if status:
            if status.mode == "auto":
                return MODE_AUTO
            elif status.mode == "custom":
                return MODE_CUSTOM
            elif status.mode == "continuous":
                return MODE_CONTINUOUS
            elif status.mode == "clothes_dry":
                return MODE_CLOTHES_DRY
            elif status.mode == "air_purify":
                return MODE_AIR_PURIFY
            elif status.mode == "mold_prev":
                return MODE_MOLD_PREV
            elif status.mode == "low_humidity":
                return MODE_LOW_HUMIDITY
            elif status.mode == "eco_comfort":
                return MODE_ECO_COMFORT

        _LOGGER.error("Missing mode.")
        return None

    @property
    def available_modes(self):
        return AVAILABLE_MODES

    @property
    def is_on(self):
        status = self.hass.data[UPDATED_DATA][self._peripheral.name]
        if status:
            if status.power == "off":
                return False
            elif status.power == "on":
                return True
        
        _LOGGER.error("Missing is_on.")
        return None
    
    @property
    def device_class(self):
        return DEVICE_CLASS_DEHUMIDIFIER
    
    @property
    def unique_id(self):
        return f"{self._peripheral.gateway_mac_address}_dehumidifier"

    @staticmethod
    def calculate_supported_features(status):
        support_flags = SUPPORT_MODES
        return support_flags

    def set_mode(self, mode):
        """Set new target preset mode."""

        _LOGGER.debug(f"Set {self.name} mode to {mode}")

        if mode == MODE_AUTO:
            self.put_queue("mode", 0, self._peripheral.name)
        elif mode == MODE_CUSTOM:
            self.put_queue("mode", 1, self._peripheral.name)
        elif mode == MODE_CONTINUOUS:
            self.put_queue("mode", 2, self._peripheral.name)
        elif mode == MODE_CLOTHES_DRY:
            self.put_queue("mode", 3, self._peripheral.name)
        elif mode == MODE_AIR_PURIFY:
            self.put_queue("mode", 4, self._peripheral.name)
        elif mode == MODE_MOLD_PREV:
            self.put_queue("mode", 5, self._peripheral.name)
        elif mode == MODE_LOW_HUMIDITY:
            self.put_queue("mode", 8, self._peripheral.name)
        elif mode == MODE_ECO_COMFORT:
            self.put_queue("mode", 9, self._peripheral.name)
        else:
            _LOGGER.error("Invalid mode.")
        self.update()
    
    def set_humidity(self, humidity):
        """Set new target humidity."""

        target_humidity = int(humidity)
        _LOGGER.debug(f"Set {self.name} humidity to {target_humidity}")

        self.put_queue("target_humidity", target_humidity, self._peripheral.name)
        self.update()
    
    def turn_on(self, **kwargs):
        """Turn the device on."""
        self.put_queue("power", 1, self._peripheral.name)
        self.update()
    
    def turn_off(self, **kwargs):
        """Turn the device off."""
        self.put_queue("power", 0, self._peripheral.name)
        self.update()

    
