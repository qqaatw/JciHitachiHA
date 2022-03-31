"""JciHitachi integration."""
import logging

from homeassistant.components.fan import SUPPORT_SET_SPEED, FanEntity
from homeassistant.util.percentage import (ordered_list_item_to_percentage,
                                           percentage_to_ordered_list_item)

from . import API, COORDINATOR, UPDATED_DATA, JciHitachiEntity

_LOGGER = logging.getLogger(__name__)

ORDERED_NAMED_FAN_SPEEDS = ["silent", "low", "moderate", "high"]


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the fan platform."""

    api = hass.data[API]
    coordinator = hass.data[COORDINATOR]

    for thing in api.things.values():
        if thing.type == "DH":
            status = hass.data[UPDATED_DATA][thing.name]
            supported_features = JciHitachiDehumidifierFanEntity.calculate_supported_features(
                status
            )
            async_add_entities(
                [JciHitachiDehumidifierFanEntity(
                    thing, coordinator, supported_features)],
                update_before_add=True)


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the fan platform from a config entry."""

    api = hass.data[API]
    coordinator = hass.data[COORDINATOR]

    for thing in api.things.values():
        if thing.type == "DH":
            status = hass.data[UPDATED_DATA][thing.name]
            supported_features = JciHitachiDehumidifierFanEntity.calculate_supported_features(
                status
            )
            async_add_devices(
                [JciHitachiDehumidifierFanEntity(
                    thing, coordinator, supported_features)],
                update_before_add=True)


class JciHitachiDehumidifierFanEntity(JciHitachiEntity, FanEntity):
    def __init__(self, thing, coordinator, supported_features):
        super().__init__(thing, coordinator)
        self._supported_features = supported_features

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._thing.name} Air Speed"

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._supported_features
    
    @property
    def is_on(self):
        """Return true if the entity is on"""
        status = self.hass.data[UPDATED_DATA][self._thing.name]
        if status:
            if status.power == "off":
                return False
            elif status.power == "on":
                return True

        _LOGGER.error("Missing is_on.")
        return None
    
    @property
    def percentage(self):
        """Return the current speed percentage."""
        status = self.hass.data[UPDATED_DATA][self._thing.name]
        return ordered_list_item_to_percentage(ORDERED_NAMED_FAN_SPEEDS, status.air_speed)
    
    @property
    def speed_count(self):
        """Return the number of speeds the fan supports."""
        return len(ORDERED_NAMED_FAN_SPEEDS)

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_dehumidifier_air_speed"

    @staticmethod
    def calculate_supported_features(status):
        support_flags = SUPPORT_SET_SPEED
        return support_flags
    
    def set_percentage(self, percentage):
        """Set the speed percentage of the fan."""
        air_speed = percentage_to_ordered_list_item(
            ORDERED_NAMED_FAN_SPEEDS, percentage)
        
        _LOGGER.debug(f"Set {self.name} air speed to {air_speed}")

        if air_speed == "silent":
            self.put_queue("air_speed", status_str_value="silent")
        elif air_speed == "low":
            self.put_queue("air_speed", status_str_value="low")
        elif air_speed == "moderate":
            self.put_queue("air_speed", status_str_value="moderate")
        elif air_speed == "high":
            self.put_queue("air_speed", status_str_value="high")
        else:
            _LOGGER.error("Invalid air_speed.")
        self.update()

    def turn_on(self, **kwargs):
        """Turn the device on."""
        _LOGGER.debug(f"Turn {self.name} on")
        self.put_queue("power", status_str_value="on")
        self.update()

    def turn_off(self, **kwargs):
        """Turn the device off."""
        _LOGGER.debug(f"Turn {self.name} off")
        self.put_queue("power", status_str_value="off")
        self.update()
