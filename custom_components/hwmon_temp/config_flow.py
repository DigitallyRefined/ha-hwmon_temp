from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN


class HwmonConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            # Single instance only
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="HWMON Temperatures", data=user_input)

        data_schema = vol.Schema(
            {vol.Optional("scan_interval", default=DEFAULT_SCAN_INTERVAL): int}
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )


class HwmonOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="Options", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Optional(
                    "scan_interval",
                    default=self.config_entry.options.get(
                        "scan_interval",
                        self.config_entry.data.get(
                            "scan_interval", DEFAULT_SCAN_INTERVAL
                        ),
                    ),
                ): int
            }
        )
        return self.async_show_form(step_id="init", data_schema=data_schema)


@callback
def async_get_options_flow(config_entry: config_entries.ConfigEntry):
    return HwmonOptionsFlowHandler(config_entry)
