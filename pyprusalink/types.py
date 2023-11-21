from enum import Enum
from typing import TypedDict

"""Types of the v1 API. Source: https://github.com/prusa3d/Prusa-Link-Web/blob/master/spec/openapi.yaml"""


class PrusaLinkError(Exception):
    """Base class for PrusaLink errors."""


class InvalidAuth(PrusaLinkError):
    """Error to indicate there is invalid auth."""


class Conflict(PrusaLinkError):
    """Error to indicate the command hit a conflict."""


class Capabilities(TypedDict):
    """API Capabilities"""

    upload_by_put: bool | None


class VersionInfo(TypedDict):
    """Version data."""

    api: str
    version: str
    printer: str
    text: str
    firmware: str
    sdk: str | None
    capabilities: Capabilities | None


class PrinterInfo(TypedDict):
    """Printer informations."""

    mmu: bool | None
    name: str | None
    location: str | None
    farm_mode: bool | None
    nozzle_diameter: float | None
    min_extrusion_temp: int | None
    serial: str | None
    sd_ready: bool | None
    active_camera: bool | None
    hostname: str | None
    port: str | None
    network_error_chime: bool | None


class StatusInfo(TypedDict):
    """Status of the printer."""

    ok: bool | None
    message: str | None


class PrinterState(Enum):
    """Printer state as Enum."""

    IDLE = "IDLE"
    BUSY = "BUSY"
    PRINTING = "PRINTING"
    PAUSED = "PAUSED"
    FINISHED = "FINISHED"
    STOPPED = "STOPPED"
    ERROR = "ERROR"
    ATTENTION = "ATTENTION"
    READY = "READY"


class PrinterStatusInfo(TypedDict):
    """Printer information."""

    state: PrinterState
    temp_nozzle: float | None
    target_nozzle: float | None
    temp_bed: float | None
    target_bed: float | None
    axis_x: float | None
    axis_y: float | None
    axis_z: float | None
    flow: int | None
    speed: int | None
    fan_hotend: int | None
    fan_print: int | None
    status_printer: StatusInfo | None
    status_connect: StatusInfo | None


class PrinterStatus(TypedDict):
    """Printer status."""

    printer: PrinterStatusInfo


class PrintFileRefs(TypedDict):
    """Additional Files for the current Job"""

    download: str | None
    icon: str | None
    thumbnail: str | None


class JobFilePrint(TypedDict):
    """Currently printed file informations."""

    name: str
    display_name: str | None
    path: str
    display_path: str | None
    size: int | None
    m_timestamp: int
    meta: dict | None
    refs: PrintFileRefs | None


class JobInfo(TypedDict):
    """Job information."""

    id: int
    state: str
    progress: int
    time_remaining: int | None
    time_printing: int
    inaccurate_estimates: bool | None
    serial_print: bool | None
    file: JobFilePrint | None
