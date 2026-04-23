"""Tests for ApiClient error handling."""

import httpx
from pyprusalink.client import ApiClient
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


def test_uses_standard_digest_auth():
    """ApiClient uses httpx.DigestAuth directly, without any subclassing."""
    async_client = httpx.AsyncClient()
    api = ApiClient(async_client, HOST, "maker", "password")
    assert type(api._auth) is httpx.DigestAuth
