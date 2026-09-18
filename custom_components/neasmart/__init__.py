"""Set up the Nea Smart integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import NeaSmartClient, NeaSmartError
from .const import CONF_HOST, CONF_PORT, DEFAULT_PORT, DOMAIN
from .coordinator import NeaSmartCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

SERVICE_WRITE_ZONE = "write_zone_value"
SERVICE_WRITE_DEVICE = "write_device_value"

WRITE_ZONE_SCHEMA = vol.Schema(
    {
        vol.Optional("entry_id"): cv.string,
        vol.Required("zone"): vol.Coerce(int),
        vol.Required("tag"): cv.string,
        vol.Required("value"): vol.Any(int, float, str),
    }
)

WRITE_DEVICE_SCHEMA = vol.Schema(
    {
        vol.Optional("entry_id"): cv.string,
        vol.Required("path"): cv.string,
        vol.Required("value"): vol.Any(int, float, str),
    }
)


def _resolve_coordinator(
    hass: HomeAssistant, entry_id: str | None
) -> NeaSmartCoordinator:
    """Return the coordinator targeted by a service call.

    Args:
        hass: The Home Assistant instance.
        entry_id: An optional config entry identifier.

    Returns:
        The coordinator of the matching config entry.

    Raises:
        ServiceValidationError: If no single entry can be resolved.
    """
    if entry_id:
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry is not None and isinstance(entry.runtime_data, NeaSmartCoordinator):
            return entry.runtime_data
        raise ServiceValidationError(
            f"config entry {entry_id} is not a Nea Smart entry"
        )

    coordinators = [
        entry.runtime_data
        for entry in hass.config_entries.async_entries(DOMAIN)
        if isinstance(entry.runtime_data, NeaSmartCoordinator)
    ]
    if len(coordinators) == 1:
        return coordinators[0]
    raise ServiceValidationError(
        "entry_id is required when several Nea Smart entries are configured"
    )


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the services exposed by the integration."""

    async def _async_write_zone(call: ServiceCall) -> None:
        coordinator = _resolve_coordinator(hass, call.data.get("entry_id"))
        await coordinator.async_write_zone(
            int(call.data["zone"]),
            str(call.data["tag"]),
            call.data["value"],
        )

    async def _async_write_device(call: ServiceCall) -> None:
        coordinator = _resolve_coordinator(hass, call.data.get("entry_id"))
        path = tuple(part for part in str(call.data["path"]).split("/") if part)
        if not path:
            raise ServiceValidationError("path must name at least one element")
        await coordinator.async_write_device(path, call.data["value"])

    hass.services.async_register(
        DOMAIN, SERVICE_WRITE_ZONE, _async_write_zone, schema=WRITE_ZONE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_WRITE_DEVICE,
        _async_write_device,
        schema=WRITE_DEVICE_SCHEMA,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Nea Smart base from a config entry."""
    client = NeaSmartClient(
        async_get_clientsession(hass),
        entry.data[CONF_HOST],
        entry.data.get(CONF_PORT, DEFAULT_PORT),
    )
    coordinator = NeaSmartCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)


__all__ = [
    "CONFIG_SCHEMA",
    "PLATFORMS",
    "NeaSmartError",
    "async_setup",
    "async_setup_entry",
    "async_unload_entry",
]
