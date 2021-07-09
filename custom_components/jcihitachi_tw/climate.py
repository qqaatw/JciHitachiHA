"""JciHitachi integration."""
import logging
import asyncio
import async_timeout
from datetime import timedelta

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    FAN_AUTO,
    FAN_DIFFUSE,
    FAN_FOCUS,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
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
    SUPPORT_PRESET_MODE
)
from homeassistant.const import ATTR_TEMPERATURE, TEMP_CELSIUS
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from . import API, UPDATED_DATA, UPDATE_DATA, JciHitachiEntity

_LOGGER = logging.getLogger(__name__)

PRESET_MOLD_PREVENTION = "Mold Prev"
PRESET_ECO_MOLD_PREVENTION = "Eco & Mold Prev"

SUPPORT_FAN = [FAN_AUTO, FAN_LOW, FAN_MEDIUM, FAN_HIGH]
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
SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE | SUPPORT_PRESET_MODE


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the climate platform."""

    api = hass.data[API]

    async def async_update_data():
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(10):
                data_updated = False
                while hass.data[UPDATE_DATA].qsize() > 0:
                    data_updated = True
                    update_data = hass.data[UPDATE_DATA].get()
                    _LOGGER.debug(f"Updating data: {update_data}")
                    result = await hass.async_add_executor_job(api.set_status, update_data.command, update_data.value, update_data.device_name)
                    _LOGGER.debug("Data updated successfully.")

                if data_updated:
                    asyncio.sleep(0.5)

                await hass.async_add_executor_job(api.refresh_status)
                _LOGGER.debug(
                    f"Peripheral info: {[peripheral for peripheral in api._peripherals.values()]}")
                
                hass.data[UPDATED_DATA] = api.get_status()
                return hass.data[UPDATED_DATA]

        except Exception as err:
            _LOGGER.error(f"Error communicating with API: {err}")
            raise UpdateFailed(f"Error communicating with API: {err}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        # Name of the data. For logging purposes.
        name="climate",
        update_method=async_update_data,
        # Polling interval. Will only be polled if there are subscribers.
        update_interval=timedelta(seconds=30),
    )

    await coordinator.async_refresh()

    for peripheral in api.peripherals.values():
        if peripheral.type == "AC":
            async_add_entities(
                [JciHitachiClimateEntity(peripheral, coordinator)]
            )


class JciHitachiClimateEntity(ClimateEntity, JciHitachiEntity):
    def __init__(self, peripheral, coordinator):
        super().__init__(
            peripheral=peripheral,
            coordinator=coordinator
        )

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        status = self.coordinator.data[self._peripheral.name]
        if status:
            return status.indoor_temp
        return None

    @property
    def target_temperature(self):
        """Return the target temperature."""
        status = self.coordinator.data[self._peripheral.name]
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
        status = self.coordinator.data[self._peripheral.name]
        return status.max_temp
    
    @property
    def min_temp(self):
        """Return the minimum temperature."""
        status = self.coordinator.data[self._peripheral.name]
        return status.min_temp

    @property
    def hvac_mode(self):
        status = self.coordinator.data[self._peripheral.name]
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
        status = self.coordinator.data[self._peripheral.name]
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
        status = self.coordinator.data[self._peripheral.name]
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
    def unique_id(self):
        return f"{self._peripheral.gateway_mac_address}_climate"
   
    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""

        _LOGGER.debug(f"Set {self.name} hvac_mode to {hvac_mode}")

        status = self.coordinator.data[self._peripheral.name]
        if status.power == "off" and hvac_mode != HVAC_MODE_OFF:
            await self.put_queue("power", 1, self._peripheral.name)

        if hvac_mode == HVAC_MODE_OFF:
            await self.put_queue("power", 0, self._peripheral.name)
        elif hvac_mode == HVAC_MODE_COOL:
            await self.put_queue("mode", 0, self._peripheral.name)
        elif hvac_mode == HVAC_MODE_DRY:
            await self.put_queue("mode", 1, self._peripheral.name)
        elif hvac_mode == HVAC_MODE_FAN_ONLY:
            await self.put_queue("mode", 2, self._peripheral.name)
        elif hvac_mode == HVAC_MODE_AUTO:
            await self.put_queue("mode", 3, self._peripheral.name)
        elif hvac_mode == HVAC_MODE_HEAT:
            await self.put_queue("mode", 4, self._peripheral.name)
        else:
            _LOGGER.error("Invalid hvac_mode.")

        ret = await self.async_update()

        if not ret:
            _LOGGER.error("Setting hvac_mode failed.")

    async def async_set_preset_mode(self, preset_mode):
        """Set new target preset mode."""

        _LOGGER.debug(f"Set {self.name} preset_mode to {preset_mode}")
        
        if preset_mode == PRESET_ECO_MOLD_PREVENTION:
            await self.put_queue("energy_save", 1, self._peripheral.name)
            await self.put_queue("mold_prev", 1, self._peripheral.name)
            await self.put_queue("fast_op", 0, self._peripheral.name)
        elif preset_mode == PRESET_ECO:
            await self.put_queue("energy_save", 1, self._peripheral.name)
            await self.put_queue("mold_prev", 0, self._peripheral.name)
            await self.put_queue("fast_op", 0, self._peripheral.name)
        elif preset_mode == PRESET_MOLD_PREVENTION:
            await self.put_queue("energy_save", 0, self._peripheral.name)
            await self.put_queue("mold_prev", 1, self._peripheral.name)
            await self.put_queue("fast_op", 0, self._peripheral.name)
        elif preset_mode == PRESET_BOOST:
            await self.put_queue("energy_save", 0, self._peripheral.name)
            await self.put_queue("mold_prev", 0, self._peripheral.name)
            await self.put_queue("fast_op", 1, self._peripheral.name)
        elif preset_mode == PRESET_NONE:
            await self.put_queue("energy_save", 0, self._peripheral.name)
            await self.put_queue("mold_prev", 0, self._peripheral.name)
            await self.put_queue("fast_op", 0, self._peripheral.name)
        else:
            _LOGGER.error("Invalid preset_mode.")

        ret = await self.async_update()

        if not ret:
            _LOGGER.error("Setting preset_mode failed.")

    async def async_set_fan_mode(self, fan_mode):
        """Set new target fan mode."""

        _LOGGER.debug(f"Set {self.name} fan_mode to {fan_mode}")

        if fan_mode == FAN_AUTO:
            await self.put_queue("air_speed", 0, self._peripheral.name)
        elif fan_mode == FAN_LOW:
            await self.put_queue("air_speed", 1, self._peripheral.name)
        elif fan_mode == FAN_MEDIUM:
            await self.put_queue("air_speed", 3, self._peripheral.name)
        elif fan_mode == FAN_HIGH:
            await self.put_queue("air_speed", 4, self._peripheral.name)
        else:
            _LOGGER.error("Invalid fan_mode.")

        ret = await self.async_update()

        if not ret:
            _LOGGER.error("Setting fan_mode failed.")

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        target_temp = kwargs.get(ATTR_TEMPERATURE)
        if target_temp is None:
            _LOGGER.error("Missing target temperature %s", kwargs)
            return

        target_temp = int(target_temp)
        _LOGGER.debug("Set %s temperature %s", self.name, target_temp)
        # Limit the target temperature into acceptable range.
        target_temp = min(self.max_temp, target_temp)
        target_temp = max(self.min_temp, target_temp)
        await self.put_queue("target_temp", target_temp, self._peripheral.name)

        ret = await self.async_update()

        if not ret:
            _LOGGER.error("Setting temperature failed.")
