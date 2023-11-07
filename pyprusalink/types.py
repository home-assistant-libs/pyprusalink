from typing import TypedDict, Optional
from enum import Enum

"""Types of the v1 API. Source: https://github.com/prusa3d/Prusa-Link-Web/blob/master/spec/openapi.yaml"""


class PrusaLinkError(Exception):
    """Base class for PrusaLink errors."""


class InvalidAuth(PrusaLinkError):
    """Error to indicate there is invalid auth."""


class Conflict(PrusaLinkError):
    """Error to indicate the command hit a conflict."""


class Capabilities(TypedDict):
    """API Capabilities"""

    upload_by_put: Optional[bool]


class VersionInfo(TypedDict):
    """Version data."""

    api: str
    version: str
    printer: str
    text: str
    firmware: str
    sdk: Optional[str]
    capabilities: Optional[Capabilities]


class PrinterInfo(TypedDict):
    """Printer informations."""

    mmu: Optional[bool]
    name: Optional[str]
    location: Optional[str]
    farm_mode: Optional[bool]
    nozzle_diameter: Optional[float]
    min_extrusion_temp: Optional[int]
    serial: Optional[str]
    sd_ready: Optional[bool]
    active_camera: Optional[bool]
    hostname: Optional[str]
    port: Optional[str]
    network_error_chime: Optional[bool]


class StatusInfo(TypedDict):
    """Status of the printer."""

    ok: Optional[bool]
    message: Optional[str]


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
    temp_nozzle: Optional[float]
    target_nozzle: Optional[float]
    temp_bed: Optional[float]
    target_bed: Optional[float]
    axis_x: Optional[float]
    axis_y: Optional[float]
    axis_z: Optional[float]
    flow: Optional[int]
    speed: Optional[int]
    fan_hotend: Optional[int]
    fan_print: Optional[int]
    status_printer: Optional[StatusInfo]
    status_connect: Optional[StatusInfo]


class PrinterStatus(TypedDict):
    """Printer status."""

    printer: PrinterStatusInfo


class PrintFileRefs(TypedDict):
    """Additional Files for the current Job"""

    download: Optional[str]
    icon: Optional[str]
    thumbnail: Optional[str]


class JobFilePrint(TypedDict):
    """Currently printed file informations."""

    name: str
    display_name: Optional[str]
    path: str
    display_path: Optional[str]
    size: Optional[int]
    m_timestamp: int
    meta: Optional[dict]
    refs: Optional[PrintFileRefs]


class JobInfo(TypedDict):
    """Job information."""

    id: int
    state: str
    progress: int
    time_remaining: Optional[int]
    time_printing: int
    inaccurate_estimates: Optional[bool]
    serial_print: Optional[bool]
    file: Optional[JobFilePrint]
