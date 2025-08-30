from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import HwmonCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: HwmonCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[HwmonTempSensor] = []
    for key, reading in coordinator.data.items():
        entities.append(HwmonTempSensor(coordinator, entry.entry_id, key))

    async_add_entities(entities)


class HwmonTempSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: HwmonCoordinator, entry_id: str, key: str) -> None:
        self.coordinator = coordinator
        self._key = key
        self._entry_id = entry_id
        reading = coordinator.data[key]

        self._attr_unique_id = f"hwmon_temp_{key}"
        self._attr_name = reading.display_name

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        reading = self.coordinator.data.get(self._key)
        if not reading:
            return None
        return {"device": reading.device_node} if reading.device_node else None

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name="HWMON Temperatures",
            manufacturer="Linux",
            model="hwmon",
        )

    @property
    def native_value(self) -> float | None:
        reading = self.coordinator.data.get(self._key)
        return reading.temperature_c if reading else None

    async def async_update(self) -> None:
        await self.coordinator.async_request_refresh()
