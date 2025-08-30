from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
import logging


LOGGER = logging.getLogger(__name__)


SYS_CLASS_HWMON = Path("/sys/class/hwmon")


@dataclass
class TemperatureReading:
    display_name: str
    device_node: str | None
    unique_key: str
    temperature_c: float


def _read_text_file(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return None


def _resolve_device_path(hwmon_path: Path) -> Optional[Path]:
    try:
        device_link = (hwmon_path / "device").resolve(strict=False)
        return device_link
    except Exception:
        return None


def _scan_hwmon_temperatures() -> List[TemperatureReading]:
    results: List[TemperatureReading] = []

    hwmon_dirs = list(SYS_CLASS_HWMON.glob("hwmon*"))
    if not hwmon_dirs:
        LOGGER.warning(
            "No hwmon devices found in /sys/class/hwmon. This may indicate that hardware monitoring is not available or not properly configured. If you're running Home Assistant inside of a virtual machine, this is expected if /sys/class/hwmon/ is not shared from host machine to the guest machine."
        )

    for hwmon in sorted(hwmon_dirs):
        name = _read_text_file(hwmon / "name") or ""
        device_path = _resolve_device_path(hwmon)

        temp_inputs = sorted(hwmon.glob("temp*_input"))
        for input_file in temp_inputs:
            if not input_file.is_file():
                continue

            # Decide display name like the bash script
            display_name: str = ""
            device_node: str | None = None

            device_basename = device_path.name if device_path else ""
            dev_node = Path("/dev") / device_basename if device_basename else None

            if (dev_node and dev_node.exists()) or name == "nvme":
                model = _read_text_file(hwmon / "device" / "model") or ""
                device_node = f"/dev/{device_basename}" if device_basename else None
                display_name = (
                    model if model else (name or device_basename or "temperature")
                )
            else:
                label = (
                    _read_text_file(Path(str(input_file).replace("_input", "_label")))
                    or ""
                )
                if name == "coretemp":
                    device_node = "/dev/cpu"
                    display_name = label if label else name or "cpu"
                elif device_path and "thermal_zone" in str(device_path):
                    device_node = "/dev/cpu"
                    display_name = name or "cpu"
                else:
                    device_node = f"/dev/{device_basename}" if device_basename else None
                    combined = f"{name} {label}".strip()
                    display_name = (
                        combined
                        if combined
                        else (name or label or device_basename or "temperature")
                    )

            # Read temperature
            raw_text = _read_text_file(input_file)
            if raw_text is None:
                continue
            try:
                raw_value = int(raw_text)
            except ValueError:
                # Some files might be non-integer; try float
                try:
                    raw_value = int(float(raw_text))
                except Exception:
                    continue

            temp_c = round(raw_value / 1000.0, 1)

            # Unique key based on path
            unique_key = f"{hwmon.name}-{input_file.stem}"

            results.append(
                TemperatureReading(
                    display_name=display_name,
                    device_node=device_node,
                    unique_key=unique_key,
                    temperature_c=temp_c,
                )
            )

    return results


class HwmonCoordinator(DataUpdateCoordinator[Dict[str, TemperatureReading]]):
    def __init__(self, hass: HomeAssistant, update_interval) -> None:
        super().__init__(
            hass,
            LOGGER,
            name="Hwmon Temperatures",
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> Dict[str, TemperatureReading]:
        readings: List[TemperatureReading] = await self.hass.async_add_executor_job(
            _scan_hwmon_temperatures
        )
        return {reading.unique_key: reading for reading in readings}
