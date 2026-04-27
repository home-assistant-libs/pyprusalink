"""Shared test fixtures."""

import httpx
from pyprusalink import PrusaLink
import pytest

HOST = "http://printer.local"


@pytest.fixture
async def pl(respx_mock):
    """Return a PrusaLink instance backed by a mocked HTTP transport."""
    async with httpx.AsyncClient() as client:
        yield PrusaLink(client, HOST, "maker", "password")
