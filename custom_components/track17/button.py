from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

class Track17RefreshButton(CoordinatorEntity, ButtonEntity):
    """Button to refresh all 17TRACK packages."""

    def __init__(self, coordinator):
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_name = "17TRACK Refresh"
        self._attr_unique_id = f"{DOMAIN}_refresh_button"
        self._attr_icon = "mdi:refresh"

    async def async_press(self) -> None:
        """Handle the button press."""
        # Use the coordinator helper which triggers a refresh for all
        # packages. Coordinator exposes async_refresh_all_packages.
        if hasattr(self.coordinator, "async_refresh_all_packages"):
            await self.coordinator.async_refresh_all_packages()
        else:
            # Fallback to requesting a refresh
            await self.coordinator.async_request_refresh()


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the 17TRACK button platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([Track17RefreshButton(coordinator)])

