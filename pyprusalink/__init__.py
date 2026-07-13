"""Prusalink API."""

from __future__ import annotations

from typing import cast

from httpx import AsyncClient
from pyprusalink.client import ApiClient
from pyprusalink.file_metadata import parse_file_metadata
from pyprusalink.types import (
    FileTooLarge,
    JobInfo,
    PrinterInfo,
    PrinterStatus,
    PrintFileMetadata,
    Storage,
    Transfer,
    VersionInfo,
)
from pyprusalink.types_legacy import LegacyPrinterStatus

MAX_FILE_METADATA_BYTES = 16 * 1024 * 1024


class PrusaLink:
    """Wrapper for the Prusalink API.

    Data format can be found here:
    https://github.com/prusa3d/Prusa-Link-Web/blob/master/spec/openapi.yaml
    """

    def __init__(
        self, async_client: AsyncClient, host: str, username: str, password: str
    ) -> None:
        """Initialize the PrusaLink class."""
        self.client = ApiClient(
            async_client=async_client, host=host, username=username, password=password
        )

    async def cancel_job(self, job_id: int) -> None:
        """Cancel the current job."""
        async with self.client.request("DELETE", f"/api/v1/job/{job_id}"):
            pass

    async def pause_job(self, job_id: int) -> None:
        """Pause a job."""
        async with self.client.request("PUT", f"/api/v1/job/{job_id}/pause"):
            pass

    async def resume_job(self, job_id: int) -> None:
        """Resume a paused job."""
        async with self.client.request("PUT", f"/api/v1/job/{job_id}/resume"):
            pass

    async def continue_job(self, job_id: int) -> None:
        """Continue a job after a timelapse capture."""
        async with self.client.request("PUT", f"/api/v1/job/{job_id}/continue"):
            pass

    async def get_version(self) -> VersionInfo:
        """Get the version."""
        async with self.client.request("GET", "/api/version") as response:
            return cast(VersionInfo, response.json())

    async def get_legacy_printer(self) -> LegacyPrinterStatus:
        """Get the legacy printer endpoint."""
        async with self.client.request("GET", "/api/printer") as response:
            return cast(LegacyPrinterStatus, response.json())

    async def get_info(self) -> PrinterInfo:
        """Get the printer."""
        async with self.client.request("GET", "/api/v1/info") as response:
            return cast(PrinterInfo, response.json())

    async def get_status(self) -> PrinterStatus:
        """Get the printer."""
        async with self.client.request("GET", "/api/v1/status") as response:
            return cast(PrinterStatus, response.json())

    async def get_job(self) -> JobInfo | None:
        """Get current job. Returns None when no job is running."""
        async with self.client.request("GET", "/api/v1/job") as response:
            if response.status_code == 204:
                return None
            return cast(JobInfo, response.json())

    async def get_storage(self) -> list[Storage]:
        """Get available storage devices."""
        async with self.client.request("GET", "/api/v1/storage") as response:
            return cast(list[Storage], response.json()["storage_list"])

    async def get_transfer(self) -> Transfer | None:
        """Get active transfer. Returns None when no transfer is in progress."""
        async with self.client.request("GET", "/api/v1/transfer") as response:
            if response.status_code == 204:
                return None
            return cast(Transfer, response.json())

    async def cancel_transfer(self, transfer_id: int) -> None:
        """Cancel the transfer with the given id."""
        async with self.client.request("DELETE", f"/api/v1/transfer/{transfer_id}"):
            pass

    # Prusa Link Web UI still uses the old endpoints and it seems that the new v1 endpoint doesn't support this yet
    async def get_file(self, path: str) -> bytes:
        """Get a files such as Thumbnails or Icons. Path comes from the current job['file']['refs']['thumbnail']"""
        async with self.client.request("GET", path) as response:
            return await response.aread()

    async def get_file_metadata(
        self, path: str, max_bytes: int = MAX_FILE_METADATA_BYTES
    ) -> PrintFileMetadata:
        """Get known metadata from a print file."""
        downloaded = bytearray()

        async with self.client.stream_request("GET", path) as response:
            if content_length := response.headers.get("content-length"):
                try:
                    expected_size = int(content_length)
                except ValueError:
                    expected_size = None

                if expected_size is not None and expected_size > max_bytes:
                    raise FileTooLarge(
                        f"File {path} is {expected_size} bytes, "
                        f"maximum is {max_bytes} bytes"
                    )

            async for chunk in response.aiter_bytes():
                if len(downloaded) + len(chunk) > max_bytes:
                    raise FileTooLarge(f"File {path} is larger than {max_bytes} bytes")

                downloaded.extend(chunk)

        return parse_file_metadata(bytes(downloaded))
