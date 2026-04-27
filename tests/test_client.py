"""Tests for ApiClient error handling and DigestAuthWorkaround."""

from unittest.mock import MagicMock, patch

import httpx
from httpx import DigestAuth
from pyprusalink.client import DigestAuthWorkaround
from pyprusalink.types import Conflict, InvalidAuth, NotFound
import pytest

HOST = "http://printer.local"


async def test_invalid_auth_raises(pl, respx_mock):
    """A 401 response raises InvalidAuth."""
    respx_mock.get(f"{HOST}/api/v1/status").mock(return_value=httpx.Response(401))
    with pytest.raises(InvalidAuth):
        await pl.get_status()


async def test_conflict_raises(pl, respx_mock):
    """A 409 response raises Conflict."""
    respx_mock.delete(f"{HOST}/api/v1/job/1").mock(return_value=httpx.Response(409))
    with pytest.raises(Conflict):
        await pl.cancel_job(1)


async def test_not_found_raises(pl, respx_mock):
    """A 404 response raises NotFound."""
    respx_mock.delete(f"{HOST}/api/v1/job/1").mock(return_value=httpx.Response(404))
    with pytest.raises(NotFound):
        await pl.cancel_job(1)


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

    with patch.object(
        DigestAuth, "_build_auth_header", return_value="Digest mocked=value"
    ) as mock:
        result = auth._build_auth_header(request, challenge)
        mock.assert_called_once_with(request, challenge)

    assert result == "Digest mocked=value"
