"""Config and options flow for the Nea Smart integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    NeaSmartApiError,
    NeaSmartClient,
    NeaSmartConnectionError,
    build_zones,
)
from .const import (
    CONF_BASE_ID,
    CONF_BASE_NAME,
    CONF_BASE_TYPE,
    CONF_ENABLED_ZONES,
    CONF_FIRMWARE,
    CONF_HOST,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_ZONES,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


def _normalise_host(value: str) -> str:
    """Strip a scheme and trailing slash from a host typed by the user."""
    host = value.strip()
    for prefix in ("http://", "https://"):
        if host.lower().startswith(prefix):
            host = host[len(prefix) :]
    return host.rstrip("/")


async def _probe(hass: HomeAssistant, host: str, port: int) -> dict[str, Any]:
    """Read ``static.xml`` once to validate a candidate host."""
    client = NeaSmartClient(async_get_clientsession(hass), host, port)
    return await client.async_get_static()


class NeaSmartConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial configuration of a base."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the address of the base and validate it."""
        errors: dict[str, str] = {}
        if user_input is not None:
            host = _normalise_host(user_input[CONF_HOST])
            port = int(user_input.get(CONF_PORT) or DEFAULT_PORT)
            try:
                document = await _probe(self.hass, host, port)
            except NeaSmartConnectionError:
                errors["base"] = "cannot_connect"
            except NeaSmartApiError:
                errors["base"] = "invalid_response"
            except Exception:
                _LOGGER.exception("unexpected error while probing %s", host)
                errors["base"] = "unknown"
            else:
                device = document.get("device", {})
                base_id = str(device.get("ID") or host)
                await self.async_set_unique_id(base_id.lower())
                self._abort_if_unique_id_configured()
                name = device.get("NAME") or f"Nea Smart ({host})"
                return self.async_create_entry(
                    title=str(name),
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                        CONF_BASE_ID: base_id,
                        CONF_BASE_NAME: device.get("NAME"),
                        CONF_BASE_TYPE: device.get("TYPE"),
                        CONF_FIRMWARE: device.get("VERS_SW_STM")
                        or device.get("VERS_SW_ETH"),
                        CONF_ZONES: build_zones(device, document.get("heatareas", {})),
                    },
                )

        return self.async_show_form(
            step_id="user", data_schema=self._schema(), errors=errors
        )

    @staticmethod
    def _schema() -> vol.Schema:
        """Return the schema of the user step."""
        return vol.Schema(
            {
                vol.Required(CONF_HOST): selector.TextSelector(),
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=65535,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
            }
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow of this integration."""
        return NeaSmartOptionsFlow()


class NeaSmartOptionsFlow(OptionsFlow):
    """Handle the options of an existing base."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show the options menu."""
        return self.async_show_menu(step_id="init", menu_options=["settings", "zones"])

    async def async_step_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Edit the polling interval."""
        if user_input is not None:
            options = {
                **self.config_entry.options,
                CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL]),
            }
            return self.async_create_entry(title="", data=options)

        current = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL, default=current
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=MIN_SCAN_INTERVAL,
                        max=MAX_SCAN_INTERVAL,
                        unit_of_measurement="s",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                )
            }
        )
        return self.async_show_form(step_id="settings", data_schema=schema)

    async def async_step_zones(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose which heat areas are exposed."""
        zones = self.config_entry.data.get(CONF_ZONES, [])
        if user_input is not None:
            options = {
                **self.config_entry.options,
                CONF_ENABLED_ZONES: list(user_input[CONF_ENABLED_ZONES]),
            }
            return self.async_create_entry(title="", data=options)

        current = self.config_entry.options.get(CONF_ENABLED_ZONES)
        if current is None:
            default = [str(zone["nr"]) for zone in zones]
        else:
            default = [str(value) for value in current]
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_ENABLED_ZONES, default=default
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(
                                value=str(zone["nr"]), label=zone["name"]
                            )
                            for zone in zones
                        ],
                        multiple=True,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                )
            }
        )
        return self.async_show_form(step_id="zones", data_schema=schema)
