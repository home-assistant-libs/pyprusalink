"""Helpers for parsing Prusa print file metadata."""

from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any
import zlib

from pyprusalink.types import PrintFileMetadata

_BGCODE_MAGIC = b"GCDE"
_BGCODE_FILE_HEADER_SIZE = 10
_BGCODE_BLOCK_HEADER_SIZE = 8
_BGCODE_COMPRESSED_BLOCK_HEADER_SIZE = 12
_BGCODE_METADATA_BLOCK_TYPES = {0, 2, 3, 4}
_BGCODE_GCODE_BLOCK_TYPE = 1
_BGCODE_THUMBNAIL_BLOCK_TYPE = 5
_BGCODE_NO_COMPRESSION = 0
_BGCODE_DEFLATE_COMPRESSION = 1
_BGCODE_INI_ENCODING = 0
_BGCODE_CRC32_CHECKSUM = 1
_BGCODE_CRC32_SIZE = 4
_FLOAT_PATTERN = re.compile(r"-?\d+(?:\.\d+)?")
_DURATION_PART_PATTERN = re.compile(r"(?P<value>\d+)\s*(?P<unit>[hms])")


def parse_file_metadata(data: bytes) -> PrintFileMetadata:
    """Parse known PrusaSlicer metadata from G-code or BG-code bytes."""
    if data.startswith(_BGCODE_MAGIC):
        return parse_metadata_mapping(_bgcode_metadata_to_mapping(data))

    return parse_metadata_mapping(_gcode_metadata_to_mapping(data))


def parse_metadata_mapping(metadata: Mapping[str, Any] | None) -> PrintFileMetadata:
    """Normalize known Prusa print metadata keys."""
    parsed: PrintFileMetadata = {}

    if metadata is None:
        return parsed

    normalized = {_normalize_key(key): value for key, value in metadata.items()}

    filament_used_g = _parse_float(normalized.get("filament used [g]"))
    if filament_used_g is not None:
        parsed["filament_used_g"] = filament_used_g

    filament_used_mm = _parse_float(normalized.get("filament used [mm]"))
    if filament_used_mm is not None:
        parsed["filament_used_mm"] = filament_used_mm

    filament_used_cm3 = _parse_float(normalized.get("filament used [cm3]"))
    if filament_used_cm3 is not None:
        parsed["filament_used_cm3"] = filament_used_cm3

    filament_cost = _parse_float(normalized.get("filament cost"))
    if filament_cost is not None:
        parsed["filament_cost"] = filament_cost

    filament_type = normalized.get("filament_type")
    if filament_type is not None:
        parsed["filament_type"] = str(filament_type).strip()

    estimated_printing_time_normal = _parse_duration(
        str(normalized.get("estimated printing time (normal mode)", ""))
    )
    if estimated_printing_time_normal is not None:
        parsed["estimated_printing_time_normal"] = estimated_printing_time_normal

    estimated_printing_time_silent = _parse_duration(
        str(normalized.get("estimated printing time (silent mode)", ""))
    )
    if estimated_printing_time_silent is not None:
        parsed["estimated_printing_time_silent"] = estimated_printing_time_silent

    return parsed


def _gcode_metadata_to_mapping(data: bytes) -> dict[str, str]:
    """Extract key-value metadata lines from text G-code."""
    return _metadata_lines_to_mapping(data.decode("utf-8", errors="ignore"))


def _bgcode_metadata_to_mapping(data: bytes) -> dict[str, str]:
    """Extract INI-encoded metadata blocks from BG-code."""
    metadata: dict[str, str] = {}
    checksum_size = _bgcode_checksum_size(_read_uint16(data, 8))
    offset = _BGCODE_FILE_HEADER_SIZE

    while offset + _BGCODE_BLOCK_HEADER_SIZE <= len(data):
        block_type = _read_uint16(data, offset)
        compression = _read_uint16(data, offset + 2)
        uncompressed_size = _read_uint32(data, offset + 4)

        if block_type == _BGCODE_GCODE_BLOCK_TYPE:
            break

        if compression == _BGCODE_NO_COMPRESSION:
            block_data_size = uncompressed_size
            offset += _BGCODE_BLOCK_HEADER_SIZE
        else:
            if offset + _BGCODE_COMPRESSED_BLOCK_HEADER_SIZE > len(data):
                break

            block_data_size = _read_uint32(data, offset + 8)
            offset += _BGCODE_COMPRESSED_BLOCK_HEADER_SIZE

        parameters_size = _bgcode_block_parameters_size(block_type)
        if offset + parameters_size + block_data_size + checksum_size > len(data):
            break

        encoding = _read_uint16(data, offset) if parameters_size >= 2 else None
        offset += parameters_size

        block_data = data[offset : offset + block_data_size]
        offset += block_data_size + checksum_size

        if (
            block_type not in _BGCODE_METADATA_BLOCK_TYPES
            or encoding != _BGCODE_INI_ENCODING
        ):
            continue

        if (metadata_block := _decode_bgcode_block(block_data, compression)) is None:
            continue

        metadata.update(_metadata_lines_to_mapping(metadata_block))

    return metadata


def _metadata_lines_to_mapping(text: str) -> dict[str, str]:
    """Extract key-value metadata lines from INI-like metadata text."""
    metadata: dict[str, str] = {}
    for line in text.splitlines():
        clean_line = line.strip().lstrip(";").strip()
        if "=" not in clean_line:
            continue

        key, value = clean_line.split("=", 1)
        metadata[_normalize_key(key)] = value.strip()

    return metadata


def _decode_bgcode_block(data: bytes, compression: int) -> str | None:
    """Decode a BG-code metadata block."""
    if compression == _BGCODE_NO_COMPRESSION:
        decoded = data
    elif compression == _BGCODE_DEFLATE_COMPRESSION:
        try:
            decoded = zlib.decompress(data)
        except zlib.error:
            return None
    else:
        return None

    return decoded.decode("utf-8", errors="replace")


def _bgcode_block_parameters_size(block_type: int) -> int:
    """Return the size of the block parameters."""
    if block_type == _BGCODE_THUMBNAIL_BLOCK_TYPE:
        return 6

    return 2


def _bgcode_checksum_size(checksum_type: int) -> int:
    """Return the size of the block checksum."""
    if checksum_type == _BGCODE_CRC32_CHECKSUM:
        return _BGCODE_CRC32_SIZE

    return 0


def _read_uint16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 2], "little")


def _read_uint32(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 4], "little")


def _normalize_key(key: Any) -> str:
    return " ".join(str(key).strip().lower().split())


def _parse_float(value: Any) -> float | None:
    if isinstance(value, int | float):
        return float(value)

    match = _FLOAT_PATTERN.search(str(value))
    if match is None:
        return None

    return float(match.group(0))


def _parse_duration(value: str) -> int | None:
    total_seconds = 0

    for match in _DURATION_PART_PATTERN.finditer(value.lower()):
        amount = int(match.group("value"))
        unit = match.group("unit")

        if unit == "h":
            total_seconds += amount * 3600
        elif unit == "m":
            total_seconds += amount * 60
        else:
            total_seconds += amount

    return total_seconds or None
