import logging
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    SUPPORT_BRIGHTNESS,
    LightEntity,
)

from . import API, COORDINATOR, DOMAIN, UPDATED_DATA, JciHitachiEntity

_LOGGER = logging.getLogger(__name__)


async def _async_setup(hass, async_add):
    api = hass.data[DOMAIN][API]
    coordinator = hass.data[DOMAIN][COORDINATOR]

    for thing in api.things.values():
        if thing.type == "DH":
            async_add(
                [JciHitachiDehumidifierLightEntity(thing, coordinator)],
                update_before_add=True,
            )


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    await _async_setup(hass, async_add_entities)


async def async_setup_entry(hass, config_entry, async_add_devices):
    await _async_setup(hass, async_add_devices)


class JciHitachiDehumidifierLightEntity(JciHitachiEntity, LightEntity):
    brightness_mapping = {
        "bright": 255,
        "dark": 170,
        "off": 85,
        "all_off": 0,
    }

    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_dehumidifier_light"

    @property
    def name(self):
        return f"{self._thing.name} panel LED"

    @property
    def supported_features(self):
        return SUPPORT_BRIGHTNESS

    @property
    def is_on(self):
        """Return true if the entity is on"""
        status = self.hass.data[DOMAIN][UPDATED_DATA][self._thing.name]
        if status:
            if status.display_brightness == "all_off":
                return False
            else:
                return True

        _LOGGER.error("Missing is_on.")
        return None

    @property
    def brightness(self):
        status = self.hass.data[DOMAIN][UPDATED_DATA][self._thing.name]
        if status:
            return self.brightness_mapping.get(status.display_brightness, 0)

        _LOGGER.error("Missing brightness.")
        return 0

    def turn_on(self, **kwargs):
        _LOGGER.debug(f"Turn {self.name} on")
        brightness = kwargs.get(ATTR_BRIGHTNESS, 255)
        if brightness > 170:
            brightness_value = "bright"
        elif brightness <= 170 and brightness > 85:
            brightness_value = "dark"
        elif brightness <= 85 and brightness > 3:
            brightness_value = "off"
        else:
            brightness_value = "all_off"
        self.put_queue(
            status_name="display_brightness", status_str_value=brightness_value
        )
        self.update()

    def turn_off(self, **kwargs):
        _LOGGER.debug(f"Turn {self.name} off")
        self.put_queue(status_name="display_brightness", status_str_value="all_off")
        self.update()
