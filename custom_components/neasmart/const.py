"""Constants and dataclasses for the Nea Smart integration."""

from __future__ import annotations

from dataclasses import dataclass

DOMAIN = "neasmart"
MANUFACTURER = "Nea Smart"
MODEL = "Alpha 2"

DEFAULT_PORT = 80
DEFAULT_SCAN_INTERVAL = 60
MIN_SCAN_INTERVAL = 10
MAX_SCAN_INTERVAL = 3600

DEFAULT_T_TARGET_MIN = 5.0
DEFAULT_T_TARGET_MAX = 30.0
DEFAULT_T_TARGET_STEP = 0.5

CONF_HOST = "host"
CONF_PORT = "port"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_ENABLED_ZONES = "enabled_zones"
CONF_BASE_ID = "base_id"
CONF_BASE_NAME = "base_name"
CONF_BASE_TYPE = "base_type"
CONF_FIRMWARE = "firmware"
CONF_ZONES = "zones"
CONF_ZONE_NR = "nr"
CONF_ZONE_NAME = "name"
CONF_ZONE_MIN = "min"
CONF_ZONE_MAX = "max"

PLATFORM_SENSOR = "sensor"
PLATFORM_NUMBER = "number"
PLATFORM_SELECT = "select"
PLATFORM_BINARY_SENSOR = "binary_sensor"
PLATFORM_SWITCH = "switch"

DATA_STATIC = "/data/static.xml"
DATA_DYNAMIC = "/data/dynamic.xml"
DATA_CYCLIC = "/data/cyclic.xml"
DATA_CHANGES = "/data/changes.xml"

HEATAREA_MODE_OPTIONS: dict[int, str] = {0: "Auto", 1: "Day", 2: "Night"}
RELAIS_FUNCTION_OPTIONS: dict[int, str] = {0: "Off", 1: "CO Pilot"}

INVALID_TOKENS: frozenset[str] = frozenset({"", "-", "--", "---", "----", "!"})


@dataclass(frozen=True, kw_only=True)
class HeatAreaField:
    """Describes a child element of a ``HEATAREA`` section.

    Attributes:
        tag: The XML element name, used as-is for reads and writes.
        platform: The Home Assistant platform that exposes the value.
        translation_key: Key used in ``entity.<platform>.<key>.name``.
        unit: The unit of measurement, if any.
        device_class: The Home Assistant device class, if any.
        state_class: The Home Assistant state class, if any.
        writable: Whether the value can be written back to the base.
        options: Value to label mapping for ``select`` fields.
        enabled_default: Whether the entity is enabled when first added.
    """

    tag: str
    platform: str
    translation_key: str
    unit: str | None = None
    device_class: str | None = None
    state_class: str | None = None
    writable: bool = False
    options: dict[int, str] | None = None
    enabled_default: bool = True

    @property
    def key(self) -> str:
        """Return a stable, lowercased key for unique identifiers."""
        return self.tag.lower()


@dataclass(frozen=True, kw_only=True)
class DeviceField:
    """Describes an element of the ``Device`` section, possibly nested.

    Attributes:
        tag: The XML element name, used as-is for reads and writes.
        platform: The Home Assistant platform that exposes the value.
        translation_key: Key used in ``entity.<platform>.<key>.name``.
        path: Optional container elements to walk before ``tag``.
        unit: The unit of measurement, if any.
        device_class: The Home Assistant device class, if any.
        state_class: The Home Assistant state class, if any.
        writable: Whether the value can be written back to the base.
        options: Value to label mapping for ``select`` fields.
        enabled_default: Whether the entity is enabled when first added.
    """

    tag: str
    platform: str
    translation_key: str
    path: tuple[str, ...] = ()
    unit: str | None = None
    device_class: str | None = None
    state_class: str | None = None
    writable: bool = False
    options: dict[int, str] | None = None
    enabled_default: bool = True

    @property
    def key(self) -> str:
        """Return a stable, lowercased key for unique identifiers."""
        return "_".join((*self.path, self.tag)).lower()


@dataclass(frozen=True, kw_only=True)
class Zone:
    """A logical heat area discovered in ``static.xml``.

    Attributes:
        nr: The ``nr`` attribute of the ``HEATAREA`` element.
        name: The human readable ``HEATAREA_NAME``.
        min_temperature: The lowest settable target temperature.
        max_temperature: The highest settable target temperature.
    """

    nr: int
    name: str
    min_temperature: float
    max_temperature: float


