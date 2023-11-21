"""Prusalink API."""
from __future__ import annotations

from aiohttp import ClientSession
from pyprusalink.client import ApiClient
from pyprusalink.types import JobInfo, PrinterInfo, PrinterStatus, VersionInfo
from pyprusalink.types_legacy import LegacyPrinterStatus


class PrusaLink:
    """Wrapper for the Prusalink API.

    Data format can be found here:
    https://github.com/prusa3d/Prusa-Link-Web/blob/master/spec/openapi.yaml
    """

    def __init__(
        self, session: ClientSession, host: str, username: str, password: str
    ) -> None:
        """Initialize the PrusaLink class."""
        self.client = ApiClient(
            session=session, host=host, username=username, password=password
        )

    async def cancel_job(self, jobId: int) -> None:
        """Cancel the current job."""
        async with self.client.request("DELETE", f"/api/v1/job/{jobId}"):
            pass

    async def pause_job(self, jobId: int) -> None:
        """Pause a job."""
        async with self.client.request("PUT", f"/api/v1/job/{jobId}/pause"):
            pass

    async def resume_job(self, jobId: int) -> None:
        """Resume a paused job."""
        async with self.client.request("PUT", f"/api/v1/job/{jobId}/resume"):
            pass

    async def get_version(self) -> VersionInfo:
        """Get the version."""
        async with self.client.request("GET", "/api/version") as response:
            return await response.json()

    async def get_legacy_printer(self) -> LegacyPrinterStatus:
        """Get the legacy printer endpoint."""
        async with self.client.request("GET", "/api/printer") as response:
            return await response.json()

    async def get_info(self) -> PrinterInfo:
        """Get the printer."""
        async with self.client.request("GET", "/api/v1/info") as response:
            return await response.json()

    async def get_status(self) -> PrinterStatus:
        """Get the printer."""
        async with self.client.request("GET", "/api/v1/status") as response:
            return await response.json()

    async def get_job(self) -> JobInfo:
        """Get current job."""
        async with self.client.request("GET", "/api/v1/job") as response:
            # when there is no job running we'll an empty document that will fail to parse
            if response.status == 204:
                return {}
            return await response.json()

    # Prusa Link Web UI still uses the old endpoints and it seems that the new v1 endpoint doesn't support this yet
    async def get_file(self, path: str) -> bytes:
        """Get a files such as Thumbnails or Icons. Path comes from the current job['file']['refs']['thumbnail']"""
        async with self.client.request("GET", path) as response:
            return await response.read()
