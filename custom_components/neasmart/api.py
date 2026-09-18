"""Asynchronous client for the Nea Smart (Alpha 2) XML interface."""

from __future__ import annotations

import asyncio
import logging
from typing import Any
from xml.etree import ElementTree as ET

import aiohttp

from .const import (
    DATA_CHANGES,
    DATA_CYCLIC,
    DATA_DYNAMIC,
    DATA_STATIC,
    DEFAULT_T_TARGET_MAX,
    DEFAULT_T_TARGET_MIN,
    INVALID_TOKENS,
)

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = 15

_ANSWER_ERROR_TAGS = frozenset({"ERROR", "ERRCODE", "FAULT", "ERRORMESSAGE"})
_CONTAINER_TAGS = frozenset(
    {
        "NETWORK",
        "CLOUD",
        "KWLCTRL",
        "CODE",
        "PROGRAM",
        "PUMP_OUTPUT",
        "RELAIS",
        "EMERGENCYMODE",
        "VALVEPROTECT",
        "PUMPPROTECT",
        "VACATION",
    }
)
_REPEATED_TAGS = frozenset({"HEATCTRL", "IODEVICE"})


class NeaSmartError(Exception):
    """Base class for every error raised by this integration."""


class NeaSmartConnectionError(NeaSmartError):
    """Raised when the base cannot be reached."""


class NeaSmartApiError(NeaSmartError):
    """Raised when the base answers with an unusable or rejected payload."""


def parse_float(value: Any) -> float | None:
    """Return ``value`` as a float, or ``None`` when it is not a number."""
    if value is None:
        return None
    text = str(value).strip()
    if text in INVALID_TOKENS:
        return None
    try:
        return float(text.replace(",", "."))
    except ValueError:
        return None


def parse_int(value: Any) -> int | None:
    """Return ``value`` as an int, or ``None`` when it is not a number."""
    number = parse_float(value)
    if number is None:
        return None
    return int(number)


def _clean(value: Any) -> str | None:
    """Return a stripped string, treating placeholder tokens as missing."""
    if value is None:
        return None
    text = str(value).strip()
    if text in INVALID_TOKENS:
        return None
    return text


def _parse_leaves(element: ET.Element, target: dict[str, Any]) -> dict[str, Any]:
    """Copy the direct children of ``element`` into ``target``."""
    for child in element:
        if len(child):
            target[child.tag] = _parse_leaves(child, {})
        else:
            target[child.tag] = _clean(child.text)
    return target


def _parse_device(device: ET.Element) -> dict[str, Any]:
    """Parse a ``Device`` element into a plain dictionary."""
    document: dict[str, Any] = {"device": {}, "heatareas": {}}
    globals_: dict[str, Any] = document["device"]
    heatareas: dict[int, dict[str, Any]] = document["heatareas"]

    for child in device:
        tag = child.tag
        if tag == "HEATAREA":
            try:
                nr = int(child.get("nr", ""))
            except ValueError:
                _LOGGER.debug("ignoring HEATAREA without a valid nr attribute")
                continue
            heatareas[nr] = _parse_leaves(child, {})
        elif tag in _REPEATED_TAGS:
            entry = _parse_leaves(child, {})
            entry["NR"] = child.get("nr")
            globals_.setdefault(tag, []).append(entry)
        elif tag in _CONTAINER_TAGS:
            globals_[tag] = _parse_leaves(child, {})
        else:
            globals_[tag] = _clean(child.text)

    return document


def parse_document(text: str) -> dict[str, Any]:
    """Parse a state document (static, dynamic or cyclic) into a dictionary.

    Args:
        text: The raw XML returned by the base.

    Returns:
        A mapping with a ``device`` dictionary and a ``heatareas`` dictionary
        keyed by the ``nr`` attribute.

    Raises:
        NeaSmartApiError: If the payload is not valid XML or has no ``Device``.
    """
    try:
        root = ET.fromstring(text)
    except ET.ParseError as err:
        raise NeaSmartApiError(f"invalid XML payload: {err}") from err

    device = root.find("Device")
    if device is None:
        raise NeaSmartApiError("the payload does not contain a <Device> element")
    return _parse_device(device)


def build_zones(
    device: dict[str, Any], heatareas: dict[int, dict[str, Any]]
) -> list[dict[str, Any]]:
    """Build the serialisable zone metadata stored in the config entry.

    Args:
        device: The parsed ``Device`` section.
        heatareas: The parsed ``HEATAREA`` sections keyed by ``nr``.

    Returns:
        A list of dictionaries with the ``nr``, ``name`` and target limits.
    """
    zones: list[dict[str, Any]] = []
    for nr in sorted(heatareas):
        values = heatareas[nr]
        name = (
            _clean(values.get("HEATAREA_NAME"))
            or f"{device.get('NAME') or 'Zone'} {nr}"
        )
        min_temperature = parse_float(values.get("T_TARGET_MIN"))
        max_temperature = parse_float(values.get("T_TARGET_MAX"))
        zones.append(
            {
                "nr": nr,
                "name": name,
                "min": min_temperature
                if min_temperature is not None
                else DEFAULT_T_TARGET_MIN,
                "max": max_temperature
                if max_temperature is not None
                else DEFAULT_T_TARGET_MAX,
            }
        )
    return zones


