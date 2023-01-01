"""Prusalink API."""
from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import TypedDict
from httpx import Response, AsyncClient, BasicAuth

API_KEY = "apiKey"
API_KEY_AUTH = "ApiKeyAuth"
AUTH = "auth"
AUTH_TYPE = "authType"
DIGEST_AUTH = "DigestAuth"
HOST = "host"
PASSWORD = "password"
USER = "user"

class PrusaLinkError(Exception):
    """Base class for PrusaLink errors."""


class InvalidAuth(PrusaLinkError):
    """Error to indicate there is invalid auth."""


class Conflict(PrusaLinkError):
    """Error to indicate the command hit a conflict."""


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

class PrusaLink:
    """Wrapper for the Prusalink API.

    Data format can be found here:
    https://github.com/prusa3d/Prusa-Firmware-Buddy/blob/master/lib/WUI/link_content/basic_gets.cpp
    """

    def __init__(self, client: AsyncClient, config: LinkConfiguration) -> None:
        """Initialize the PrusaLink class."""

        print("pyprusalink config:", config)

        self.host = config[HOST]
        self.client = client
        self.auth = config[AUTH]

    async def cancel_job(self) -> None:
        """Cancel the current job."""
        async with self.request("POST", "api/job", {"command": "cancel"}):
            pass

    async def resume_job(self) -> None:
        """Resume a paused job."""
        async with self.request(
            "POST", "api/job", {"command": "pause", "action": "resume"}
        ):
            pass

    async def pause_job(self) -> None:
        """Pause the current job."""
        async with self.request(
            "POST", "api/job", {"command": "pause", "action": "pause"}
        ):
            pass

    async def get_version(self) -> VersionInfo:
        """Get the version."""
        async with self.request("GET", "api/version") as response:
            return await response.json()

    async def get_printer(self) -> PrinterInfo:
        """Get the printer."""
        async with self.request("GET", "api/printer") as response:
            return await response.json()

    async def get_job(self) -> JobInfo:
        """Get current job."""
        async with self.request("GET", "api/job") as response:
            return await response.json()

    async def get_file(self, path: str) -> FileInfo:
        """Get specific file info."""
        async with self.request("GET", f"api/files{path}") as response:
            return await response.json()

    async def get_files(self) -> FilesInfo:
        """Get all files."""
        async with self.request("GET", "api/files?recursive=true") as response:
            return await response.json()

    async def get_small_thumbnail(self, path: str) -> bytes:
        """Get a small thumbnail."""
        async with self.request("GET", f"thumb/s{path}") as response:
            return await response.read()

    async def get_large_thumbnail(self, path: str) -> bytes:
        """Get a large thumbnail."""
        async with self.request("GET", f"thumb/l{path}") as response:
            return await response.read()

    @asynccontextmanager
    async def request(
        self, method: str, path: str, json: dict | None = None
    ) -> AsyncGenerator[Response, None]:
        """Make a request to the PrusaLink API."""
        url = f"{self.host}/{path}"

        auth = None
        if self.auth[AUTH_TYPE] == DIGEST_AUTH:
            auth = BasicAuth(self.auth[USER], self.auth[PASSWORD])

        headers = {}
        if self.auth[AUTH_TYPE] == API_KEY_AUTH:
            headers = {"X-Api-Key": self.auth[API_KEY]}

        client = self.client
        async with client:
            response = await client.request(
                method, url, json=json, auth=auth, headers=headers, 
            )

            print('pyprusalink response:')
            print(response)
            if response.status == 401:
                raise InvalidAuth()
            if response.status == 409:
                raise Conflict()
            response.raise_for_status()

            yield response
