"""Prusalink API."""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from aiohttp import ClientResponse, ClientSession


class PrusaLinkError(Exception):
    """Base class for PrusaLink errors."""


class InvalidAuth(PrusaLinkError):
    """Error to indicate there is invalid auth."""


class PrusaLink:
    """Wrapper for the Prusalink API.

    Data format can be found here:
    https://github.com/prusa3d/Prusa-Firmware-Buddy/blob/master/lib/WUI/link_content/basic_gets.cpp
    """

    def __init__(self, session: ClientSession, host: str, api_key: str) -> None:
        """Initialize the PrusaLink class."""
        self._session = session
        self.host = host
        self._api_key = api_key

    async def get_version(self) -> dict:
        """Get the version."""
        async with self.request("GET", "api/version") as response:
            return await response.json()

    async def get_printer(self) -> dict:
        """Get the printer."""
        async with self.request("GET", "api/printer") as response:
            return await response.json()

    async def get_job(self) -> dict:
        """Get current job."""
        async with self.request("GET", "api/job") as response:
            return await response.json()

    async def get_file(self, path) -> dict:
        """Get specific file info."""
        async with self.request("GET", f"api/files{path}") as response:
            return await response.json()

    async def get_files(self) -> dict:
        """Get all files."""
        async with self.request("GET", "api/files?recursive=true") as response:
            return await response.json()

    async def get_small_thumbnail(self, path):
        """Get a small thumbnail."""
        async with self.request("GET", f"thumb/s{path}") as response:
            return await response.read()

    async def get_large_thumbnail(self, path):
        """Get a large thumbnail."""
        async with self.request("GET", f"thumb/l{path}") as response:
            return await response.read()

    @asynccontextmanager
    async def request(
        self, method: str, path: str
    ) -> AsyncGenerator[ClientResponse, None]:
        """Make a request to the PrusaLink API."""
        url = f"{self.host}/{path}"
        headers = {"X-Api-Key": self._api_key}

        async with self._session.request(method, url, headers=headers) as response:
            if response.status == 401:
                raise InvalidAuth()

            response.raise_for_status()
            yield response
