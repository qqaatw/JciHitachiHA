"""Offline PM2.5 contracts using real LibJciHitachi and minimal HA stubs.

These tests do not connect to devices or validate physical sensor accuracy.
"""
import asyncio
import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest

COMPONENT = Path(__file__).resolve().parents[1] / "custom_components" / "jcihitachi_tw"


@pytest.fixture
def modules(monkeypatch):
    """Load the actual sensor platform with isolated SDK mappings and HA stubs."""
    from JciHitachi.model import STATUS_DICT

    monkeypatch.setitem(STATUS_DICT, "AC", dict(STATUS_DICT["AC"]))
    package = ModuleType("offline_hitachi")
    package.__path__ = []
    for key in ("API", "COORDINATOR", "DOMAIN", "UPDATED_DATA"):
        setattr(package, key, "jcihitachi_tw" if key == "DOMAIN" else key.lower())

    class Base:
        def __init__(self, thing, coordinator):
            self._thing = thing
            self.coordinator = coordinator

    package.JciHitachiEntity = Base
    monkeypatch.setitem(sys.modules, "offline_hitachi", package)
    sensor_platform = ModuleType("homeassistant.components.sensor")
    sensor_platform.SensorEntity = type("SensorEntity", (), {
        "state_class": property(lambda self: getattr(self, "_attr_state_class", None)),
    })
    sensor_platform.SensorDeviceClass = SimpleNamespace(HUMIDITY="humidity", PM25="pm25", TEMPERATURE="temperature", ENERGY="energy")
    sensor_platform.SensorStateClass = SimpleNamespace(MEASUREMENT="measurement", TOTAL="total", TOTAL_INCREASING="total_increasing")
    monkeypatch.setitem(sys.modules, "homeassistant.components.sensor", sensor_platform)
    ha_const = ModuleType("homeassistant.const")
    ha_const.CONCENTRATION_MICROGRAMS_PER_CUBIC_METER = "µg/m³"
    ha_const.PERCENTAGE = "%"
    ha_const.UnitOfEnergy = SimpleNamespace(KILO_WATT_HOUR="kWh")
    ha_const.UnitOfTemperature = SimpleNamespace(CELSIUS="°C")
    monkeypatch.setitem(sys.modules, "homeassistant.const", ha_const)
    spec = importlib.util.spec_from_file_location("offline_hitachi.sensor", COMPONENT / "sensor.py")
    sensor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sensor)
    return SimpleNamespace(sensor=sensor)


@pytest.fixture
def context():
    """Provide one AC and an API mock that cannot publish network traffic."""
    thing = SimpleNamespace(type="AC", name="offline-test", gateway_mac_address="offline-id",
                            support_code=SimpleNamespace(), status_code=SimpleNamespace(_raw_status={}))
    api = MagicMock()
    api.things = {thing.name: thing}
    coordinator = MagicMock()
    hass = SimpleNamespace(data={"jcihitachi_tw": {"api": api, "coordinator": coordinator}})
    return hass, api, thing, coordinator


@pytest.mark.parametrize("raw,support,expected", [
    ({"PM25": 3}, None, 1),
    ({"PM25": 0}, "unsupported", 1),
    ({}, 999, 1),
    ({}, 0, 1),
    ({}, None, 0),
    ({}, "unsupported", 0),
    ({}, True, 0),
    ({}, -1, 0),
])
def test_ac_pm25_requires_reported_field_or_capability(modules, context, raw, support, expected):
    """Create an AC measurement only when its status or numeric capability advertises PM25."""
    hass, api, thing, coordinator = context
    thing.status_code._raw_status = raw
    thing.support_code.PM25 = support
    add = MagicMock()
    asyncio.run(modules.sensor.async_setup_entry(hass, None, add))
    entities = [entity for call in add.call_args_list for entity in call.args[0]]
    assert sum(isinstance(entity, modules.sensor.JciHitachiPM25SensorEntity) for entity in entities) == expected
    api.set_status.assert_not_called()


@pytest.mark.parametrize("value", [0, 1, 3, 999])
def test_actual_sdk_keeps_ac_pm25_measurement_and_legacy_name(modules, value):
    """The real SDK must preserve zero and positive readings without making PM25 controllable."""
    from JciHitachi.model import JciHitachiAWSStatus, STATUS_DICT

    state = JciHitachiAWSStatus({"DeviceType": 1, "PM25": value})
    assert state.PM25 == value
    assert state.legacy_status.pm25_value == value
    assert STATUS_DICT["AC"]["PM25"]["controllable"] is False
    assert STATUS_DICT["AC"]["PM25"]["is_numeric"] is True
    assert STATUS_DICT["AC"]["PM25"]["legacy_name"] == "pm25_value"


@pytest.mark.parametrize("device_type", ["AC", "DH"])
@pytest.mark.parametrize("value,expected", [
    (0, 0), (1, 1), (3, 3), (999, 999), (2.5, 2.5),
    (None, None), (True, None), (False, None), (-1, None),
    (float("nan"), None), (float("inf"), None), (float("-inf"), None),
    ("unsupported", None),
])
def test_pm25_sensor_preserves_measurements_and_rejects_invalid_values(modules, context, device_type, value, expected):
    """Both AC and existing DH sensors keep valid readings and never send a control command."""
    hass, api, thing, coordinator = context
    thing.type = device_type
    hass.data["jcihitachi_tw"]["updated_data"] = {thing.name: SimpleNamespace(pm25_value=value)}
    entity = modules.sensor.JciHitachiPM25SensorEntity(thing, coordinator)
    entity.hass = hass
    assert entity.native_value == expected
    assert entity.device_class == "pm25"
    assert entity.native_unit_of_measurement == "µg/m³"
    assert entity.state_class == "measurement"
    assert entity.unique_id == "offline-id_pm25_sensor"
    assert entity.name == "offline-test PM2.5"
    api.set_status.assert_not_called()


def test_pm25_sensor_missing_field_stays_unknown(modules, context):
    """An initial cached payload lacking the new legacy field must not become zero or raise."""
    hass, api, thing, coordinator = context
    hass.data["jcihitachi_tw"]["updated_data"] = {thing.name: SimpleNamespace()}
    entity = modules.sensor.JciHitachiPM25SensorEntity(thing, coordinator)
    entity.hass = hass
    assert entity.native_value is None
    api.set_status.assert_not_called()


def test_pm25_registration_keeps_existing_sdk_mapping(modules, monkeypatch):
    """The PM25 compatibility registration must preserve any future upstream SDK definition."""
    from JciHitachi.model import STATUS_DICT

    existing = {"controllable": False, "is_numeric": True, "legacy_name": "future_pm25"}
    monkeypatch.setitem(STATUS_DICT["AC"], "PM25", existing)
    modules.sensor.__spec__.loader.exec_module(modules.sensor)
    assert STATUS_DICT["AC"]["PM25"] is existing


def test_existing_dh_pm25_sensor_is_still_created(modules, context):
    """Adding AC support must retain the existing dehumidifier measurement entity."""
    hass, api, thing, coordinator = context
    thing.type = "DH"
    add = MagicMock()
    asyncio.run(modules.sensor.async_setup_entry(hass, None, add))
    entities = [entity for call in add.call_args_list for entity in call.args[0]]
    assert sum(isinstance(entity, modules.sensor.JciHitachiPM25SensorEntity) for entity in entities) == 1
    api.set_status.assert_not_called()
