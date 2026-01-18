from homeassistant.components.button import ButtonEntity
from .device import track17_device_info

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data["track17"][entry.entry_id]
    async_add_entities([Track17RefreshButton(coordinator)])

class Track17RefreshButton(ButtonEntity):
    name = "Refresh 17TRACK"
    unique_id = "track17_refresh"

    async def async_press(self):
        await self.coordinator.async_request_refresh()

    @property
    def device_info(self):
        return track17_device_info(self.coordinator.entry)
