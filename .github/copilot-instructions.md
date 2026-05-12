# Copilot code review instructions

- Start review comments with a short, one-sentence summary of the suggested fix.
- Do not comment on code style, formatting, or linting issues — `black`, `isort`, `flake8`, and `mypy --strict` run in CI.
- Suggest fixes at the library level rather than at the call site when the behaviour could affect downstream consumers.
- A dependency version bump PR should only contain changes required for the version bump.

# Project context

`pyprusalink` is a thin async Python wrapper around the [PrusaLink v2 API](https://github.com/prusa3d/Prusa-Link-Web/blob/master/spec/openapi.yaml). The primary consumer is the [Home Assistant `prusalink` integration](https://www.home-assistant.io/integrations/prusalink/); other consumers are negligible.

## Public API conventions

- Public methods return `TypedDict`s declared in `pyprusalink/types.py`. Runtime validation is deliberately **not** performed at the library boundary; `KeyError` / `AttributeError` from missing fields propagates to the caller.
- `response.json()` results are wrapped in `typing.cast(...)` against the declared `TypedDict`. This is the deliberate, lightweight alternative to runtime validation libraries (pydantic, msgspec); it is not a gap to be filled.
- For optional fields on a `TypedDict`, prefer `NotRequired[T]` over `T | None`. The PrusaLink API actually omits absent fields rather than returning `null`, so `NotRequired` is the honest contract.
- For methods that may not return data, use `T | None` for the return type (e.g. `get_transfer() -> Transfer | None`) rather than returning empty containers like `{}` or `[]`.

## Test conventions

- Tests live in `tests/`. HTTP is mocked with `respx`. Integration tests against a real printer are opt-in via the `integration` pytest marker; the default `pytest` invocation excludes them via `addopts = "-m 'not integration'"`.
- Test and lint dependencies live in `[project.optional-dependencies]` under `test` and `lint` groups. There is intentionally no `requirements-test.txt`.

## Versioning

Semantic versioning. Breaking changes — including changes to `TypedDict` shapes that affect strict-typed consumers — require a major version bump.
