from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .device import track17_device_info

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data["track17"][entry.entry_id]

    entities = [Track17PackageList(coordinator)]
    for number in coordinator.tracking_numbers:
        entities.append(Track17PackageSensor(coordinator, number))

    async_add_entities(entities)

class Track17PackageList(CoordinatorEntity, SensorEntity):
    name = "Tracked Packages"
    unique_id = "track17_packages"

    @property
    def state(self):
        return len(self.coordinator.tracking_numbers)

    @property
    def extra_state_attributes(self):
        return {"packages": self.coordinator.tracking_numbers}

    @property
    def device_info(self):
        return track17_device_info(self.coordinator.entry)

class Track17PackageSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, number):
        super().__init__(coordinator)
        self._number = number

    @property
    def name(self):
        return f"Package {self._number}"

    @property
    def unique_id(self):
        return f"track17_{self._number}"

    @property
    def state(self):
        return self.coordinator.data.get(self._number, {}).get("status")

    @property
    def extra_state_attributes(self):
        d = self.coordinator.data.get(self._number, {})
        return {
            "tracking_number": self._number,
            "carrier": d.get("carrier"),
            "country": d.get("country"),
            "last_event": d.get("lastEvent"),
            "delivered_at": d.get("deliveredAt"),
            "url": f"https://t.17track.net/en#nums={self._number}",
        }

    @property
    def device_info(self):
        return track17_device_info(self.coordinator.entry)
