"""Number platform for the Nea Smart integration."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DEFAULT_T_TARGET_MAX,
    DEFAULT_T_TARGET_MIN,
    DEFAULT_T_TARGET_STEP,
    DEVICE_FIELDS,
    HEATAREA_FIELDS,
    PLATFORM_NUMBER,
    DeviceField,
    HeatAreaField,
    Zone,
)
from .coordinator import NeaSmartCoordinator
from .entity import NeaSmartDeviceEntity, NeaSmartZoneEntity, as_float


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the writable numbers declared by the integration."""
    coordinator: NeaSmartCoordinator = entry.runtime_data
    entities: list[NumberEntity] = []
    for zone in coordinator.zones.values():
        if not coordinator.is_zone_enabled(zone.nr):
            continue
        entities.extend(
            NeaSmartZoneNumber(coordinator, entry, zone, field)
            for field in HEATAREA_FIELDS
            if field.platform == PLATFORM_NUMBER
        )
    entities.extend(
        NeaSmartDeviceNumber(coordinator, entry, field)
        for field in DEVICE_FIELDS
        if field.platform == PLATFORM_NUMBER
    )
    async_add_entities(entities)


class NeaSmartZoneNumber(NeaSmartZoneEntity, NumberEntity):
    """A setpoint that can be written back to a heat area."""

    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        coordinator: NeaSmartCoordinator,
        entry: ConfigEntry,
        zone: Zone,
        field: HeatAreaField,
    ) -> None:
        """Initialise the number for one heat area field."""
        super().__init__(coordinator, entry, zone, field)
        self._attr_native_unit_of_measurement = field.unit
        self._attr_device_class = field.device_class
        self._attr_native_min_value = zone.min_temperature
        self._attr_native_max_value = zone.max_temperature
        self._attr_native_step = DEFAULT_T_TARGET_STEP

    @property
    def native_value(self) -> float | None:
        """Return the current setpoint."""
        return as_float(self.raw_value)

    async def async_set_native_value(self, value: float) -> None:
        """Write a new setpoint to the base."""
        await self.coordinator.async_write_zone(self._zone.nr, self._field.tag, value)


class NeaSmartDeviceNumber(NeaSmartDeviceEntity, NumberEntity):
    """A setpoint that can be written back to the base itself."""

    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        coordinator: NeaSmartCoordinator,
        entry: ConfigEntry,
        field: DeviceField,
    ) -> None:
        """Initialise the number for one device level field."""
        super().__init__(coordinator, entry, field)
        self._attr_native_unit_of_measurement = field.unit
        self._attr_device_class = field.device_class
        self._attr_native_min_value = DEFAULT_T_TARGET_MIN
        self._attr_native_max_value = DEFAULT_T_TARGET_MAX
        self._attr_native_step = DEFAULT_T_TARGET_STEP

    @property
    def native_value(self) -> float | None:
        """Return the current setpoint."""
        return as_float(self.raw_value)

    async def async_set_native_value(self, value: float) -> None:
        """Write a new setpoint to the base."""
        await self.coordinator.async_write_device(
            (*self._field.path, self._field.tag), value
        )
