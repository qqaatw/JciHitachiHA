"""JciHitachi integration."""
import datetime
import logging

from homeassistant.components.switch import SwitchEntity

from . import API, COORDINATOR, DOMAIN, UPDATED_DATA, JciHitachiEntity

_LOGGER = logging.getLogger(__name__)


async def _async_setup(hass, async_add):
    api = hass.data[DOMAIN][API]
    coordinator = hass.data[DOMAIN][COORDINATOR]

    for thing in api.things.values():
        if thing.type == "AC":
            async_add([JciHitachiFreezeCleanSwitchEntity(thing, coordinator)],
                      update_before_add=True)
        elif thing.type == "DH":
            async_add(
                [JciHitachiAirCleaningFilterEntity(thing, coordinator),
                 JciHitachiCleanFilterNotifySwitchEntity(thing, coordinator),
                 JciHitachiMoldPrevSwitchEntity(thing, coordinator),
                 JciHitachiWindSwingableSwitchEntity(thing, coordinator),
                 JciHitachiIonSwitchEntity(thing, coordinator),
                 JciHitachiKeypadLockSwitchEntity(thing, coordinator)],
                update_before_add=True)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the switch platform."""
    await _async_setup(hass, async_add_entities)

async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the switch platform from a config entry."""
    await _async_setup(hass, async_add_devices)


class JciHitachiAirCleaningFilterEntity(JciHitachiEntity, SwitchEntity):
    _attr_translation_key = "air_cleaning_filter"

    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)

    @property
    def is_on(self):
        """Indicate whether air cleaning filter setting is on."""
        status = self.hass.data[DOMAIN][UPDATED_DATA].get(self._thing.name, None)
        if status:
            if status.air_cleaning_filter == "disabled":
                return False
            else:
                return True
        return None

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_air_cleaning_filter_switch"

    def turn_on(self):
        """Turn air cleaning filter setting on."""
        _LOGGER.debug(f"Turn {self.name} on")
        self.put_queue(status_name="air_cleaning_filter", status_str_value="enabled")
        self.update()

    def turn_off(self):
        """Turn air cleaning filter setting off."""
        _LOGGER.debug(f"Turn {self.name} off")
        self.put_queue(status_name="air_cleaning_filter", status_str_value="disabled")
        self.update()


class JciHitachiCleanFilterNotifySwitchEntity(JciHitachiEntity, SwitchEntity):
    _attr_translation_key = "clean_filter_notify"

    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)

    @property
    def is_on(self):
        """Indicate whether clean filter notification is on."""
        status = self.hass.data[DOMAIN][UPDATED_DATA].get(self._thing.name, None)
        if status:
            if status.clean_filter_notify == "disabled":
                return False
            else:
                return True
        return None

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_clean_filter_notify_switch"

    def turn_on(self):
        """Turn clean filter notification on."""
        _LOGGER.debug(f"Turn {self.name} on")
        self.put_queue(status_name="clean_filter_notify", status_str_value="enabled")
        self.update()

    def turn_off(self):
        """Turn clean filter notification off."""
        _LOGGER.debug(f"Turn {self.name} off")
        self.put_queue(status_name="clean_filter_notify", status_str_value="disabled")
        self.update()


class JciHitachiMoldPrevSwitchEntity(JciHitachiEntity, SwitchEntity):
    _attr_translation_key = "mold_prevention"

    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)

    @property
    def is_on(self):
        """Indicate whether mold prevention is on."""
        status = self.hass.data[DOMAIN][UPDATED_DATA].get(self._thing.name, None)
        if status:
            if status.mold_prev == "disabled":
                return False
            else:
                return True
        return None

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_mold_prev_switch"

    def turn_on(self):
        """Turn mold prevention on."""
        _LOGGER.debug(f"Turn {self.name} on")
        self.put_queue(status_name="mold_prev", status_str_value="enabled")
        self.update()

    def turn_off(self):
        """Turn mold prevention off."""
        _LOGGER.debug(f"Turn {self.name} off")
        self.put_queue(status_name="mold_prev", status_str_value="disabled")
        self.update()


class JciHitachiWindSwingableSwitchEntity(JciHitachiEntity, SwitchEntity):
    _attr_translation_key = "wind_swingable"

    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)

    @property
    def is_on(self):
        """Indicate whether wind swingable is on."""
        status = self.hass.data[DOMAIN][UPDATED_DATA].get(self._thing.name, None)
        if status:
            if status.wind_swingable == "disabled":
                return False
            else:
                return True
        return None

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_wind_swingable_switch"

    def turn_on(self):
        """Turn wind swingable on."""
        _LOGGER.debug(f"Turn {self.name} on")
        self.put_queue(status_name="wind_swingable", status_str_value="enabled")
        self.update()
    
    def turn_off(self):
        """Turn wind swingable off."""
        _LOGGER.debug(f"Turn {self.name} off")
        self.put_queue(status_name="wind_swingable", status_str_value="disabled")
        self.update()

