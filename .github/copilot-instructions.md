# Copilot code review instructions

- Start review comments with a short, one-sentence summary of the suggested fix.
- Do not comment on code style, formatting, or linting issues — `black`, `isort`, `flake8`, and `mypy --strict` run in CI.
- A dependency version bump PR should only contain changes required for the version bump.

## Helpful kinds of feedback

- Type-soundness issues: `Any` leaks, `cast()` against the wrong type, `TypedDict` fields that lie about presence (`T | None` where the API actually omits the key).
- Behaviour drift between the public API and what the upstream PrusaLink HTTP endpoint actually returns.
- Async correctness: missing `await`, sync calls inside async functions, blocking I/O.
- Test gaps for newly added behaviour, especially 204/404/409 paths and the no-resource case.

## Less helpful kinds of feedback

- Suggestions to introduce a runtime validation library (pydantic, msgspec) for the `response.json()` boundary — see "Public API conventions" below for the trade-off.
- Generic "should we add retries / caching / backoff" suggestions on the HTTP layer; those are deliberately the consumer's concern.
- Style/lint comments (CI covers these).

# Project context

`pyprusalink` is an async Python client for the [PrusaLink HTTP API](https://github.com/prusa3d/Prusa-Link-Web/blob/master/spec/openapi.yaml). It covers both the current `/api/v1/...` endpoints and a few legacy paths (`/api/version`, `/api/printer`).

The primary consumer is the [Home Assistant `prusalink` integration](https://www.home-assistant.io/integrations/prusalink/). API shape and breaking-change decisions are weighted toward what serves that integration best.

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
