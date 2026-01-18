from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .coordinator import Track17Coordinator

PLATFORMS = ["sensor", "button"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    coordinator = Track17Coordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    async def handle_add_package(call):
        await coordinator.async_add_package(call.data["tracking_number"])

    async def handle_remove_package(call):
        await coordinator.async_remove_package(call.data["tracking_number"])

    async def handle_refresh_package(call):
        await coordinator.async_refresh_package(call.data["tracking_number"])

    hass.services.async_register(DOMAIN, "add_package", handle_add_package)
    hass.services.async_register(DOMAIN, "remove_package", handle_remove_package)
    hass.services.async_register(DOMAIN, "refresh_package", handle_refresh_package)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True
