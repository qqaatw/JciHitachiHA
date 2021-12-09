"""JciHitachi integration."""
import logging

from homeassistant.components.switch import SwitchEntity

from . import API, COORDINATOR, UPDATED_DATA, JciHitachiEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the switch platform."""

    api = hass.data[API]
    coordinator = hass.data[COORDINATOR]

    for peripheral in api.peripherals.values():
        if peripheral.type == "DH":
            async_add_entities(
                [JciHitachiAirCleaningFilterEntity(peripheral, coordinator),
                 JciHitachiCleanFilterNotifySwitchEntity(peripheral, coordinator),
                 JciHitachiMoldPrevSwitchEntity(peripheral, coordinator),
                 JciHitachiWindSwingableSwitchEntity(peripheral, coordinator)],
                update_before_add=True)


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the switch platform from a config entry."""

    api = hass.data[API]
    coordinator = hass.data[COORDINATOR]

    for peripheral in api.peripherals.values():
        if peripheral.type == "DH":
            async_add_devices(
                [JciHitachiAirCleaningFilterEntity(peripheral, coordinator),
                 JciHitachiCleanFilterNotifySwitchEntity(peripheral, coordinator),
                 JciHitachiMoldPrevSwitchEntity(peripheral, coordinator),
                 JciHitachiWindSwingableSwitchEntity(peripheral, coordinator)],
                update_before_add=True)


class JciHitachiAirCleaningFilterEntity(JciHitachiEntity, SwitchEntity):
    def __init__(self, peripheral, coordinator):
        super().__init__(peripheral, coordinator)

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._peripheral.name} Air Cleaning Filter Setting"

    @property
    def is_on(self):
        """Indicate whether air cleaning filter setting is on."""
        status = self.hass.data[UPDATED_DATA].get(self._peripheral.name, None)
        if status:
            if status.air_cleaning_filter == "disabled":
                return False
            else:
                return True
        return None

    @property
    def unique_id(self):
        return f"{self._peripheral.gateway_mac_address}_air_cleaning_filter_switch"

    def turn_on(self):
        """Turn air cleaning filter setting on."""
        _LOGGER.debug(f"Turn {self.name} on")
        self.put_queue("air_cleaning_filter", 1, self._peripheral.name)
        self.update()

    def turn_off(self):
        """Turn air cleaning filter setting off."""
        _LOGGER.debug(f"Turn {self.name} off")
        self.put_queue("air_cleaning_filter", 0, self._peripheral.name)
        self.update()


class JciHitachiCleanFilterNotifySwitchEntity(JciHitachiEntity, SwitchEntity):
    def __init__(self, peripheral, coordinator):
        super().__init__(peripheral, coordinator)

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._peripheral.name} Clean Filter Notification"

    @property
    def is_on(self):
        """Indicate whether clean filter notification is on."""
        status = self.hass.data[UPDATED_DATA].get(self._peripheral.name, None)
        if status:
            if status.clean_filter_notify == "disabled":
                return False
            else:
                return True
        return None

    @property
    def unique_id(self):
        return f"{self._peripheral.gateway_mac_address}_clean_filter_notify_switch"

    def turn_on(self):
        """Turn clean filter notification on."""
        _LOGGER.debug(f"Turn {self.name} on")
        self.put_queue("clean_filter_notify", 1, self._peripheral.name)
        self.update()

    def turn_off(self):
        """Turn clean filter notification off."""
        _LOGGER.debug(f"Turn {self.name} off")
        self.put_queue("clean_filter_notify", 0, self._peripheral.name)
        self.update()


class JciHitachiMoldPrevSwitchEntity(JciHitachiEntity, SwitchEntity):
    def __init__(self, peripheral, coordinator):
        super().__init__(peripheral, coordinator)

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._peripheral.name} Mold Prevention"

    @property
    def is_on(self):
        """Indicate whether mold prevention is on."""
        status = self.hass.data[UPDATED_DATA].get(self._peripheral.name, None)
        if status:
            if status.mold_prev == "off":
                return False
            else:
                return True
        return None

    @property
    def unique_id(self):
        return f"{self._peripheral.gateway_mac_address}_mold_prev_switch"

    def turn_on(self):
        """Turn mold prevention on."""
        _LOGGER.debug(f"Turn {self.name} on")
        self.put_queue("mold_prev", 1, self._peripheral.name)
        self.update()

    def turn_off(self):
        """Turn mold prevention off."""
        _LOGGER.debug(f"Turn {self.name} off")
        self.put_queue("mold_prev", 0, self._peripheral.name)
        self.update()


class JciHitachiWindSwingableSwitchEntity(JciHitachiEntity, SwitchEntity):
    def __init__(self, peripheral, coordinator):
        super().__init__(peripheral, coordinator)

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._peripheral.name} Wind Swingable"

    @property
    def is_on(self):
        """Indicate whether wind swingable is on."""
        status = self.hass.data[UPDATED_DATA].get(self._peripheral.name, None)
        if status:
            if status.wind_swingable == "off":
                return False
            else:
                return True
        return None

    @property
    def unique_id(self):
        return f"{self._peripheral.gateway_mac_address}_wind_swingable_switch"

    def turn_on(self):
        """Turn wind swingable on."""
        _LOGGER.debug(f"Turn {self.name} on")
        self.put_queue("wind_swingable", 1, self._peripheral.name)
        self.update()
    
    def turn_off(self):
        """Turn wind swingable off."""
        _LOGGER.debug(f"Turn {self.name} off")
        self.put_queue("wind_swingable", 0, self._peripheral.name)
        self.update()
