from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers import entity_registry as er
from homeassistant.components import input_text as it
from .const import DOMAIN
from .coordinator import Track17Coordinator

PLATFORMS = ["sensor", "button"]

DEFAULT_HELPER_ENTITY = "input_text.track17_new_package"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    # Create coordinator
    coordinator = Track17Coordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Automatically create input_text helper if it doesn't exist
    if DEFAULT_HELPER_ENTITY not in hass.states:
        await hass.services.async_call(
            "input_text",
            "create",
            {
                "name": "17TRACK New Package",
                "entity_id": DEFAULT_HELPER_ENTITY,
                "max": 40
            },
        )

    # Service handlers
    async def handle_add_package(call):
        number = call.data["tracking_number"]
        added = await coordinator.async_add_package(number)
        if added:
            await hass.config_entries.async_reload(entry.entry_id)

    async def handle_remove_package(call):
        number = call.data["tracking_number"]
        removed = await coordinator.async_remove_package(number)
        if removed:
            await hass.config_entries.async_reload(entry.entry_id)

    async def handle_refresh_package(call):
        number = call.data["tracking_number"]
        await coordinator.async_refresh_package(number)

    # Register services
    hass.services.async_register(DOMAIN, "add_package", handle_add_package)
    hass.services.async_register(DOMAIN, "remove_package", handle_remove_package)
    hass.services.async_register(DOMAIN, "refresh_package", handle_refresh_package)

    # Forward platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True
