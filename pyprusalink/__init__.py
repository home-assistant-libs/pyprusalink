"""Prusalink API."""
from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from httpx import AsyncClient, DigestAuth, Response

from .const import (
    API_KEY,
    API_KEY_AUTH,
    AUTH,
    AUTH_TYPE,
    DIGEST_AUTH,
    HOST,
    PASSWORD,
    USER,
)
from .types import (
    FileInfo,
    FilesInfo,
    JobInfo,
    LinkConfiguration,
    PrinterInfo,
    VersionInfo,
)


class PrusaLinkError(Exception):
    """Base class for PrusaLink errors."""


class InvalidAuth(PrusaLinkError):
    """Error to indicate there is invalid auth."""


class Conflict(PrusaLinkError):
    """Error to indicate the command hit a conflict."""


class PrusaLink:
    """Wrapper for the Prusalink API.

    Data format can be found here:
    https://github.com/prusa3d/Prusa-Firmware-Buddy/blob/master/lib/WUI/link_content/basic_gets.cpp
    """

    def __init__(self, client: AsyncClient, config: LinkConfiguration) -> None:
        """Initialize the PrusaLink class."""

        self.host = config[HOST]
        self.auth = config[AUTH]
        self.client = client

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
            return response.json()

    async def get_printer(self) -> PrinterInfo:
        """Get the printer."""
        async with self.request("GET", "api/printer") as response:
            return response.json()

    async def get_job(self) -> JobInfo:
        """Get current job."""
        async with self.request("GET", "api/job") as response:
            return response.json()

    async def get_file(self, path: str) -> FileInfo:
        """Get specific file info."""
        async with self.request("GET", f"api/files{path}") as response:
            return response.json()

    async def get_files(self) -> FilesInfo:
        """Get all files."""
        async with self.request("GET", "api/files?recursive=true") as response:
            return response.json()

    async def get_small_thumbnail(self, path: str) -> bytes:
        """Get a small thumbnail."""
        async with self.request("GET", f"thumb/s{path}") as response:
            return response.read()

    async def get_large_thumbnail(self, path: str) -> bytes:
        """Get a large thumbnail."""
        async with self.request("GET", f"thumb/l{path}") as response:
            return response.read()

    @asynccontextmanager
    async def request(
        self, method: str, path: str, json: dict | None = None
    ) -> AsyncGenerator[Response, None]:
        """Make a request to the PrusaLink API."""
        url = f"{self.host}/{path}"
        client = self.client

        async with client:
            if self.auth[AUTH_TYPE] == DIGEST_AUTH:
                auth = DigestAuth(self.auth[USER], self.auth[PASSWORD])
                response = await client.request(method, url, json=json, auth=auth)

            elif self.auth[AUTH_TYPE] == API_KEY_AUTH:
                headers = {"X-Api-Key": self.auth[API_KEY]}
                response = await client.request(
                    method,
                    url,
                    json=json,
                    headers=headers,
                )

            if response.status_code == 401:
                raise InvalidAuth()
            elif response.status_code == 409:
                raise Conflict()

            response.raise_for_status()

            yield response
