from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .device import track17_device_info
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [Track17PackageList(coordinator)]

    # dynamically add package sensors
    for number in coordinator.tracking_numbers:
        entities.append(Track17PackageSensor(coordinator, number))

    async_add_entities(entities, True)


class Track17PackageList(CoordinatorEntity, SensorEntity):
    """Sensor showing total tracked packages and their list."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Tracked Packages"
        self._attr_unique_id = f"{DOMAIN}_packages"

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
    """Sensor for an individual package."""

    def __init__(self, coordinator, number):
        super().__init__(coordinator)
        self._number = number
        self._attr_name = f"Package {number}"
        self._attr_unique_id = f"{DOMAIN}_{number}"

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
