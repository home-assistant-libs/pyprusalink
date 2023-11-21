from typing import TypedDict

"""Legacy Types of the non v1 API. Source: https://github.com/prusa3d/Prusa-Link-Web/blob/master/spec/openapi-legacy.yaml"""


class LegacyPrinterTelemetry(TypedDict):
    """Legacy Printer telemetry."""

    material: str | None


class LegacyPrinterStatus(TypedDict):
    """Legacy Printer status."""

    telemetry: LegacyPrinterTelemetry | None
