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
    # Create coordinator and register it early so other components can access
    # it during the first refresh.
    coordinator = Track17Coordinator(hass, entry)
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Load stored package list before the first refresh so sensors are
    # created for existing tracked numbers, then perform the first fetch.
    await coordinator.async_load()
    await coordinator.async_config_entry_first_refresh()

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

    async def handle_refresh_all(call):
        """Refresh all tracked packages on demand."""
        await coordinator.async_refresh_all_packages()

    # Register services
    hass.services.async_register(DOMAIN, "add_package", handle_add_package)
    hass.services.async_register(DOMAIN, "remove_package", handle_remove_package)
    hass.services.async_register(DOMAIN, "refresh_package", handle_refresh_package)
    hass.services.async_register(DOMAIN, "refresh_all_packages", handle_refresh_all)

    # Forward platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry and clean up resources."""
    coordinator: Track17Coordinator = hass.data[DOMAIN].get(entry.entry_id)
    if not coordinator:
        return True

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Close api session
    try:
        await coordinator.api.async_close()
    except Exception:
        pass

    # Remove saved coordinator reference and services
    hass.data[DOMAIN].pop(entry.entry_id, None)
    hass.services.async_remove(DOMAIN, "add_package")
    hass.services.async_remove(DOMAIN, "remove_package")
    hass.services.async_remove(DOMAIN, "refresh_package")

    return unload_ok
