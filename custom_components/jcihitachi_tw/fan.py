"""JciHitachi integration."""
import logging

from homeassistant.components.fan import (FanEntity, FanEntityFeature)
from homeassistant.util.percentage import (ordered_list_item_to_percentage,
                                           percentage_to_ordered_list_item)

from . import API, COORDINATOR, DOMAIN, UPDATED_DATA, JciHitachiEntity

_LOGGER = logging.getLogger(__name__)

ORDERED_NAMED_FAN_SPEEDS = [
    "auto",
    "silent",
    "low",
    "moderate",
    "high",
]
DEHUMIDIFIER_PRESET_MODES = [
    "auto"
]
HEAT_EXCHANGER_PRESET_MODES = [
    "auto",
    "energy_recovery",
    "normal",
]

async def _async_setup(hass, async_add):
    api = hass.data[DOMAIN][API]
    coordinator = hass.data[DOMAIN][COORDINATOR]

    for thing in api.things.values():
        if thing.type == "DH":
            async_add([JciHitachiDehumidifierFanEntity(thing, coordinator)], update_before_add=True)
        elif thing.type == "HE":
            async_add([JciHitachiHeatExchangerFanEntity(thing, coordinator)], update_before_add=True)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the fan platform."""
    await _async_setup(hass, async_add_entities)

async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the fan platform from a config entry."""
    await _async_setup(hass, async_add_devices)


class JciHitachiDehumidifierFanEntity(JciHitachiEntity, FanEntity):
    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)
        self._supported_features = self.calculate_supported_features()
        self._supported_fan_speeds = self.calculate_supported_fan_speeds()

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
        status = self.hass.data[DOMAIN][UPDATED_DATA][self._thing.name]
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
        status = self.hass.data[DOMAIN][UPDATED_DATA][self._thing.name]
        return ordered_list_item_to_percentage(self._supported_fan_speeds, status.air_speed)
    
    @property
    def speed_count(self):
        """Return the number of speeds the fan supports."""
        return len(self._supported_fan_speeds)

    @property
    def preset_mode(self):
        status = self.hass.data[DOMAIN][UPDATED_DATA][self._thing.name]
        if status:
            if status.air_speed == "auto":
                return "auto"
            return None
        
        _LOGGER.error("Missing preset_mode.")
        return None

    @property
    def preset_modes(self):
        return DEHUMIDIFIER_PRESET_MODES

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_dehumidifier_air_speed"

    def calculate_supported_features(self):
        support_flags = 0
        if self._thing.support_code.FanSpeed != "unsupported":
            support_flags |= FanEntityFeature.SET_SPEED
        if self._thing.support_code.FanSpeed & 1 == 1:  # auto mode is at the first bit.
            support_flags |= FanEntityFeature.PRESET_MODE

        return support_flags
    
    def calculate_supported_fan_speeds(self):
        support_fan_speeds = []
        if self._thing.support_code.FanSpeed != "unsupported":
            support_fan_speeds = [fan_speed for i, fan_speed in enumerate(ORDERED_NAMED_FAN_SPEEDS) if 2 ** i & self._thing.support_code.FanSpeed != 0]
    
        return support_fan_speeds
    
    def set_percentage(self, percentage):
        """Set the speed percentage of the fan."""
        air_speed = percentage_to_ordered_list_item(
            self._supported_fan_speeds,
            percentage
        )
        
        _LOGGER.debug(f"Set {self.name} air speed to {air_speed}")

        if air_speed == "silent":
            self.put_queue(status_name="air_speed", status_str_value="silent")
        elif air_speed == "low":
            self.put_queue(status_name="air_speed", status_str_value="low")
        elif air_speed == "moderate":
            self.put_queue(status_name="air_speed", status_str_value="moderate")
        elif air_speed == "high":
            self.put_queue(status_name="air_speed", status_str_value="high")
        else:
            _LOGGER.error("Invalid air_speed.")
        
        self.update()
    
    def set_preset_mode(self, preset_mode):
        """Set the preset mode of the fan."""
        _LOGGER.debug(f"Set {self.name} preset mode to {preset_mode}")
        self.put_queue(status_name="air_speed", status_str_value="auto")
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


