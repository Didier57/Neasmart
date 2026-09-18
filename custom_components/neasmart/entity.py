"""Shared entity helpers for the Nea Smart integration."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import parse_float, parse_int
from .const import (
    CONF_BASE_ID,
    CONF_BASE_NAME,
    CONF_FIRMWARE,
    DOMAIN,
    MANUFACTURER,
    MODEL,
    DeviceField,
    HeatAreaField,
    Zone,
)
from .coordinator import NeaSmartCoordinator


def base_device_info(
    coordinator: NeaSmartCoordinator, entry: ConfigEntry
) -> DeviceInfo:
    """Build the device registry entry for the base itself."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.data.get(CONF_BASE_NAME) or entry.title,
        manufacturer=MANUFACTURER,
        model=MODEL,
        configuration_url=coordinator.client.base_url,
        serial_number=entry.data.get(CONF_BASE_ID),
        sw_version=entry.data.get(CONF_FIRMWARE),
    )


def zone_device_info(entry: ConfigEntry, zone: Zone) -> DeviceInfo:
    """Build the device registry entry for a single heat area."""
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry.entry_id}_zone_{zone.nr}")},
        name=zone.name,
        manufacturer=MANUFACTURER,
        model=MODEL,
        via_device=(DOMAIN, entry.entry_id),
    )


def as_float(value: Any) -> float | None:
    """Return ``value`` as a float when possible."""
    return parse_float(value)


def as_int(value: Any) -> int | None:
    """Return ``value`` as an int when possible."""
    return parse_int(value)


def as_timestamp(value: Any) -> datetime | None:
    """Return ``value`` parsed as an ISO 8601 timestamp when possible."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


class NeaSmartZoneEntity(CoordinatorEntity[NeaSmartCoordinator]):
    """Base class for every entity attached to a heat area."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NeaSmartCoordinator,
        entry: ConfigEntry,
        zone: Zone,
        field: HeatAreaField,
    ) -> None:
        """Initialise the entity for one field of one heat area.

        Args:
            coordinator: The shared coordinator.
            entry: The config entry being set up.
            zone: The heat area the entity belongs to.
            field: The description of the exposed XML element.
        """
        super().__init__(coordinator)
        self._entry = entry
        self._zone = zone
        self._field = field
        self._attr_unique_id = f"{entry.entry_id}_zone_{zone.nr}_{field.key}"
        self._attr_device_info = zone_device_info(entry, zone)
        self._attr_translation_key = field.translation_key
        self._attr_entity_registry_enabled_default = field.enabled_default

    @property
    def raw_value(self) -> Any:
        """Return the last value reported for this field."""
        heatareas = (self.coordinator.data or {}).get("heatareas") or {}
        return (heatareas.get(self._zone.nr) or {}).get(self._field.tag)


class NeaSmartDeviceEntity(CoordinatorEntity[NeaSmartCoordinator]):
    """Base class for every entity attached to the base itself."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: NeaSmartCoordinator,
        entry: ConfigEntry,
        field: DeviceField,
    ) -> None:
        """Initialise the entity for one device level field.

        Args:
            coordinator: The shared coordinator.
            entry: The config entry being set up.
            field: The description of the exposed XML element.
        """
        super().__init__(coordinator)
        self._entry = entry
        self._field = field
        self._attr_unique_id = f"{entry.entry_id}_device_{field.key}"
        self._attr_device_info = base_device_info(coordinator, entry)
        self._attr_translation_key = field.translation_key
        self._attr_entity_registry_enabled_default = field.enabled_default

    @property
    def raw_value(self) -> Any:
        """Return the last value reported for this field."""
        node: Any = (self.coordinator.data or {}).get("device") or {}
        for name in self._field.path:
            if not isinstance(node, dict):
                return None
            node = node.get(name) or {}
        if not isinstance(node, dict):
            return None
        return node.get(self._field.tag)
