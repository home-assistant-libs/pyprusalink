from typing import TypedDict

"""Types of the non-versioned API. Source: https://github.com/prusa3d/Prusa-Firmware-Buddy/blob/v4.4.1/lib/WUI/link_content/basic_gets.cpp"""


class VersionInfo(TypedDict):
    """Version data."""

    api: str
    server: str
    text: str
    hostname: str


class PrinterInfo(TypedDict):
    """Printer data."""

    telemetry: dict
    temperature: dict
    state: dict


class JobInfo(TypedDict):
    """Job data."""

    state: str
    job: dict | None


class FileInfo(TypedDict):
    """File data."""

    name: str
    origin: str
    size: int
    refs: dict


class FilesInfo(TypedDict):
    """Files data."""

    files: list[FileInfo]
