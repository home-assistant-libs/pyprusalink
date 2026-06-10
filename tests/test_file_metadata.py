"""Tests for Prusa print file metadata parsing."""

import struct
import zlib

from pyprusalink.file_metadata import parse_file_metadata, parse_metadata_mapping


def _bgcode_block(
    block_type: int, payload: bytes, encoding: int = 0, compression: int = 0
) -> bytes:
    if compression == 1:
        block_data = zlib.compress(payload)
        header = struct.pack(
            "<HHII", block_type, compression, len(payload), len(block_data)
        )
    else:
        block_data = payload
        header = struct.pack("<HHI", block_type, compression, len(payload))

    return header + struct.pack("<H", encoding) + block_data


def test_parse_file_metadata_from_gcode_comments():
    data = b"""
; printer_model=COREONE
; filament_type=PLA
; filament used [mm]=8184.17
; filament used [g]=24.41
; filament cost=0.68
; filament used [cm3]=19.69
; estimated printing time (normal mode)=1h 3m 31s
; estimated printing time (silent mode)=1h 10m 56s
"""

    result = parse_file_metadata(data)

    assert result == {
        "filament_type": "PLA",
        "filament_used_mm": 8184.17,
        "filament_used_g": 24.41,
        "filament_cost": 0.68,
        "filament_used_cm3": 19.69,
        "estimated_printing_time_normal": 3811,
        "estimated_printing_time_silent": 4256,
    }


def test_parse_file_metadata_from_bgcode_binary_content():
    metadata = b"\n".join(
        (
            b"printer_model=COREONE",
            b"filament_type=PETG",
            b"filament used [mm]=1234.5",
            b"filament used [g]=3.21",
            b"estimated printing time (normal mode)=2h 4m",
        )
    )
    data = (
        b"GCDE"
        + struct.pack("<IH", 1, 0)
        + _bgcode_block(4, metadata)
        + _bgcode_block(1, b"G1 X10")
    )

    result = parse_file_metadata(data)

    assert result["filament_type"] == "PETG"
    assert result["filament_used_mm"] == 1234.5
    assert result["filament_used_g"] == 3.21
    assert result["estimated_printing_time_normal"] == 7440


def test_parse_file_metadata_from_deflated_bgcode_metadata_block():
    metadata = b"filament_type=PLA\nfilament used [g]=24.41"
    data = (
        b"GCDE" + struct.pack("<IH", 1, 0) + _bgcode_block(4, metadata, compression=1)
    )

    result = parse_file_metadata(data)

    assert result == {
        "filament_type": "PLA",
        "filament_used_g": 24.41,
    }


def test_parse_file_metadata_from_multiple_bgcode_metadata_blocks():
    data = (
        b"GCDE"
        + struct.pack("<IH", 1, 0)
        + _bgcode_block(3, b"filament_type=PETG")
        + _bgcode_block(4, b"filament used [g]=12.34")
    )

    result = parse_file_metadata(data)

    assert result == {
        "filament_type": "PETG",
        "filament_used_g": 12.34,
    }


def test_parse_file_metadata_ignores_missing_values():
    assert parse_file_metadata(b"; printer_model=COREONE\nG1 X10 Y10") == {}


def test_parse_metadata_mapping_normalizes_values():
    result = parse_metadata_mapping(
        {
            " Filament Used [G] ": "24.41 g",
            "FILAMENT_TYPE": " PLA ",
            "Estimated Printing Time (Normal Mode)": "31s",
        }
    )

    assert result == {
        "filament_used_g": 24.41,
        "filament_type": "PLA",
        "estimated_printing_time_normal": 31,
    }
