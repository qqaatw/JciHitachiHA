"""JciHitachi integration."""
import logging

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    FAN_AUTO,
    FAN_DIFFUSE,
    FAN_FOCUS,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    SWING_OFF,
    SWING_VERTICAL,
    SWING_HORIZONTAL,
    SWING_BOTH,
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    PRESET_NONE,
    PRESET_BOOST,
    PRESET_ECO,
    SUPPORT_FAN_MODE,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_PRESET_MODE,
    SUPPORT_SWING_MODE
)
from homeassistant.const import ATTR_TEMPERATURE, TEMP_CELSIUS

from . import API, COORDINATOR, UPDATED_DATA, JciHitachiEntity

_LOGGER = logging.getLogger(__name__)

PRESET_MOLD_PREVENTION = "Mold Prev"
PRESET_ECO_MOLD_PREVENTION = "Eco & Mold Prev"

SUPPORT_FAN = [FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH]
SUPPORT_SWING = [
    SWING_OFF,
    SWING_VERTICAL,
    SWING_HORIZONTAL,
    SWING_BOTH
]
SUPPORT_HVAC = [
    HVAC_MODE_OFF,
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_AUTO,
    HVAC_MODE_HEAT,
]
SUPPORT_PRESET = [
    PRESET_NONE,
    PRESET_BOOST,
    PRESET_ECO,
    PRESET_MOLD_PREVENTION,
    PRESET_ECO_MOLD_PREVENTION
]


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the climate platform."""

    api = hass.data[API]
    coordinator = hass.data[COORDINATOR]

    for peripheral in api.peripherals.values():
        if peripheral.type == "AC":
            status = hass.data[UPDATED_DATA][peripheral.name]
            support_features = JciHitachiClimateEntity.calculate_supported_features(status)
            async_add_entities(
                [JciHitachiClimateEntity(
                    peripheral, coordinator, support_features)],
                update_before_add=True
            )


class JciHitachiClimateEntity(JciHitachiEntity, ClimateEntity):
    def __init__(self, peripheral, coordinator, supported_features):
        super().__init__(peripheral, coordinator)
        self._supported_features = supported_features

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._supported_features

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        status = self.hass.data[UPDATED_DATA][self._peripheral.name]
        if status:
            return status.indoor_temp
        return None

    @property
    def target_temperature(self):
        """Return the target temperature."""
        status = self.hass.data[UPDATED_DATA][self._peripheral.name]
        if status:
            return status.target_temp
        return None

    @property
    def target_temperature_step(self):
        """Return the target temperature step."""
        return 1.0

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        status = self.hass.data[UPDATED_DATA][self._peripheral.name]
        return status.max_temp
    
    @property
    def min_temp(self):
        """Return the minimum temperature."""
        status = self.hass.data[UPDATED_DATA][self._peripheral.name]
        return status.min_temp

    @property
    def hvac_mode(self):
        status = self.hass.data[UPDATED_DATA][self._peripheral.name]
        if status:
            if status.power == "off":
                return HVAC_MODE_OFF
            elif status.mode == "cool":
                return HVAC_MODE_COOL
            elif status.mode == "dry":
                return HVAC_MODE_DRY
            elif status.mode == "fan":
                return HVAC_MODE_FAN_ONLY
            elif status.mode == "auto":
                return HVAC_MODE_AUTO
            elif status.mode == "heat":
                return HVAC_MODE_HEAT

        _LOGGER.error("Missing hvac_mode")
        return None

    @property
    def hvac_modes(self):
        return SUPPORT_HVAC
    
    @property
    def preset_mode(self):
        status = self.hass.data[UPDATED_DATA][self._peripheral.name]
        if status:
            if status.energy_save == "enabled" and status.mold_prev == "enabled":
                return PRESET_ECO_MOLD_PREVENTION
            elif status.energy_save == "enabled":
                return PRESET_ECO
            elif status.mold_prev == "enabled":
                return PRESET_MOLD_PREVENTION
            elif status.fast_op == "enabled":
                return PRESET_BOOST
            else:
                return PRESET_NONE

        _LOGGER.error("Missing preset_mode")
        return None

    @property
    def preset_modes(self):
        return SUPPORT_PRESET

    @property
    def fan_mode(self):
        status = self.hass.data[UPDATED_DATA][self._peripheral.name]
        if status:
            if status.air_speed == "auto":
                return FAN_AUTO
            elif status.air_speed == "silent":
                return FAN_LOW
            elif status.air_speed == "low":
                return FAN_LOW
            elif status.air_speed == "moderate":
                return FAN_MEDIUM
            elif status.air_speed == "high":
                return FAN_HIGH
        _LOGGER.error("Missing fan_mode.")
        return None
    
    @property
    def fan_modes(self):
        return SUPPORT_FAN
    
    @property
    def swing_mode(self):
        status = self.hass.data[UPDATED_DATA][self._peripheral.name]
        if status:
            if status.vertical_wind_swingable == "enabled" and \
                status.horizontal_wind_direction == "auto":
                return SWING_BOTH
            elif status.vertical_wind_swingable == "enabled":
                return SWING_VERTICAL
            elif status.horizontal_wind_direction == "auto":
                return SWING_HORIZONTAL
            else:
                return SWING_OFF
        _LOGGER.error("Missing swing_mode.")
        return None

    @property
    def swing_modes(self):
        return SUPPORT_SWING

    @property
    def unique_id(self):
        return f"{self._peripheral.gateway_mac_address}_climate"

    @staticmethod
    def calculate_supported_features(status):
        support_flags = SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE | SUPPORT_PRESET_MODE
        if status.horizontal_wind_direction != "unsupported" and \
                status.vertical_wind_swingable != "unsupported":
            support_flags |= SUPPORT_SWING_MODE
        return support_flags

    def set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""

        _LOGGER.debug(f"Set {self.name} hvac_mode to {hvac_mode}")

        status = self.hass.data[UPDATED_DATA][self._peripheral.name]
        if status.power == "off" and hvac_mode != HVAC_MODE_OFF:
            self.put_queue("power", 1, self._peripheral.name)

        if hvac_mode == HVAC_MODE_OFF:
            self.put_queue("power", 0, self._peripheral.name)
        elif hvac_mode == HVAC_MODE_COOL:
            self.put_queue("mode", 0, self._peripheral.name)
        elif hvac_mode == HVAC_MODE_DRY:
            self.put_queue("mode", 1, self._peripheral.name)
        elif hvac_mode == HVAC_MODE_FAN_ONLY:
            self.put_queue("mode", 2, self._peripheral.name)
        elif hvac_mode == HVAC_MODE_AUTO:
            self.put_queue("mode", 3, self._peripheral.name)
        elif hvac_mode == HVAC_MODE_HEAT:
            self.put_queue("mode", 4, self._peripheral.name)
        else:
            _LOGGER.error("Invalid hvac_mode.")
        self.update()

    def set_preset_mode(self, preset_mode):
        """Set new target preset mode."""

        _LOGGER.debug(f"Set {self.name} preset_mode to {preset_mode}")
        
        if preset_mode == PRESET_ECO_MOLD_PREVENTION:
            self.put_queue("energy_save", 1, self._peripheral.name)
            self.put_queue("mold_prev", 1, self._peripheral.name)
            self.put_queue("fast_op", 0, self._peripheral.name)
        elif preset_mode == PRESET_ECO:
            self.put_queue("energy_save", 1, self._peripheral.name)
            self.put_queue("mold_prev", 0, self._peripheral.name)
            self.put_queue("fast_op", 0, self._peripheral.name)
        elif preset_mode == PRESET_MOLD_PREVENTION:
            self.put_queue("energy_save", 0, self._peripheral.name)
            self.put_queue("mold_prev", 1, self._peripheral.name)
            self.put_queue("fast_op", 0, self._peripheral.name)
        elif preset_mode == PRESET_BOOST:
            self.put_queue("energy_save", 0, self._peripheral.name)
            self.put_queue("mold_prev", 0, self._peripheral.name)
            self.put_queue("fast_op", 1, self._peripheral.name)
        elif preset_mode == PRESET_NONE:
            self.put_queue("energy_save", 0, self._peripheral.name)
            self.put_queue("mold_prev", 0, self._peripheral.name)
            self.put_queue("fast_op", 0, self._peripheral.name)
        else:
            _LOGGER.error("Invalid preset_mode.")
        self.update()

    def set_fan_mode(self, fan_mode):
        """Set new target fan mode."""

        _LOGGER.debug(f"Set {self.name} fan_mode to {fan_mode}")

        if fan_mode == FAN_AUTO:
            self.put_queue("air_speed", 0, self._peripheral.name)
        elif fan_mode == FAN_LOW:
            self.put_queue("air_speed", 1, self._peripheral.name)
        elif fan_mode == FAN_MEDIUM:
            self.put_queue("air_speed", 3, self._peripheral.name)
        elif fan_mode == FAN_HIGH:
            self.put_queue("air_speed", 4, self._peripheral.name)
        else:
            _LOGGER.error("Invalid fan_mode.")
        self.update()

    def set_swing_mode(self, swing_mode):
        """Set swing mode."""

        _LOGGER.debug(f"Set {self.name} swing_mode to {swing_mode}")

        if swing_mode == SWING_OFF:
            self.put_queue("vertical_wind_swingable", 0, self._peripheral.name)
            self.put_queue("horizontal_wind_direction", 3, self._peripheral.name)
        elif swing_mode == SWING_VERTICAL:
            self.put_queue("vertical_wind_swingable", 1, self._peripheral.name)
            self.put_queue("horizontal_wind_direction", 3, self._peripheral.name)
        elif swing_mode == SWING_HORIZONTAL:
            self.put_queue("vertical_wind_swingable", 0, self._peripheral.name)
            self.put_queue("horizontal_wind_direction", 0, self._peripheral.name)
        elif swing_mode == SWING_BOTH:
            self.put_queue("vertical_wind_swingable", 1, self._peripheral.name)
            self.put_queue("horizontal_wind_direction", 0, self._peripheral.name)
        else:
            _LOGGER.error("Invalid swing_mode.")
        self.update()

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        target_temp = kwargs.get(ATTR_TEMPERATURE)
        if target_temp is None:
            _LOGGER.error("Missing target temperature %s", kwargs)
            return

        target_temp = int(target_temp)
        _LOGGER.debug(f"Set {self.name} temperature to {target_temp}")
        # Limit the target temperature into acceptable range.
        target_temp = min(self.max_temp, target_temp)
        target_temp = max(self.min_temp, target_temp)
        self.put_queue("target_temp", target_temp, self._peripheral.name)
        self.update()
