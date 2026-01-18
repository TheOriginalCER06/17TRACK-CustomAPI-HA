from datetime import timedelta
import asyncio
import json
from typing import Any, Dict, List, Optional, Set, Tuple

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.storage import Store
from homeassistant.helpers import entity_registry as er

from .api import Track17Api
from .const import STORAGE_KEY, STORAGE_VERSION, EVENT_DELIVERED
import logging

_LOGGER = logging.getLogger(__name__)


class Track17Coordinator(DataUpdateCoordinator):
    """Coordinator for fetching 17TRACK data.

    This coordinator fetches tracking info concurrently with a small
    semaphore to avoid hammering the API. It stores a list of tracking
    numbers in the integration storage and exposes small helpers for
    adding/removing/refreshing packages.
    """

    def __init__(self, hass, entry):
        self.hass = hass
        self.entry = entry
        self.api = Track17Api(entry.data["api_key"])
        self.store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.tracking_numbers: List[str] = []
        self._delivered_cache: Set[str] = set()

        interval = entry.options.get("scan_interval", 24)

        super().__init__(
            hass,
            logger=_LOGGER,
            name="17TRACK",
            update_interval=timedelta(hours=interval),
        )

        # Limit concurrent outgoing requests
        self._concurrency = 5

    async def async_load(self) -> None:
        """Load tracking numbers from storage, ensuring a list is returned."""
        try:
            stored = await self.store.async_load()
            if isinstance(stored, list):
                self.tracking_numbers = stored
            else:
                self.tracking_numbers = []
        except Exception as err:
            self.logger.exception("Failed to load stored tracking numbers: %s", err)
            self.tracking_numbers = []

    async def async_save(self) -> None:
        """Persist the tracking numbers list to storage."""
        try:
            await self.store.async_save(self.tracking_numbers)
        except Exception as err:
            self.logger.exception("Failed to save tracking numbers: %s", err)

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data for all tracked packages concurrently and return a mapping.

        The method uses a semaphore to limit concurrency and returns a mapping
        of tracking_number -> data suitable for Coordinator consumers.
        """
        results: Dict[str, Any] = {}
        sem = asyncio.Semaphore(self._concurrency)

        async def _fetch(number: str) -> Optional[Tuple[str, Any]]:
            async with sem:
                try:
                    data = await self.api.async_get_tracking(number)

                    # If data is a JSON string, try to parse it
                    if isinstance(data, str):
                        try:
                            data = json.loads(data)
                        except json.JSONDecodeError:
                            self.logger.error("Invalid JSON for %s: %s", number, data)
                            return None

                    if not isinstance(data, dict):
                        self.logger.error("Unexpected data format for %s: %s", number, type(data))
                        return None

                    return (number, data)
                except Exception as exc:  # noqa: BLE001 - we want to catch all runtime errors
                    self.logger.exception("Error fetching 17TRACK data for %s: %s", number, exc)
                    return None

        tasks = [asyncio.create_task(_fetch(num)) for num in self.tracking_numbers]

        for task in asyncio.as_completed(tasks):
            res = await task
            if not res:
                continue
            number, data = res
            results[number] = data

            # Fire delivery event if delivered and not already seen
            if data.get("status") == "Delivered" and number not in self._delivered_cache:
                self._delivered_cache.add(number)
                self.hass.bus.async_fire(EVENT_DELIVERED, {"tracking_number": number, "data": data})

        return results

    async def async_add_package(self, number: str) -> bool:
        """Add a package and request a refresh. Returns True if added."""
        if not number or number in self.tracking_numbers:
            return False

        # Reject obvious template literals or UI-templating that were sent
        # verbatim from Lovelace. This prevents sensors like
        # `sensor.package_states_input_text_track17_new_package` being created
        # when a template string (e.g. "{{ states('input_text...') }}") is
        # accidentally passed as the tracking number.
        if isinstance(number, str):
            s = number.strip()
            if (s.startswith("{{") and s.endswith("}}")) or "{{" in s or "}}" in s or "states(" in s:
                self.logger.warning("Rejected template-like tracking number: %s", number)
                return False
        data = await self.api.async_get_tracking(number)
        if isinstance(data, dict) and "error" in data:
            self.logger.warning("Cannot add %s: %s", number, data.get("error"))
            return False

        self.tracking_numbers.append(number)
        await self.async_save()
        await self.async_request_refresh()
        return True

    async def async_remove_package(self, number: str) -> bool:
        """Remove a package, delete its entity and request a refresh."""
        if number not in self.tracking_numbers:
            return False
        try:
            self.tracking_numbers.remove(number)
            await self.async_save()

            registry = er.async_get(self.hass)
            entity_id = f"sensor.track17_{number}"
            if entity := registry.async_get(entity_id):
                registry.async_remove(entity.entity_id)

            await self.async_request_refresh()
            return True
        except Exception as exc:
            self.logger.exception("Failed to remove package %s: %s", number, exc)
            return False

    async def async_refresh_package(self, number: str) -> bool:
        """Refresh a single package and update coordinator data."""
        if number not in self.tracking_numbers:
            return False
        data = await self.api.fetch_single(number)
        # fetch_single returns { number: data }
        self.data.update(data)
        self.async_set_updated_data(self.data)
        return True

    async def async_refresh_all_packages(self) -> None:
        """Trigger a full refresh for all packages."""
        await self.async_request_refresh()

    async def async_close(self) -> None:
        """Close internal resources (HTTP session)."""
        try:
            await self.api.async_close()
        except Exception:
            pass
