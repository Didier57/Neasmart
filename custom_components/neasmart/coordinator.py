"""Data update coordinator for the Nea Smart integration."""

from __future__ import annotations

import copy
import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import NeaSmartApiError, NeaSmartClient, NeaSmartConnectionError
from .const import (
    CONF_BASE_ID,
    CONF_ENABLED_ZONES,
    CONF_SCAN_INTERVAL,
    CONF_ZONES,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    Zone,
)

_LOGGER = logging.getLogger(__name__)


def _parse_enabled_zones(raw: Any) -> set[int] | None:
    """Return the set of enabled heat area numbers, or ``None`` for all."""
    if not raw:
        return None
    enabled: set[int] = set()
    for value in raw:
        try:
            enabled.add(int(value))
        except (TypeError, ValueError):
            continue
    return enabled or None


class NeaSmartCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll a base and expose its data to the entities."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: NeaSmartClient,
    ) -> None:
        """Initialise the coordinator.

        Args:
            hass: The Home Assistant instance.
            entry: The config entry being set up.
            client: The XML client bound to this base.
        """
        scan_interval = entry.options.get(
            CONF_SCAN_INTERVAL,
            entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} {entry.title}",
            update_interval=timedelta(seconds=scan_interval),
            config_entry=entry,
        )
        self.client = client
        self.base_id: str = entry.data[CONF_BASE_ID]
        self.zones: dict[int, Zone] = self._build_zones(entry)
        self._enabled_zones = _parse_enabled_zones(
            entry.options.get(CONF_ENABLED_ZONES)
        )

    @staticmethod
    def _build_zones(entry: ConfigEntry) -> dict[int, Zone]:
        """Rebuild the zone descriptors stored in the config entry."""
        zones: dict[int, Zone] = {}
        for raw in entry.data.get(CONF_ZONES, []):
            nr = int(raw["nr"])
            zones[nr] = Zone(
                nr=nr,
                name=raw.get("name") or f"Zone {nr}",
                min_temperature=float(raw.get("min", 5.0)),
                max_temperature=float(raw.get("max", 30.0)),
            )
        return zones

    def is_zone_enabled(self, nr: int) -> bool:
        """Return whether the heat area should expose its entities."""
        return self._enabled_zones is None or nr in self._enabled_zones

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch ``dynamic.xml`` and return the device and zone sections."""
        try:
            document = await self.client.async_get_dynamic()
        except NeaSmartConnectionError as err:
            raise UpdateFailed(f"cannot reach the base: {err}") from err
        except NeaSmartApiError as err:
            raise UpdateFailed(f"the base sent an unusable answer: {err}") from err
        return {
            "device": document.get("device", {}),
            "heatareas": document.get("heatareas", {}),
        }

    async def async_write_zone(self, nr: int, tag: str, value: Any) -> None:
        """Write a value in a heat area and reflect it optimistically.

        Args:
            nr: The ``nr`` of the target heat area.
            tag: The XML element to write.
            value: The value to send.
        """
        await self.client.async_write_heatarea(self.base_id, nr, tag, value)
        self._optimistic_zone(nr, tag, value)

    async def async_write_device(self, path: tuple[str, ...], value: Any) -> None:
        """Write a device level value and reflect it optimistically.

        Args:
            path: The element names leading to the value.
            value: The value to send.
        """
        await self.client.async_write_device(self.base_id, path, value)
        self._optimistic_device(path, value)

    def _optimistic_zone(self, nr: int, tag: str, value: Any) -> None:
        """Store a written heat area value without waiting for the next poll."""
        data = dict(self.data or {})
        heatareas = {
            key: dict(section) for key, section in (data.get("heatareas") or {}).items()
        }
        zone = dict(heatareas.get(nr) or {})
        zone[tag] = value
        heatareas[nr] = zone
        data["heatareas"] = heatareas
        self.data = data
        self.async_update_listeners()

    def _optimistic_device(self, path: tuple[str, ...], value: Any) -> None:
        """Store a written device value without waiting for the next poll."""
        data = dict(self.data or {})
        device = copy.deepcopy(data.get("device") or {})
        node: dict[str, Any] = device
        for name in path[:-1]:
            child = node.get(name)
            if not isinstance(child, dict):
                child = {}
                node[name] = child
            node = child
        node[path[-1]] = value
        data["device"] = device
        self.data = data
        self.async_update_listeners()
