"""Switch platform for the Nea Smart integration."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DEVICE_FIELDS,
    PLATFORM_SWITCH,
    DeviceField,
)
from .coordinator import NeaSmartCoordinator
from .entity import NeaSmartDeviceEntity, as_int


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switches declared by the integration."""
    coordinator: NeaSmartCoordinator = entry.runtime_data
    async_add_entities(
        NeaSmartDeviceSwitch(coordinator, entry, field)
        for field in DEVICE_FIELDS
        if field.platform == PLATFORM_SWITCH
    )


class NeaSmartDeviceSwitch(NeaSmartDeviceEntity, SwitchEntity):
    """A boolean setting of the base itself."""

    def __init__(
        self,
        coordinator: NeaSmartCoordinator,
        entry: ConfigEntry,
        field: DeviceField,
    ) -> None:
        """Initialise the switch for one device level field."""
        super().__init__(coordinator, entry, field)
        self._attr_device_class = field.device_class

    @property
    def is_on(self) -> bool | None:
        """Return whether the setting is enabled."""
        code = as_int(self.raw_value)
        if code is None:
            return None
        return code != 0

    async def async_turn_on(self, **kwargs: object) -> None:
        """Enable the setting on the base."""
        await self.coordinator.async_write_device(
            (*self._field.path, self._field.tag), 1
        )

    async def async_turn_off(self, **kwargs: object) -> None:
        """Disable the setting on the base."""
        await self.coordinator.async_write_device(
            (*self._field.path, self._field.tag), 0
        )