def _format_value(value: Any) -> str:
    """Render a Python value the way the base expects it in a command."""
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f"{value:g}"
    return str(value)


def _command_template(base_id: str) -> ET.Element:
    """Create a ``Devices/Device/ID`` skeleton ready to receive a command."""
    root = ET.Element("Devices")
    device = ET.SubElement(root, "Device")
    ET.SubElement(device, "ID").text = base_id
    return root


def _serialise(root: ET.Element) -> bytes:
    """Serialise a command tree to a UTF-8 XML document."""
    xml = ET.tostring(root, encoding="unicode")
    return f'<?xml version="1.0" encoding="utf-8"?>\n{xml}'.encode()


def _check_answer(text: str) -> None:
    """Raise when the answer payload reports an error.

    The exact answer schema is not documented, so the check is deliberately
    lenient: an empty body or an unparsable body is accepted, and only an
    explicit error element with a non-zero value is rejected.
    """
    if not text or not text.strip():
        return
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return
    for element in root.iter():
        if element.tag.upper() not in _ANSWER_ERROR_TAGS:
            continue
        value = (element.text or "").strip()
        if value and value not in {"0", "OK", "NONE"}:
            raise NeaSmartApiError(f"the base rejected the command: {value}")


class NeaSmartClient:
    """Talk to the XML interface of a single Alpha 2 base."""

    def __init__(self, session: aiohttp.ClientSession, host: str, port: int) -> None:
        """Initialise the client.

        Args:
            session: The shared aiohttp session.
            host: The IP address or DNS name of the base.
            port: The TCP port of the embedded web server.
        """
        self._session = session
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"

    async def _async_get(self, path: str) -> str:
        """Fetch a state document and return its raw body."""
        url = f"{self.base_url}{path}"
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                async with self._session.get(url) as response:
                    if response.status != 200:
                        raise NeaSmartApiError(
                            f"GET {path} returned HTTP {response.status}"
                        )
                    return await response.text()
        except TimeoutError as err:
            raise NeaSmartConnectionError(f"GET {path} timed out") from err
        except aiohttp.ClientError as err:
            raise NeaSmartConnectionError(str(err)) from err

    async def async_get_static(self) -> dict[str, Any]:
        """Read and parse ``static.xml``."""
        return parse_document(await self._async_get(DATA_STATIC))

    async def async_get_dynamic(self) -> dict[str, Any]:
        """Read and parse ``dynamic.xml``."""
        return parse_document(await self._async_get(DATA_DYNAMIC))

    async def async_get_cyclic(self) -> dict[str, Any]:
        """Read and parse ``cyclic.xml``."""
        return parse_document(await self._async_get(DATA_CYCLIC))

    async def _async_post(self, root: ET.Element) -> None:
        """Post a command tree to ``changes.xml`` and check the answer."""
        url = f"{self.base_url}{DATA_CHANGES}"
        payload = _serialise(root)
        headers = {"Content-Type": "text/xml; charset=utf-8"}
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                async with self._session.post(
                    url, data=payload, headers=headers
                ) as response:
                    body = await response.text()
                    if response.status != 200:
                        raise NeaSmartApiError(
                            f"POST {DATA_CHANGES} returned HTTP {response.status}"
                        )
        except TimeoutError as err:
            raise NeaSmartConnectionError("the command timed out") from err
        except aiohttp.ClientError as err:
            raise NeaSmartConnectionError(str(err)) from err
        _check_answer(body)

    async def async_write_heatarea(
        self, base_id: str, nr: int, tag: str, value: Any
    ) -> None:
        """Write a single value inside a ``HEATAREA`` section.

        Args:
            base_id: The unique base identifier read from ``static.xml``.
            nr: The ``nr`` attribute of the target heat area.
            tag: The XML element to write.
            value: The value to send, converted to text.
        """
        root = _command_template(base_id)
        device = root.find("Device")
        if device is None:  # pragma: no cover - the template always has one
            raise NeaSmartApiError("internal command template is malformed")
        heatarea = ET.SubElement(device, "HEATAREA", {"nr": str(nr)})
        ET.SubElement(heatarea, tag).text = _format_value(value)
        await self._async_post(root)

    async def async_write_device(
        self, base_id: str, path: tuple[str, ...], value: Any
    ) -> None:
        """Write a single value at device level, walking a nested path.

        Args:
            base_id: The unique base identifier read from ``static.xml``.
            path: The element names leading to the value, the last one being
                the element that receives ``value`` (for example
                ``("RELAIS", "FUNCTION")``).
            value: The value to send, converted to text.
        """
        root = _command_template(base_id)
        parent = root.find("Device")
        if parent is None:  # pragma: no cover - the template always has one
            raise NeaSmartApiError("internal command template is malformed")
        for name in path[:-1]:
            parent = ET.SubElement(parent, name)
        ET.SubElement(parent, path[-1]).text = _format_value(value)
        await self._async_post(root)
