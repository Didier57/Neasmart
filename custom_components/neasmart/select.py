"""Select platform for the Nea Smart integration."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DEVICE_FIELDS,
    HEATAREA_FIELDS,
    PLATFORM_SELECT,
    DeviceField,
    HeatAreaField,
    Zone,
)
from .coordinator import NeaSmartCoordinator
from .entity import NeaSmartDeviceEntity, NeaSmartZoneEntity, as_int


def _labels(field: HeatAreaField | DeviceField) -> list[str]:
    """Return the ordered labels declared by a select field."""
    return list((field.options or {}).values())


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the enumerations declared by the integration."""
    coordinator: NeaSmartCoordinator = entry.runtime_data
    entities: list[SelectEntity] = []
    for zone in coordinator.zones.values():
        if not coordinator.is_zone_enabled(zone.nr):
            continue
        entities.extend(
            NeaSmartZoneSelect(coordinator, entry, zone, field)
            for field in HEATAREA_FIELDS
            if field.platform == PLATFORM_SELECT
        )
    entities.extend(
        NeaSmartDeviceSelect(coordinator, entry, field)
        for field in DEVICE_FIELDS
        if field.platform == PLATFORM_SELECT
    )
    async_add_entities(entities)


class NeaSmartZoneSelect(NeaSmartZoneEntity, SelectEntity):
    """An enumeration that can be written back to a heat area."""

    def __init__(
        self,
        coordinator: NeaSmartCoordinator,
        entry: ConfigEntry,
        zone: Zone,
        field: HeatAreaField,
    ) -> None:
        """Initialise the select for one heat area field."""
        super().__init__(coordinator, entry, zone, field)
        self._attr_options = _labels(field)

    @property
    def current_option(self) -> str | None:
        """Return the label matching the last reported code."""
        code = as_int(self.raw_value)
        if code is None:
            return None
        return (self._field.options or {}).get(code)

    async def async_select_option(self, option: str) -> None:
        """Write the code matching ``option`` to the base."""
        for code, label in (self._field.options or {}).items():
            if label == option:
                await self.coordinator.async_write_zone(
                    self._zone.nr, self._field.tag, code
                )
                return


class NeaSmartDeviceSelect(NeaSmartDeviceEntity, SelectEntity):
    """An enumeration that can be written back to the base itself."""

    def __init__(
        self,
        coordinator: NeaSmartCoordinator,
        entry: ConfigEntry,
        field: DeviceField,
    ) -> None:
        """Initialise the select for one device level field."""
        super().__init__(coordinator, entry, field)
        self._attr_options = _labels(field)

    @property
    def current_option(self) -> str | None:
        """Return the label matching the last reported code."""
        code = as_int(self.raw_value)
        if code is None:
            return None
        return (self._field.options or {}).get(code)

    async def async_select_option(self, option: str) -> None:
        """Write the code matching ``option`` to the base."""
        for code, label in (self._field.options or {}).items():
            if label == option:
                await self.coordinator.async_write_device(
                    (*self._field.path, self._field.tag), code
                )
                return
