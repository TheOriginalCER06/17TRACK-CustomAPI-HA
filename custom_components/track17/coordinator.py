from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.storage import Store
from homeassistant.helpers import entity_registry as er
from .api import Track17Api
from .const import STORAGE_KEY, STORAGE_VERSION, EVENT_DELIVERED
import logging

_LOGGER = logging.getLogger(__name__)

class Track17Coordinator(DataUpdateCoordinator):
    """Coordinator for fetching 17TRACK data."""

    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry
        self.api = Track17Api(entry.data["api_key"])
        self.store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.tracking_numbers = []
        self._delivered_cache = set()

        interval = entry.options.get("scan_interval", 24)

        super().__init__(
            hass,
            logger=_LOGGER,
            name="17TRACK",
            update_interval=timedelta(hours=interval),
        )

    async def async_load(self):
        self.tracking_numbers = await self.store.async_load() or []

    async def async_save(self):
        await self.store.async_save(self.tracking_numbers)

    async def _async_update_data(self):
        """Fetch data for all tracked packages safely."""
        results = {}
        for number in self.tracking_numbers:
            try:
                data = await self.api.async_get_tracking(number)
    
                # Parse string JSON if necessary
                if isinstance(data, str):
                    import json
                    try:
                        data = json.loads(data)
                    except json.JSONDecodeError:
                        self.logger.error("Invalid JSON for %s: %s", number, data)
                        continue
                    
                # Ensure we have a dict
                if not isinstance(data, dict):
                    self.logger.error("Unexpected data format for %s: %s", number, data)
                    continue
                
                results[number] = data
    
                # Fire delivery event if delivered
                if data.get("status") == "Delivered" and number not in self._delivered_cache:
                    self._delivered_cache.add(number)
                    self.hass.bus.async_fire(
                        "track17_delivered",
                        {"tracking_number": number, "data": data},
                    )
    
            except Exception as e:
                self.logger.error("Error fetching 17TRACK data for %s: %s", number, e)
    
        return results


    async def async_add_package(self, number):
        """Add a package and refresh sensors."""
        if not number or number in self.tracking_numbers:
            return False
        data = await self.api.async_get_tracking(number)
        if "error" in data:
            self.logger.warning("Cannot add %s: %s", number, data["error"])
            return False
        self.tracking_numbers.append(number)
        await self.async_save()
        await self.async_request_refresh()
        return True

    async def async_remove_package(self, number):
        """Remove a package and its sensor."""
        if number not in self.tracking_numbers:
            return False
        self.tracking_numbers.remove(number)
        await self.async_save()

        registry = er.async_get(self.hass)
        entity_id = f"sensor.track17_{number}"
        if entity := registry.async_get(entity_id):
            registry.async_remove(entity.entity_id)

        await self.async_request_refresh()
        return True

    async def async_refresh_package(self, number):
        """Refresh a single package."""
        if number not in self.tracking_numbers:
            return False
        data = await self.api.fetch_single(number)
        self.data.update(data)
        self.async_set_updated_data(self.data)
        return True

    async def async_refresh_all_packages(self):
        """Refresh all packages on demand."""
        await self.async_request_refresh()
