"""Happy-path tests for PrusaLink public API methods."""

import httpx
from pyprusalink.types import FileTooLarge
import pytest

HOST = "http://printer.local"


async def test_get_version(pl, respx_mock):
    """Modern firmware (Buddy v6.5.1+) returns firmware and printer fields."""
    respx_mock.get(f"{HOST}/api/version").mock(
        return_value=httpx.Response(
            200,
            json={
                "api": "2.0.0",
                "server": "2.1.2",
                "nozzle_diameter": 0.40,
                "text": "PrusaLink",
                "hostname": "prusa-core-one",
                "firmware": "6.5.3+12780",
                "printer": "7.1.0",
                "capabilities": {"upload-by-put": True},
            },
        )
    )
    result = await pl.get_version()
    assert result["api"] == "2.0.0"
    assert result["firmware"] == "6.5.3+12780"
    assert result["printer"] == "7.1.0"


async def test_get_version_legacy_firmware(pl, respx_mock):
    """Legacy firmware (Buddy <v6.5.1, XL, MINI) omits firmware and printer fields."""
    respx_mock.get(f"{HOST}/api/version").mock(
        return_value=httpx.Response(
            200,
            json={
                "api": "2.0.0",
                "server": "2.1.2",
                "nozzle_diameter": 0.40,
                "text": "PrusaLink",
                "hostname": "prusa-mk39",
                "capabilities": {"upload-by-put": True},
            },
        )
    )
    result = await pl.get_version()
    assert result["api"] == "2.0.0"
    assert "firmware" not in result
    assert "printer" not in result


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


async def test_get_info_minimal_firmware(pl, respx_mock):
    """Older firmware may omit several PrinterInfo fields."""
    respx_mock.get(f"{HOST}/api/v1/info").mock(
        return_value=httpx.Response(
            200,
            json={
                "serial": "CZPX4720X004XC34242",
                "nozzle_diameter": 0.4,
                "hostname": "prusa-mk3",
            },
        )
    )
    result = await pl.get_info()
    assert result["serial"] == "CZPX4720X004XC34242"
    assert "min_extrusion_temp" not in result
    assert "network_error_chime" not in result
    assert "farm_mode" not in result


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
                },
                "job": {
                    "id": 42,
                    "progress": 55.0,
                    "time_printing": 1200,
                    "time_remaining": 980,
                },
                "storage": {
                    "path": "/usb/",
                    "name": "usb",
                    "read_only": False,
                    "free_space": 4202335,
                },
            },
        )
    )
    result = await pl.get_status()
    assert result["printer"]["state"] == "PRINTING"
    assert result["printer"]["temp_nozzle"] == 214.9
    assert result["job"]["id"] == 42
    assert result["job"]["time_remaining"] == 980
    assert result["storage"]["name"] == "usb"
    assert result["storage"]["free_space"] == 4202335


async def test_get_status_idle(pl, respx_mock):
    """In IDLE state the job key is absent from the response."""
    respx_mock.get(f"{HOST}/api/v1/status").mock(
        return_value=httpx.Response(
            200,
            json={
                "printer": {
                    "state": "IDLE",
                    "temp_nozzle": 27.6,
                    "target_nozzle": 0.0,
                    "temp_bed": 24.3,
                    "target_bed": 0.0,
                    "axis_z": 0.0,
                    "flow": 100,
                    "speed": 100,
                    "fan_hotend": 0,
                    "fan_print": 0,
                },
                "storage": {
                    "path": "/usb/",
                    "name": "usb",
                    "read_only": False,
                },
            },
        )
    )
    result = await pl.get_status()
    assert result["printer"]["state"] == "IDLE"
    assert "job" not in result


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
    """When no job is running the API returns 204 and we return None."""
    respx_mock.get(f"{HOST}/api/v1/job").mock(return_value=httpx.Response(204))
    result = await pl.get_job()
    assert result is None


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


async def test_continue_job(pl, respx_mock):
    respx_mock.put(f"{HOST}/api/v1/job/42/continue").mock(
        return_value=httpx.Response(204)
    )
    await pl.continue_job(42)


async def test_get_storage(pl, respx_mock):
    respx_mock.get(f"{HOST}/api/v1/storage").mock(
        return_value=httpx.Response(
            200,
            json={
                "storage_list": [
                    {
                        "name": "usb",
                        "type": "USB",
                        "path": "/usb/",
                        "read_only": False,
                        "available": True,
                        "free_space": 14123456789,
                        "total_space": 16000000000,
                    }
                ]
            },
        )
    )
    result = await pl.get_storage()
    assert len(result) == 1
    assert result[0]["name"] == "usb"
    assert result[0]["type"] == "USB"
    assert result[0]["available"] is True


async def test_get_transfer(pl, respx_mock):
    respx_mock.get(f"{HOST}/api/v1/transfer").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 7,
                "type": "FROM_WEB",
                "display_name": "model.gcode",
                "path": "/usb",
                "size": "2393142",
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


async def test_get_file_metadata(pl, respx_mock):
    print_file = b"""
; filament_type=PLA
; filament used [g]=24.41
; filament used [mm]=8184.17
; estimated printing time (normal mode)=1h 3m 31s
"""
    respx_mock.get(f"{HOST}/usb/test.bgcode").mock(
        return_value=httpx.Response(200, content=print_file)
    )

    result = await pl.get_file_metadata("/usb/test.bgcode")

    assert result == {
        "filament_type": "PLA",
        "filament_used_g": 24.41,
        "filament_used_mm": 8184.17,
        "estimated_printing_time_normal": 3811,
    }


async def test_get_file_metadata_rejects_large_files(pl, respx_mock):
    print_file = b"; filament_type=PLA\n"
    respx_mock.get(f"{HOST}/usb/large.bgcode").mock(
        return_value=httpx.Response(
            200, content=print_file, headers={"content-length": "18"}
        )
    )

    with pytest.raises(FileTooLarge):
        await pl.get_file_metadata("/usb/large.bgcode", max_bytes=17)
