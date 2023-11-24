"""Prusalink API."""
from __future__ import annotations

from aiohttp import ClientSession
from pyprusalink.client import ApiClient
from pyprusalink.types import FileInfo, FilesInfo, JobInfo, PrinterInfo, VersionInfo


class PrusaLink:
    """Wrapper for the Prusalink API.

    Data format can be found here:
    https://github.com/prusa3d/Prusa-Firmware-Buddy/blob/master/lib/WUI/link_content/basic_gets.cpp
    """

    def __init__(self, session: ClientSession, host: str, api_key: str) -> None:
        """Initialize the PrusaLink class."""
        self.client = ApiClient.get_api_key_client(session, host, api_key)

    async def cancel_job(self) -> None:
        """Cancel the current job."""
        async with self.client.request("POST", "/api/job", {"command": "cancel"}):
            pass

    async def resume_job(self) -> None:
        """Resume a paused job."""
        async with self.client.request(
            "POST", "/api/job", {"command": "pause", "action": "resume"}
        ):
            pass

    async def pause_job(self) -> None:
        """Pause the current job."""
        async with self.client.request(
            "POST", "/api/job", {"command": "pause", "action": "pause"}
        ):
            pass

    async def get_version(self) -> VersionInfo:
        """Get the version."""
        async with self.client.request("GET", "/api/version") as response:
            return await response.json()

    async def get_printer(self) -> PrinterInfo:
        """Get the printer."""
        async with self.client.request("GET", "/api/printer") as response:
            return await response.json()

    async def get_job(self) -> JobInfo:
        """Get current job."""
        async with self.client.request("GET", "/api/job") as response:
            return await response.json()

    async def get_file(self, path: str) -> FileInfo:
        """Get specific file info."""
        async with self.client.request("GET", f"/api/files{path}") as response:
            return await response.json()

    async def get_files(self) -> FilesInfo:
        """Get all files."""
        async with self.client.request("GET", "/api/files?recursive=true") as response:
            return await response.json()

    async def get_small_thumbnail(self, path: str) -> bytes:
        """Get a small thumbnail."""
        async with self.client.request("GET", f"/thumb/s{path}") as response:
            return await response.read()

    async def get_large_thumbnail(self, path: str) -> bytes:
        """Get a large thumbnail."""
        async with self.client.request("GET", f"/thumb/l{path}") as response:
            return await response.read()
