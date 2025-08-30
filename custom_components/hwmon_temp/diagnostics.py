from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN
from .coordinator import HwmonCoordinator

REDACT_KEYS = {"device"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    coordinator: HwmonCoordinator = hass.data[DOMAIN][entry.entry_id]
    data = {
        key: {
            "name": r.display_name,
            "device": r.device_node,
            "temperature_c": r.temperature_c,
        }
        for key, r in coordinator.data.items()
    }
    return async_redact_data({"readings": data}, REDACT_KEYS)
