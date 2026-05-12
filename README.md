# pyprusalink

[![PyPI](https://img.shields.io/pypi/v/pyprusalink.svg)](https://pypi.org/project/pyprusalink/)
[![Python](https://img.shields.io/pypi/pyversions/pyprusalink.svg)](https://pypi.org/project/pyprusalink/)
[![License](https://img.shields.io/pypi/l/pyprusalink.svg)](https://github.com/home-assistant-libs/pyprusalink/blob/main/LICENSE)

Async Python wrapper for the [PrusaLink v2 API](https://github.com/prusa3d/Prusa-Link-Web/blob/master/spec/openapi.yaml).

The primary consumer is the [Home Assistant `prusalink` integration](https://www.home-assistant.io/integrations/prusalink/). The library is intentionally a thin wrapper around the HTTP API — it does not perform runtime validation, retry, or caching. Consumers handle those concerns.

## Requirements

- Python 3.11+
- A PrusaLink-enabled Prusa printer (bundled with Prusa-Firmware-Buddy on Core One, MK4, MK3.9, MK3.5, MINI, XL; or standalone PrusaLink on an RPi)

The library is async-only and is built on [`httpx`](https://www.python-httpx.org/). Digest authentication is handled by `httpx.DigestAuth` under the hood.

## Installation

```bash
pip install pyprusalink
```

## Quickstart

```python
import asyncio

import httpx
from pyprusalink import PrusaLink


async def main() -> None:
    async with httpx.AsyncClient() as client:
        api = PrusaLink(client, "http://prusa.local", "maker", "<password>")

        info = await api.get_info()
        print(info.get("name"), info.get("serial"))

        status = await api.get_status()
        print(status["printer"]["state"])

        job = await api.get_job()
        if job is not None:
            print(f"{job['progress']:.0f}% — {job['file']['display_name']}")


asyncio.run(main())
```

The username on bundled-firmware printers is `maker`. The password is the API key shown under **Settings → PrusaLink** on the printer.

## Public API

| Method | Returns | Notes |
| --- | --- | --- |
| `get_version()` | `VersionInfo` | `/api/version` — firmware, hostname, API version |
| `get_info()` | `PrinterInfo` | `/api/v1/info` — serial, model, location, capabilities |
| `get_status()` | `PrinterStatus` | `/api/v1/status` — printer state plus embedded job/storage/transfer/camera |
| `get_job()` | `JobInfo \| None` | `/api/v1/job` — `None` when no job is running |
| `get_storage()` | `list[Storage]` | `/api/v1/storage` — available storage devices |
| `get_transfer()` | `Transfer \| None` | `/api/v1/transfer` — `None` when no transfer is in progress |
| `cancel_transfer(transfer_id)` | `None` | Cancel an active upload |
| `cancel_job(job_id)` | `None` | Cancel a print |
| `pause_job(job_id)` | `None` | Pause a running print |
| `resume_job(job_id)` | `None` | Resume a paused print |
| `continue_job(job_id)` | `None` | Continue after the printer enters the `ATTENTION` state (e.g. timelapse capture) |
| `get_legacy_printer()` | `LegacyPrinterStatus` | `/api/printer` — legacy endpoint, used for `material` |
| `get_file(path)` | `bytes` | Fetch raw resources such as thumbnails referenced from `JobFilePrint.refs` |

### Errors

All HTTP errors map to subclasses of `PrusaLinkError`:

| Exception | When |
| --- | --- |
| `InvalidAuth` | 401 — wrong credentials |
| `NotFound` | 404 — resource missing |
| `Conflict` | 409 — action conflicts with current printer state (e.g. cancel while idle) |

```python
from pyprusalink.types import Conflict

try:
    await api.cancel_job(42)
except Conflict:
    ...  # printer wasn't in a cancellable state
```

## Type contract

Return types are `TypedDict`s declared in [`pyprusalink/types.py`](pyprusalink/types.py). Two conventions worth knowing:

1. **`NotRequired[T]` for optional fields.** The PrusaLink API omits absent fields rather than returning `null`, so optional fields are `NotRequired[T]` and consumers must use `.get(...)` or membership checks. Indexing a missing key raises `KeyError`.

2. **`T | None` for return types when the resource may be absent.** `get_job()` and `get_transfer()` return `None` (not an empty `dict`) when there's no active job/transfer.

The library does not perform runtime validation. `response.json()` results are wrapped in `typing.cast(...)` against the declared `TypedDict`. This is a deliberate choice — for a thin wrapper, the runtime overhead and dependency footprint of pydantic/msgspec is not worth it. If you need runtime validation, layer it on top.

## Versioning

[Semantic versioning](https://semver.org/). Changes to `TypedDict` shapes that affect strict-typed consumers are counted as breaking and require a major version bump.

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[test,lint]"

# unit tests (default — integration tests are excluded)
pytest tests/

# lint
black --check pyprusalink/ tests/
flake8 pyprusalink/ tests/
isort --check pyprusalink/ tests/
mypy
```

### Integration tests

Integration tests live in `tests/test_integration.py` and run against a real printer. They are opt-in via the `integration` pytest marker:

```bash
PRUSALINK_HOST=http://prusa.local \
PRUSALINK_USERNAME=maker \
PRUSALINK_PASSWORD=<api-key> \
pytest tests/test_integration.py -m integration
```

## License

[Apache-2.0](LICENSE).
