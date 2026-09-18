"""Binary sensor platform for the Nea Smart integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DEVICE_FIELDS,
    HEATAREA_FIELDS,
    PLATFORM_BINARY_SENSOR,
    DeviceField,
    HeatAreaField,
    Zone,
)
from .coordinator import NeaSmartCoordinator
from .entity import NeaSmartDeviceEntity, NeaSmartZoneEntity, as_int


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensors declared by the integration."""
    coordinator: NeaSmartCoordinator = entry.runtime_data
    entities: list[BinarySensorEntity] = []
    for zone in coordinator.zones.values():
        if not coordinator.is_zone_enabled(zone.nr):
            continue
        entities.extend(
            NeaSmartZoneBinarySensor(coordinator, entry, zone, field)
            for field in HEATAREA_FIELDS
            if field.platform == PLATFORM_BINARY_SENSOR
        )
    entities.extend(
        NeaSmartDeviceBinarySensor(coordinator, entry, field)
        for field in DEVICE_FIELDS
        if field.platform == PLATFORM_BINARY_SENSOR
    )
    async_add_entities(entities)


class NeaSmartZoneBinarySensor(NeaSmartZoneEntity, BinarySensorEntity):
    """A boolean flag of a heat area."""

    def __init__(
        self,
        coordinator: NeaSmartCoordinator,
        entry: ConfigEntry,
        zone: Zone,
        field: HeatAreaField,
    ) -> None:
        """Initialise the binary sensor for one heat area field."""
        super().__init__(coordinator, entry, zone, field)
        self._attr_device_class = field.device_class

    @property
    def is_on(self) -> bool | None:
        """Return whether the flag is set."""
        code = as_int(self.raw_value)
        if code is None:
            return None
        return code != 0


class NeaSmartDeviceBinarySensor(NeaSmartDeviceEntity, BinarySensorEntity):
    """A boolean flag of the base itself."""

    def __init__(
        self,
        coordinator: NeaSmartCoordinator,
        entry: ConfigEntry,
        field: DeviceField,
    ) -> None:
        """Initialise the binary sensor for one device level field."""
        super().__init__(coordinator, entry, field)
        self._attr_device_class = field.device_class

    @property
    def is_on(self) -> bool | None:
        """Return whether the flag is set."""
        code = as_int(self.raw_value)
        if code is None:
            return None
        return code != 0
