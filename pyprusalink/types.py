from enum import Enum
from typing import NotRequired, TypedDict

"""Types of the v1 API. Source: https://github.com/prusa3d/Prusa-Link-Web/blob/master/spec/openapi.yaml"""


class PrusaLinkError(Exception):
    """Base class for PrusaLink errors."""


class InvalidAuth(PrusaLinkError):
    """Error to indicate there is invalid auth."""


class Conflict(PrusaLinkError):
    """Error to indicate the command hit a conflict."""


class NotFound(PrusaLinkError):
    """Error to indicate the requested resource was not found. (404)"""


class Capabilities(TypedDict):
    """API Capabilities"""

    upload_by_put: bool | None


class VersionInfo(TypedDict):
    """Version data from /api/version.

    Field availability differs between PrusaLink variants and firmware versions:

    Bundled PrusaLink (Prusa-Firmware-Buddy, all printers):
      Always returned: api, server, nozzle_diameter, text, hostname, capabilities
      Returned on v6.5.1+ only: firmware, printer
        - v6.5.1 (2025-11-11): added on Core One L
        - v6.5.3 (2026-03-24): propagated to Core One/MK4/MK3.9/MK3.5 family
        - XL (6.4.x track) and MINI (6.4.0): not yet backported
        - Source: https://github.com/prusa3d/Prusa-Firmware-Buddy/commit/64b7a21

    Example response from MK4 firmware 6.4.0 (no firmware/printer fields):
        {"api": "2.0.0", "server": "2.1.2", "nozzle_diameter": 0.4,
         "text": "PrusaLink", "hostname": "prusa-mk4",
         "capabilities": {"upload-by-put": True}}

    Standalone PrusaLink (RPi-based installations):
      May return version and sdk per the Prusa-Link-Web OpenAPI spec; these
      are never returned by bundled firmware.

    Use dict.get() for any field other than `api` to handle absence safely.
    """

    api: str
    text: NotRequired[str]
    server: NotRequired[str]
    hostname: NotRequired[str]
    nozzle_diameter: NotRequired[float]
    firmware: NotRequired[str]
    printer: NotRequired[str]
    version: NotRequired[str]
    sdk: NotRequired[str]
    capabilities: NotRequired[Capabilities]


class PrinterInfo(TypedDict):
    """Printer information from /api/v1/info.

    The set of fields returned varies by firmware version and printer
    model — older firmware may omit fields like `min_extrusion_temp` or
    `network_error_chime`, and a Buddy printer not in farm mode may omit
    `farm_mode`. Treat any missing key as "not reported", not
    "false/zero/empty".

    Use `dict.get()` or `key in info` rather than indexing.
    """

    mmu: NotRequired[bool]
    name: NotRequired[str]
    location: NotRequired[str]
    farm_mode: NotRequired[bool]
    nozzle_diameter: NotRequired[float]
    min_extrusion_temp: NotRequired[int]
    serial: NotRequired[str]
    sd_ready: NotRequired[bool]
    active_camera: NotRequired[bool]
    hostname: NotRequired[str]
    port: NotRequired[str]
    network_error_chime: NotRequired[bool]


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


class StatusJob(TypedDict, total=False):
    """Job summary embedded in the status response.

    All fields are optional per the OpenAPI spec.
    """

    id: int
    progress: float
    time_printing: int
    time_remaining: int


class StatusStorage(TypedDict):
    """Active storage device embedded in the status response."""

    path: str
    name: str
    read_only: bool
    free_space: NotRequired[int]


class PrinterStatus(TypedDict):
    """Printer status."""

    printer: PrinterStatusInfo
    job: NotRequired[StatusJob]
    storage: NotRequired[StatusStorage]


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


class Storage(TypedDict):
    """A storage device returned by /api/v1/storage."""

    type: str
    path: str
    available: bool
    name: NotRequired[str]
    read_only: NotRequired[bool]
    free_space: NotRequired[int]
    total_space: NotRequired[int]
    print_files: NotRequired[int]
    system_files: NotRequired[int]


class Transfer(TypedDict):
    """An active file transfer returned by /api/v1/transfer."""

    type: str
    display_name: str
    path: str
    progress: float
    transferred: int
    time_transferring: int
    to_print: bool
    id: NotRequired[int]
    url: NotRequired[str]
    size: NotRequired[str]
    time_remaining: NotRequired[int]
