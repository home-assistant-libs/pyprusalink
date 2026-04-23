"""Shared test fixtures."""

import httpx
from pyprusalink import PrusaLink
import pytest

HOST = "http://printer.local"


@pytest.fixture
def prusalink(respx_mock):
    """Return a PrusaLink instance backed by a mocked HTTP transport."""
    client = httpx.AsyncClient()
    return PrusaLink(client, HOST, "maker", "password")