class JciHitachiHeatExchangerFanEntity(JciHitachiEntity, FanEntity):
    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)
        self._supported_features = self.calculate_supported_features()
        self._supported_fan_speeds = self.calculate_supported_fan_speeds()
        self._supported_presets = self.calculate_supported_presets()

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
        status = self.hass.data[DOMAIN][UPDATED_DATA][self._thing.name]
        if status:
            if status.Switch == "off":
                return False
            elif status.Switch == "on":
                return True

        _LOGGER.error("Missing is_on.")
        return None
    
    @property
    def percentage(self):
        """Return the current speed percentage."""
        status = self.hass.data[DOMAIN][UPDATED_DATA][self._thing.name]
        return ordered_list_item_to_percentage(self._supported_fan_speeds, status.FanSpeed)
    
    @property
    def speed_count(self):
        """Return the number of speeds the fan supports."""
        return len(self._supported_fan_speeds)

    @property
    def preset_mode(self):
        status = self.hass.data[DOMAIN][UPDATED_DATA][self._thing.name]
        if status:
            return status.BreathMode
        _LOGGER.error("Missing preset_mode.")
        return None

    @property
    def preset_modes(self):
        return self._supported_presets

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_heat_exchanger_fan"

    def calculate_supported_features(self):
        support_flags = 0
        if self._thing.support_code.FanSpeed != "unsupported":
            support_flags |= SUPPORT_SET_SPEED
        if self._thing.support_code.BreathMode != "unsupported":
            support_flags |= SUPPORT_PRESET_MODE

        return support_flags
    
    def calculate_supported_fan_speeds(self):
        support_fan_speeds = []
        if self._thing.support_code.FanSpeed != "unsupported":
            support_fan_speeds = [fan_speed for i, fan_speed in enumerate(ORDERED_NAMED_FAN_SPEEDS) if 2 ** i & self._thing.support_code.FanSpeed != 0]
    
        return support_fan_speeds
    
    def calculate_supported_presets(self):
        support_presets = []
        if self._thing.support_code.BreathMode != "unsupported":
            support_presets = [preset for i, preset in enumerate(HEAT_EXCHANGER_PRESET_MODES) if 2 ** i & self._thing.support_code.BreathMode != 0]
        
        return support_presets

    def set_percentage(self, percentage):
        """Set the speed percentage of the fan."""
        fan_speed = percentage_to_ordered_list_item(
            ORDERED_NAMED_FAN_SPEEDS, percentage)
        
        _LOGGER.debug(f"Set {self.name} air speed to {fan_speed}")

        if fan_speed == "silent":
            self.put_queue(status_name="FanSpeed", status_str_value="silent")
        elif fan_speed == "low":
            self.put_queue(status_name="FanSpeed", status_str_value="low")
        elif fan_speed == "moderate":
            self.put_queue(status_name="FanSpeed", status_str_value="moderate")
        elif fan_speed == "high":
            self.put_queue(status_name="FanSpeed", status_str_value="high")
        else:
            _LOGGER.error("Invalid FanSpeed.")
        
        self.update()
    
    def set_preset_mode(self, preset_mode):
        """Set the preset mode of the fan."""
        _LOGGER.debug(f"Set {self.name} preset mode to {preset_mode}")
        self.put_queue(status_name="BreathMode", status_str_value=preset_mode)
        self.update()

    def turn_on(self, **kwargs):
        """Turn the device on."""
        _LOGGER.debug(f"Turn {self.name} on")
        self.put_queue(status_name="Switch", status_str_value="on")
        self.update()

    def turn_off(self, **kwargs):
        """Turn the device off."""
        _LOGGER.debug(f"Turn {self.name} off")
        self.put_queue(status_name="Switch", status_str_value="off")
        self.update()