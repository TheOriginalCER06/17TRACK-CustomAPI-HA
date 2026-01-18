from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN

def track17_device_info(entry):
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="17TRACK Packages",
        manufacturer="17TRACK",
        model="Package Tracking",
        configuration_url="https://t.17track.net",
    )