class JciHitachiIonSwitchEntity(JciHitachiEntity, SwitchEntity):
    _attr_translation_key = "ion"

    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)

    @property
    def is_on(self):
        """Indicate whether ion is on."""
        status = self.hass.data[DOMAIN][UPDATED_DATA].get(self._thing.name, None)
        if status:
            if status.Ion == "disabled":
                return False
            else:
                return True
        return None

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_ion_switch"

    def turn_on(self):
        """Turn ion on."""
        _LOGGER.debug(f"Turn {self.name} on")
        self.put_queue(status_name="Ion", status_str_value="enabled")
        self.update()
    
    def turn_off(self):
        """Turn ion off."""
        _LOGGER.debug(f"Turn {self.name} off")
        self.put_queue(status_name="Ion", status_str_value="disabled")
        self.update()

class JciHitachiKeypadLockSwitchEntity(JciHitachiEntity, SwitchEntity):
    _attr_translation_key = "keypad_lock"

    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)

    @property
    def is_on(self):
        """Indicate whether keypad lock is on."""
        status = self.hass.data[DOMAIN][UPDATED_DATA].get(self._thing.name, None)
        if status:
            if status.KeypadLock == "disabled":
                return False
            else:
                return True
        return None

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_keypad_lock_switch"

    def turn_on(self):
        """Turn keypad lock on."""
        _LOGGER.debug(f"Turn {self.name} on")
        self.put_queue(status_name="KeypadLock", status_str_value="enabled")
        self.update()
    
    def turn_off(self):
        """Turn keypad lock off."""
        _LOGGER.debug(f"Turn {self.name} off")
        self.put_queue(status_name="KeypadLock", status_str_value="disabled")
        self.update()


class JciHitachiFreezeCleanSwitchEntity(JciHitachiEntity, SwitchEntity):
    """Freeze clean (凍結洗淨) of an air conditioner: backend status `CleanSwitch` (legacy `freeze_clean`).

    EXPERIMENTAL: verified on one device family only (LibJciHitachi contract profile
    ac-rad-fw6.0.032, 2026-09-17). There, on and off both worked, but a unit may ignore a start
    it cannot carry out, for example while another unit on the same outdoor unit is cleaning. The
    cloud still echoes CleanSwitch 1 with Error 0 then. The library caches that echo, so the switch
    shows on until the next poll reports the unit's own CleanSwitch (0); read from the code, not
    observed in Home Assistant. Every command keeps the cloud's raw answer
    in the `last_control_response` attribute (recorded by the recorder) so the behaviour can be
    checked afterwards. The support code of the tested RAD-series units reports CleanSwitch mask 3
    (on and off supported).
    """

    _attr_translation_key = "freeze_clean"
    _attr_icon = "mdi:snowflake-melt"

    def __init__(self, thing, coordinator):
        super().__init__(thing, coordinator)

    @property
    def is_on(self):
        """Current CleanSwitch from the latest status poll."""
        status = self.hass.data[DOMAIN][UPDATED_DATA].get(self._thing.name, None)
        if status:
            if status.freeze_clean == "on":
                return True
            if status.freeze_clean == "off":
                return False
        return None

    @property
    def extra_state_attributes(self):
        response = getattr(self._thing, "last_control_response", None)
        if isinstance(response, (bytes, bytearray)):
            response = f"not JSON, hex {bytes(response).hex()}"
        sent_at = getattr(self._thing, "last_control_at", None)
        return {
            "experimental": True,
            "last_control_request": getattr(self._thing, "last_control_request", None),
            "last_control_response": response,
            "last_control_at": (
                datetime.datetime.fromtimestamp(sent_at).isoformat(timespec="seconds")
                if sent_at
                else None
            ),
        }

    @property
    def unique_id(self):
        return f"{self._thing.gateway_mac_address}_freeze_clean_switch"

    def turn_on(self, **kwargs):
        """Start freeze clean."""
        _LOGGER.debug(f"Turn {self.name} on")
        self.put_queue(status_name="freeze_clean", status_str_value="on")
        self.update()

    def turn_off(self, **kwargs):
        """Stop freeze clean."""
        _LOGGER.debug(f"Turn {self.name} off")
        self.put_queue(status_name="freeze_clean", status_str_value="off")
        self.update()
