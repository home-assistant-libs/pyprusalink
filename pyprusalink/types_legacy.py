from typing import TypedDict, Optional

"""Legacy Types of the non v1 API. Source: https://github.com/prusa3d/Prusa-Link-Web/blob/master/spec/openapi-legacy.yaml"""


class LegacyPrinterTelemetry(TypedDict):
    material: Optional[str]


class LegacyPrinterStatus(TypedDict):
    """Printer status."""

    telemetry: Optional[LegacyPrinterTelemetry]
