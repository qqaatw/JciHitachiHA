"""Remember each device's last support code, for when the cloud stops answering it.

Why: after a restart the support-code request (registration/response) of a unit can answer a
non-JSON payload on every poll for tens of minutes to hours, while its status answers normally.
The climate / humidifier entity needs the support code (modes, fan speeds, temperature range), so
without it the controls did not exist all that time. On 2026-09-17 a unit in that state still
carried out power, mode, fan speed and temperature commands within 9 s (LibJciHitachi contract
profile ac-rad-fw6.0.032). The support code describes the model: one unit's answers on
2026-09-16 and 2026-09-17 differed only in their timestamps.

So the raw support-code JSON of each device is kept in `.storage/jcihitachi_tw.support_codes`
(keyed by gateway MAC, without WiFiSSID) and used when the device does not answer at setup.
Such devices keep being asked on every poll; the saved copy is replaced as soon as they answer.
A device that never answered gets no saved copy and no control entity.
"""
from __future__ import annotations

import logging

from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util
from JciHitachi.model import JciHitachiAWSStatusSupport

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STORE_VERSION = 1
STORE_KEY = f"{DOMAIN}.support_codes"
# fields that change on every answer without changing what the device can do
VOLATILE_KEYS = {"Timestamp", "RequestTimestamp", "SystemTimestamp", "ReceiveTimestamp", "WiFiSSID"}


class SupportCodeCache:
    def __init__(self, hass) -> None:
        self._store = Store(hass, STORE_VERSION, STORE_KEY)
        self._data: dict[str, dict] = {}  # gateway MAC -> {"saved_at", "support"}
        self._in_use: dict[str, dict] = {}  # device name -> {"saved_at", "support" (object)}
        self._saved: dict[str, object] = {}  # device name -> support object last written

    async def async_load(self, api) -> None:
        """Give devices whose support code was not read at login their saved one, if any."""
        self._data = await self._store.async_load() or {}
        for name, thing in api.things.items():
            entry = self._data.get(thing.gateway_mac_address)
            if thing.support_code is not None or entry is None:
                continue
            support = JciHitachiAWSStatusSupport(entry["support"])
            thing.support_code = support
            self._in_use[name] = {"saved_at": entry["saved_at"], "support": support}
            _LOGGER.warning(
                f"{name} did not answer its support code; using the one saved at {entry['saved_at']}."
            )
        await self.async_save_new(api)

    def uses_saved(self, name: str, thing) -> bool:
        entry = self._in_use.get(name)
        return entry is not None and thing.support_code is entry["support"]

    def saved_at(self, name: str, thing) -> str | None:
        """Local "YYYY-MM-DD HH:MM" of the saved support code in use, or None."""
        if not self.uses_saved(name, thing):
            return None
        moment = dt_util.parse_datetime(self._in_use[name]["saved_at"])
        return dt_util.as_local(moment).strftime("%Y-%m-%d %H:%M") if moment else None

    def release(self, name: str, thing) -> bool:
        """The device answered its support code again. True when its entities must be rebuilt.

        Rebuild when it had no saved copy (its entities were never created) or when what it can
        do differs from the saved copy.
        """
        entry = self._in_use.pop(name, None)
        if entry is None:
            return True
        old = {k: v for k, v in entry["support"]._raw_status.items() if k not in VOLATILE_KEYS}
        new = {k: v for k, v in thing.support_code._raw_status.items() if k not in VOLATILE_KEYS}
        return old != new

    async def async_save_new(self, api) -> None:
        """Write every support code read from the cloud since the last save."""
        changed = False
        for name, thing in api.things.items():
            support = thing.support_code
            if support is None or self._saved.get(name) is support or self.uses_saved(name, thing):
                continue
            raw = getattr(support, "_raw_status", None)
            if not isinstance(raw, dict):
                continue
            self._data[thing.gateway_mac_address] = {
                "saved_at": dt_util.now().isoformat(timespec="seconds"),
                "support": {k: v for k, v in raw.items() if k != "WiFiSSID"},
            }
            self._saved[name] = support
            changed = True
        if changed:
            await self._store.async_save(self._data)
