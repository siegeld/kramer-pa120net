# config_flow.py
import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN

DATA_SCHEMA = vol.Schema(
    {
        vol.Required("host"): str,
        vol.Required("port", default=5000): int,
        vol.Required("name", default="PA120Net"): str,
    }
)

class PA120NetConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PA120Net."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            await self.async_set_unique_id(f"{user_input['host']}_{user_input['port']}")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_input["name"], data=user_input)
        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors=errors)
