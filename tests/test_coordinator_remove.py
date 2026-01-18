import pytest
import asyncio
from unittest.mock import MagicMock

from custom_components.track17 import coordinator


@pytest.mark.asyncio
async def test_async_remove_package_removes_entity_and_saves(monkeypatch):
    # Minimal fake hass and entry
    hass = MagicMock()
    hass.bus = MagicMock()

    entry = MagicMock()
    entry.data = {"api_key": "abc"}
    entry.options = {}
    entry.entry_id = "test"

    # Dummy Store that records saved data
    class DummyStore:
        def __init__(self, hass_arg, version, key):
            self._data = []

        async def async_load(self):
            return []

        async def async_save(self, data):
            self._data = list(data)

    monkeypatch.setattr(coordinator, "Store", DummyStore)

    # Instantiate coordinator
    coord = coordinator.Track17Coordinator(hass, entry)

    # Replace network/API with a dummy
    coord.api = MagicMock()

    # Seed tracking numbers
    coord.tracking_numbers = ["LP1"]

    # Fake entity registry
    registry = MagicMock()
    entity = MagicMock()
    entity.entity_id = "sensor.track17_LP1"
    registry.async_get.return_value = entity

    monkeypatch.setattr(coordinator.er, "async_get", lambda hass_arg: registry)

    # Call removal
    result = await coord.async_remove_package("LP1")

    assert result is True
    assert "LP1" not in coord.tracking_numbers
    registry.async_remove.assert_called_with("sensor.track17_LP1")
