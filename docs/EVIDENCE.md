# Evidence

Every line below was produced by a command run against this exact checkout, on this machine, at the time recorded. Nothing here is copied from the README.

| | |
| --- | --- |
| Generated | 2026-10-19 09:42 |
| Python | 3.14.7 |
| Platform | Windows 11 |

## Test suite

```sh
python -m pytest -q
```

- exit code **0**
- 22 passed in 0.92s

## Static gates

| Gate | Exit | Last line |
| --- | --- | --- |
| `ruff check` | 0 | All checks passed! |
| `ruff format --check` | 0 | 19 files already formatted |
| `mypy src` | 0 | Success: no issues found in 15 source files |
| `bandit -c pyproject.toml -r src` | 0 | — |

## Live route walk

The application was imported through `wsgi.py` and each GET path declared in `openapi/` was requested once through the Werkzeug test client.

| Status | Path | Bytes | Content-Type |
| --- | --- | --- | --- |
| 401 | `/api/shot` | 25 | application/json |
| 404 | `/api/keys/1/usage` | 51 | application/json |

2 paths walked, 0 of them raised or answered 5xx.

## CLI

```
usage: shot [-h] [--base BASE] {shot,usage,newkey} ...

shotapi command line client

positional arguments:
  {shot,usage,newkey}
    shot               capture a screenshot through the API
    usage              show quota usage for a key id
    newkey             create a new API key

options:
  -h, --help           show this help message and exit
  --base BASE          base URL of a running instance
```

## Screenshots

Captured from the running service with headless Chromium at 1440x900 and committed with the repository:

| File | Bytes |
| --- | --- |
| `docs/assets/screens/docs.png` | 44,421 |
| `docs/assets/screens/healthz.png` | 8,461 |
| `docs/assets/screens/keys.png` | 28,666 |
| `docs/assets/screens/livez.png` | 7,468 |
| `docs/assets/screens/metrics.png` | 16,534 |
| `docs/assets/screens/playground.png` | 31,192 |
| `docs/assets/screens/readyz.png` | 7,880 |
| `docs/assets/screens/root.png` | 40,335 |
| `docs/assets/screens/version.png` | 26,754 |

## What this file does not prove

- It is not a load test: every request is a single uncached call from one process.
- A green suite is not a coverage claim; `pytest --cov` reports the number the README quotes.
- The route walk exercises GET paths only; mutating routes are covered by the suite.
