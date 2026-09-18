"""Sensor platform for the Nea Smart integration."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DEVICE_FIELDS,
    HEATAREA_FIELDS,
    PLATFORM_SENSOR,
    DeviceField,
    HeatAreaField,
    Zone,
)
from .coordinator import NeaSmartCoordinator
from .entity import (
    NeaSmartDeviceEntity,
    NeaSmartZoneEntity,
    as_float,
    as_timestamp,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensors declared by the integration."""
    coordinator: NeaSmartCoordinator = entry.runtime_data
    entities: list[SensorEntity] = []
    for zone in coordinator.zones.values():
        if not coordinator.is_zone_enabled(zone.nr):
            continue
        entities.extend(
            NeaSmartZoneSensor(coordinator, entry, zone, field)
            for field in HEATAREA_FIELDS
            if field.platform == PLATFORM_SENSOR
        )
    entities.extend(
        NeaSmartDeviceSensor(coordinator, entry, field)
        for field in DEVICE_FIELDS
        if field.platform == PLATFORM_SENSOR
    )
    async_add_entities(entities)


class NeaSmartZoneSensor(NeaSmartZoneEntity, SensorEntity):
    """A read only value of a heat area."""

    def __init__(
        self,
        coordinator: NeaSmartCoordinator,
        entry: ConfigEntry,
        zone: Zone,
        field: HeatAreaField,
    ) -> None:
        """Initialise the sensor for one heat area field."""
        super().__init__(coordinator, entry, zone, field)
        self._attr_native_unit_of_measurement = field.unit
        self._attr_device_class = field.device_class
        self._attr_state_class = field.state_class

    @property
    def native_value(self) -> float | str | None:
        """Return the last reported value."""
        value = self.raw_value
        if self._field.state_class is not None:
            return as_float(value)
        number = as_float(value)
        if number is not None:
            return number
        if value is None:
            return None
        text = str(value).strip()
        return text or None


class NeaSmartDeviceSensor(NeaSmartDeviceEntity, SensorEntity):
    """A read only value of the base itself."""

    def __init__(
        self,
        coordinator: NeaSmartCoordinator,
        entry: ConfigEntry,
        field: DeviceField,
    ) -> None:
        """Initialise the sensor for one device level field."""
        super().__init__(coordinator, entry, field)
        self._attr_native_unit_of_measurement = field.unit
        self._attr_device_class = field.device_class
        self._attr_state_class = field.state_class

    @property
    def native_value(self) -> float | str | None:
        """Return the last reported value."""
        value = self.raw_value
        if self._field.device_class == "timestamp":
            return as_timestamp(value)
        if self._field.state_class is not None:
            return as_float(value)
        number = as_float(value)
        if number is not None:
            return number
        if value is None:
            return None
        text = str(value).strip()
        return text or None