HEATAREA_FIELDS: tuple[HeatAreaField, ...] = (
    HeatAreaField(
        tag="T_ACTUAL",
        platform=PLATFORM_SENSOR,
        translation_key="t_actual",
        unit="°C",
        device_class="temperature",
        state_class="measurement",
    ),
    HeatAreaField(
        tag="T_ACTUAL_EXT",
        platform=PLATFORM_SENSOR,
        translation_key="t_actual_ext",
        unit="°C",
        device_class="temperature",
        state_class="measurement",
    ),
    HeatAreaField(
        tag="T_TARGET",
        platform=PLATFORM_NUMBER,
        translation_key="t_target",
        unit="°C",
        device_class="temperature",
        writable=True,
    ),
    HeatAreaField(
        tag="T_TARGET_BASE",
        platform=PLATFORM_SENSOR,
        translation_key="t_target_base",
        unit="°C",
        device_class="temperature",
        state_class="measurement",
    ),
    HeatAreaField(
        tag="HEATAREA_MODE",
        platform=PLATFORM_SELECT,
        translation_key="heatarea_mode",
        writable=True,
        options=HEATAREA_MODE_OPTIONS,
    ),
    HeatAreaField(
        tag="HEATAREA_STATE",
        platform=PLATFORM_BINARY_SENSOR,
        translation_key="heatarea_state",
    ),
    HeatAreaField(
        tag="PROGRAM_SOURCE",
        platform=PLATFORM_SENSOR,
        translation_key="program_source",
    ),
    HeatAreaField(
        tag="PROGRAM_WEEK",
        platform=PLATFORM_SENSOR,
        translation_key="program_week",
    ),
    HeatAreaField(
        tag="PROGRAM_WEEKEND",
        platform=PLATFORM_SENSOR,
        translation_key="program_weekend",
    ),
    HeatAreaField(
        tag="PARTY",
        platform=PLATFORM_BINARY_SENSOR,
        translation_key="party",
    ),
    HeatAreaField(
        tag="PARTY_REMAININGTIME",
        platform=PLATFORM_SENSOR,
        translation_key="party_remaining_time",
        enabled_default=False,
    ),
    HeatAreaField(
        tag="PRESENCE",
        platform=PLATFORM_BINARY_SENSOR,
        translation_key="presence",
    ),
    HeatAreaField(
        tag="ISLOCKED",
        platform=PLATFORM_BINARY_SENSOR,
        translation_key="islocked",
    ),
    HeatAreaField(
        tag="LOCK_AVAILABLE",
        platform=PLATFORM_BINARY_SENSOR,
        translation_key="lock_available",
        enabled_default=False,
    ),
    HeatAreaField(
        tag="SENSOR_EXT",
        platform=PLATFORM_BINARY_SENSOR,
        translation_key="sensor_ext",
        enabled_default=False,
    ),
)

DEVICE_FIELDS: tuple[DeviceField, ...] = (
    DeviceField(
        tag="DATETIME",
        platform=PLATFORM_SENSOR,
        translation_key="datetime",
        device_class="timestamp",
    ),
    DeviceField(
        tag="COOLING",
        platform=PLATFORM_SWITCH,
        translation_key="cooling",
        writable=True,
    ),
    DeviceField(
        tag="FUNCTION",
        path=("RELAIS",),
        platform=PLATFORM_SELECT,
        translation_key="relais_function",
        writable=True,
        options=RELAIS_FUNCTION_OPTIONS,
    ),
    DeviceField(
        tag="VACATION_STATE",
        path=("VACATION",),
        platform=PLATFORM_BINARY_SENSOR,
        translation_key="vacation_state",
    ),
    DeviceField(
        tag="T_HEAT_VACATION",
        platform=PLATFORM_NUMBER,
        translation_key="t_heat_vacation",
        unit="°C",
        device_class="temperature",
        writable=True,
    ),
    DeviceField(
        tag="ERRORCOUNT",
        platform=PLATFORM_SENSOR,
        translation_key="errorcount",
        enabled_default=False,
    ),
)
