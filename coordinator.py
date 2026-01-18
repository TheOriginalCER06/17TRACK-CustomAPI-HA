from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.storage import Store
from homeassistant.helpers import entity_registry as er
from .api import Track17Api
import logging
from .const import STORAGE_KEY, STORAGE_VERSION, EVENT_DELIVERED

_LOGGER = logging.getLogger(__name__)

class Track17Coordinator(DataUpdateCoordinator):
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
        await self.async_load()

        try:
            data = await self.api.fetch(self.tracking_numbers)

            for number, info in data.items():
                if info.get("status") == "Delivered" and number not in self._delivered_cache:
                    self._delivered_cache.add(number)
                    self.hass.bus.async_fire(
                        EVENT_DELIVERED,
                        {"tracking_number": number},
                    )

            return data
        except Exception as err:
            raise UpdateFailed(err)

    async def async_add_package(self, number):
        if not number or number in self.tracking_numbers:
            return False
        self.tracking_numbers.append(number)
        await self.async_save()
        await self.async_request_refresh()
        return True

    async def async_remove_package(self, number):
        if number not in self.tracking_numbers:
            return False

        self.tracking_numbers.remove(number)
        await self.async_save()

        # Remove entity from registry
        registry = er.async_get(self.hass)
        entity_id = f"sensor.package_{number.lower()}"

        if entity := registry.async_get(entity_id):
            registry.async_remove(entity.entity_id)

        await self.async_request_refresh()
        return True

    async def async_refresh_package(self, number):
        if number not in self.tracking_numbers:
            return False
        data = await self.api.fetch_single(number)
        self.data.update(data)
        self.async_set_updated_data(self.data)
        return True
