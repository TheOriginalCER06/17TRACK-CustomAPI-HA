from homeassistant import config_entries
import voluptuous as vol
from .const import DOMAIN, DEFAULT_SCAN_INTERVAL_HOURS

class Track17ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input:
            return self.async_create_entry(
                title="17TRACK",
                data={"api_key": user_input["api_key"]},
                options={"scan_interval": DEFAULT_SCAN_INTERVAL_HOURS},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("api_key"): str
            }),
        )

    async def async_step_options(self, user_input=None):
        if user_input:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="options",
            data_schema=vol.Schema({
                vol.Required(
                    "scan_interval",
                    default=DEFAULT_SCAN_INTERVAL_HOURS
                ): int
            }),
        )
