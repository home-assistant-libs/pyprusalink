"""Happy-path tests for PrusaLink public API methods."""

import httpx

HOST = "http://printer.local"


async def test_get_version(pl, respx_mock):
    respx_mock.get(f"{HOST}/api/version").mock(
        return_value=httpx.Response(
            200,
            json={
                "api": "2.0.0",
                "version": "0.7.0",
                "printer": "1.3.1",
                "text": "PrusaLink 0.7.0",
                "firmware": "3.10.1-4697",
            },
        )
    )
    result = await pl.get_version()
    assert result["api"] == "2.0.0"
    assert result["firmware"] == "3.10.1-4697"


async def test_get_info(pl, respx_mock):
    respx_mock.get(f"{HOST}/api/v1/info").mock(
        return_value=httpx.Response(
            200,
            json={
                "mmu": False,
                "name": "MuadDib",
                "location": "Arrakis",
                "farm_mode": False,
                "nozzle_diameter": 0.4,
                "min_extrusion_temp": 170,
                "serial": "CZPX4720X004XC34242",
                "sd_ready": True,
                "active_camera": False,
                "hostname": "prusa.lan",
                "port": "/dev/tty",
                "network_error_chime": False,
            },
        )
    )
    result = await pl.get_info()
    assert result["name"] == "MuadDib"
    assert result["serial"] == "CZPX4720X004XC34242"
    assert result["nozzle_diameter"] == 0.4


async def test_get_status(pl, respx_mock):
    respx_mock.get(f"{HOST}/api/v1/status").mock(
        return_value=httpx.Response(
            200,
            json={
                "printer": {
                    "state": "PRINTING",
                    "temp_nozzle": 214.9,
                    "target_nozzle": 215.0,
                    "temp_bed": 59.5,
                    "target_bed": 60.0,
                    "axis_z": 0.5,
                    "flow": 100,
                    "speed": 100,
                    "fan_hotend": 1200,
                    "fan_print": 4500,
                }
            },
        )
    )
    result = await pl.get_status()
    assert result["printer"]["state"] == "PRINTING"
    assert result["printer"]["temp_nozzle"] == 214.9


async def test_get_job(pl, respx_mock):
    respx_mock.get(f"{HOST}/api/v1/job").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 42,
                "state": "PRINTING",
                "progress": 55.0,
                "time_printing": 1200,
                "time_remaining": 980,
                "file": {
                    "name": "TEST~1.gco",
                    "display_name": "test_print.gcode",
                    "path": "/local",
                    "display_path": "/PrusaLink gcodes",
                    "size": 2393142,
                    "m_timestamp": 1648042843,
                    "refs": {
                        "download": None,
                        "icon": None,
                        "thumbnail": "/api/thumbnails/local/test.gcode.orig.png",
                    },
                },
            },
        )
    )
    result = await pl.get_job()
    assert result["id"] == 42
    assert result["progress"] == 55.0
    assert result["file"]["display_name"] == "test_print.gcode"


async def test_get_job_no_active_job(pl, respx_mock):
    """When no job is running the API returns 204 and we return an empty dict."""
    respx_mock.get(f"{HOST}/api/v1/job").mock(return_value=httpx.Response(204))
    result = await pl.get_job()
    assert result == {}


async def test_get_legacy_printer(pl, respx_mock):
    respx_mock.get(f"{HOST}/api/printer").mock(
        return_value=httpx.Response(
            200,
            json={"telemetry": {"material": "PLA"}},
        )
    )
    result = await pl.get_legacy_printer()
    assert result["telemetry"]["material"] == "PLA"


async def test_cancel_job(pl, respx_mock):
    respx_mock.delete(f"{HOST}/api/v1/job/42").mock(return_value=httpx.Response(204))
    await pl.cancel_job(42)  # Should not raise


async def test_pause_job(pl, respx_mock):
    respx_mock.put(f"{HOST}/api/v1/job/42/pause").mock(return_value=httpx.Response(204))
    await pl.pause_job(42)


async def test_resume_job(pl, respx_mock):
    respx_mock.put(f"{HOST}/api/v1/job/42/resume").mock(
        return_value=httpx.Response(204)
    )
    await pl.resume_job(42)


async def test_get_transfer(pl, respx_mock):
    respx_mock.get(f"{HOST}/api/v1/transfer").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 7,
                "type": "FROM_WEB",
                "display_name": "model.gcode",
                "path": "/usb",
                "size": 2393142,
                "progress": 42.25,
                "transferred": 1011000,
                "time_remaining": 61,
                "time_transferring": 42,
                "to_print": False,
            },
        )
    )
    result = await pl.get_transfer()
    assert result["type"] == "FROM_WEB"
    assert result["progress"] == 42.25


async def test_get_transfer_none(pl, respx_mock):
    """Returns None when no transfer is active."""
    respx_mock.get(f"{HOST}/api/v1/transfer").mock(return_value=httpx.Response(204))
    assert await pl.get_transfer() is None


async def test_cancel_transfer(pl, respx_mock):
    respx_mock.delete(f"{HOST}/api/v1/transfer/7").mock(
        return_value=httpx.Response(204)
    )
    await pl.cancel_transfer(7)


async def test_get_file(pl, respx_mock):
    thumbnail_bytes = b"\x89PNG\r\nfake-image-data"
    respx_mock.get(f"{HOST}/api/thumbnails/test.png").mock(
        return_value=httpx.Response(200, content=thumbnail_bytes)
    )
    result = await pl.get_file("/api/thumbnails/test.png")
    assert result == thumbnail_bytes
