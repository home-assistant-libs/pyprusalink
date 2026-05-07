"""Integration tests against a real PrusaLink printer.

Run with:
    PRUSALINK_HOST=http://prusa.lan \
    PRUSALINK_USERNAME=maker \
    PRUSALINK_PASSWORD=secret \
    pytest tests/test_integration.py -v -s -m integration

The `-m integration` flag is required to override the default
`-m 'not integration'` from pyproject.toml. All tests are skipped
when PRUSALINK_HOST is not set.
"""

import os

import httpx
from pyprusalink import PrusaLink
import pytest

pytestmark = pytest.mark.integration


@pytest.fixture
async def printer():
    host = os.environ.get("PRUSALINK_HOST")
    if not host:
        pytest.skip("PRUSALINK_HOST not set")
    username = os.environ.get("PRUSALINK_USERNAME", "maker")
    password = os.environ.get("PRUSALINK_PASSWORD", "")
    async with httpx.AsyncClient() as client:
        yield PrusaLink(client, host, username, password)


async def test_get_version(printer):
    result = await printer.get_version()
    assert "api" in result


async def test_get_info(printer):
    result = await printer.get_info()
    assert "serial" in result
    assert "nozzle_diameter" in result


async def test_get_status(printer):
    result = await printer.get_status()
    assert "printer" in result
    assert "state" in result["printer"]


async def test_get_job(printer):
    result = await printer.get_job()
    # Returns empty dict when no job is running — both states are valid
    assert isinstance(result, dict)
    if result:
        assert "id" in result
        assert "state" in result


async def test_get_legacy_printer(printer):
    result = await printer.get_legacy_printer()
    assert isinstance(result, dict)
