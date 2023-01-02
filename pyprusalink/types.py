from typing import TypedDict

from .const import API_KEY_AUTH, DIGEST_AUTH


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


class UserAuth(TypedDict):
    """Authentication via `user` + `password` digest"""

    type: DIGEST_AUTH
    user: str
    password: str


class ApiKeyAuth(TypedDict):
    """Authentication via api key"""

    type: API_KEY_AUTH
    apiKey: str


class LinkConfiguration(TypedDict):
    """Configuration shape for PrusaLink"""

    host: str
    auth: UserAuth | ApiKeyAuth
