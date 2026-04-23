"""Tests for ApiClient error handling and DigestAuthWorkaround."""

from unittest.mock import MagicMock

import httpx
from pyprusalink import PrusaLink
from pyprusalink.client import DigestAuthWorkaround
from pyprusalink.types import Conflict, InvalidAuth, NotFound
import pytest

HOST = "http://printer.local"


async def test_invalid_auth_raises(respx_mock):
    """A 401 response without a Digest challenge raises InvalidAuth."""
    respx_mock.get(f"{HOST}/api/v1/status").mock(return_value=httpx.Response(401))
    async with httpx.AsyncClient() as client:
        with pytest.raises(InvalidAuth):
            await PrusaLink(client, HOST, "maker", "password").get_status()


async def test_conflict_raises(respx_mock):
    """A 409 response raises Conflict."""
    respx_mock.delete(f"{HOST}/api/v1/job/1").mock(return_value=httpx.Response(409))
    async with httpx.AsyncClient() as client:
        with pytest.raises(Conflict):
            await PrusaLink(client, HOST, "maker", "password").cancel_job(1)


async def test_not_found_raises(respx_mock):
    """A 404 response raises NotFound."""
    respx_mock.delete(f"{HOST}/api/v1/job/1").mock(return_value=httpx.Response(404))
    async with httpx.AsyncClient() as client:
        with pytest.raises(NotFound):
            await PrusaLink(client, HOST, "maker", "password").cancel_job(1)


def test_digest_workaround_omits_algorithm_without_qop():
    """When the server sends no qop, the Authorization header must not include algorithm.

    Old Prusa firmware (< 5.2.0) rejects Digest headers that contain an unquoted
    algorithm parameter. The workaround builds the header manually in that case.
    """
    auth = DigestAuthWorkaround(username="maker", password="password")

    challenge = MagicMock()
    challenge.qop = None
    challenge.realm = b"Printer API"
    challenge.nonce = b"testnonce123"

    request = MagicMock()
    request.url.raw_path = b"/api/version"
    request.method = "GET"

    header = auth._build_auth_header(request, challenge)

    assert header.startswith("Digest ")
    assert "algorithm" not in header.lower()


def test_digest_workaround_delegates_to_parent_with_qop():
    """When qop is present the workaround delegates to the standard httpx implementation."""
    auth = DigestAuthWorkaround(username="maker", password="password")

    challenge = MagicMock()
    challenge.qop = b"auth"

    request = MagicMock()

    # Parent's _build_auth_header is called when qop is not None.
    # We verify this by patching the parent and checking it was invoked.
    called_with = {}

    original = DigestAuthWorkaround.__bases__[0]._build_auth_header

    def spy(self, req, chal):
        called_with["req"] = req
        called_with["chal"] = chal
        return "Digest mocked=value"

    DigestAuthWorkaround.__bases__[0]._build_auth_header = spy
    try:
        result = auth._build_auth_header(request, challenge)
    finally:
        DigestAuthWorkaround.__bases__[0]._build_auth_header = original

    assert called_with["req"] is request
    assert called_with["chal"] is challenge
    assert result == "Digest mocked=value"
