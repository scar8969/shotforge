<p align="center">
  <img src="docs/assets/screens/root.png" alt="shotforge running" width="900">
</p>

<h1 align="center">shotforge</h1>

<p align="center"><b>A screenshot API with per-key quotas and an honest 502.</b></p>

<p align="center">
  <a href="https://github.com/scar8969/shotforge/actions/workflows/ci.yml"><img src="https://github.com/scar8969/shotforge/actions/workflows/ci.yml/badge.svg" alt="ci"></a> <a href="#quality-gates"><img src="https://img.shields.io/badge/tests-22%20passed-2ea44f" alt="tests: 22 passed"></a> <a href="#quality-gates"><img src="https://img.shields.io/badge/coverage-60.8%-yellow" alt="coverage: 60.8%"></a> <a href="#api"><img src="https://img.shields.io/badge/routes-10%20live-0969da" alt="routes: 10 live"></a> <a href="#requirements"><img src="https://img.shields.io/badge/python-3.11%2B-3776ab" alt="python: 3.11+"></a> <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-2ea44f" alt="license: MIT"></a>
</p>

shotforge renders a URL to an image through a headless browser, caches the result on disk, and enforces a hard per-key quota. When no renderer can start it returns 502 with the reason instead of an empty PNG.

---

**Contents** &nbsp;·&nbsp; [Why](#why-this-exists) &nbsp;·&nbsp; [What it does](#what-it-does) &nbsp;·&nbsp; [Quickstart](#quickstart) &nbsp;·&nbsp; [Screenshots](#screenshots) &nbsp;·&nbsp; [API](#api) &nbsp;·&nbsp; [CLI](#cli) &nbsp;·&nbsp; [Configuration](#configuration) &nbsp;·&nbsp; [Measured](#measured-not-estimated) &nbsp;·&nbsp; [How a request flows](#how-a-request-flows) &nbsp;·&nbsp; [Architecture](#architecture) &nbsp;·&nbsp; [Quality gates](#quality-gates) &nbsp;·&nbsp; [Development](#development) &nbsp;·&nbsp; [Deploy](#deploy) &nbsp;·&nbsp; [Limits](#limits-stated-rather-than-hidden)

## Why this exists

Screenshot services fail in a specific way: they return a blank image and call it success. This one treats a missing renderer as a failed request, caches by URL and viewport, and meters usage per key so one caller cannot exhaust the host.

## What it does

| Capability | How it works |
| --- | --- |
| **Per-key auth and quota** | Each key has a quota and a usage counter; exhausted keys get 429. |
| **On-disk cache** | The same URL and viewport is served from cache with the age reported. |
| **Honest failure** | No renderer means 502 with the attempted command, not a placeholder image. |
| **CLI client** | newkey, shot and usage talk to a running instance. |

## Quickstart

```sh
git clone https://github.com/scar8969/shotforge.git
cd shotforge
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python wsgi.py                                 # http://127.0.0.1:8000
```

It is up when this answers:

```sh
curl -s http://127.0.0.1:8000/api/shot
```

## Screenshots

Captured from the running service with headless Chromium at 1440×900, one image per page, committed under [`docs/assets/screens/`](docs/assets/screens/).

<table>
<tr>
<td width="50%"><img src="docs/assets/screens/docs.png" alt="/docs" width="100%"><br><sub><code>/docs</code> &middot; 43.4 KB</sub></td>
<td width="50%"><img src="docs/assets/screens/keys.png" alt="/keys" width="100%"><br><sub><code>/keys</code> &middot; 28.0 KB</sub></td>
</tr>
</table>

<table>
<tr>
<td width="50%"><img src="docs/assets/screens/playground.png" alt="/playground" width="100%"><br><sub><code>/playground</code> &middot; 30.5 KB</sub></td>
</tr>
</table>

The other 5 captures — the health, liveness, readiness, metrics and version endpoints — are committed in the same folder rather than shown here.

## API

Every route below is declared in [`openapi/shotforge.yaml`](openapi/shotforge.yaml) and exercised by the live probe recorded in [`docs/EVIDENCE.md`](docs/EVIDENCE.md).

| Method | Path | What it does |
| --- | --- | --- |
| `GET` | `/api/shot` | capture |
| `POST` | `/api/keys` | create key |
| `GET` | `/api/keys/<id>/usage` | usage |

## CLI

The same operations without an HTTP client. Installed as `shotforge`, and runnable from a checkout with no install:

```sh
python -m shotapi.cli --help
```

```text
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

## Configuration

Environment only — there is no config file. Copy `.env.example` to `.env` and edit; `APP_ENV=production` refuses to start without `SECRET_KEY`.

| Variable | Default | Meaning |
| --- | --- | --- |
| `APP_ENV` | `development` | development \| staging \| production; production enforces the secret. |
| `SECRET_KEY` | `change-me-in-production` | Session/CSRF signing key. Required when APP_ENV=production. |
| `HOST` | `0.0.0.0` | Interface the dev server binds. |
| `PORT` | `8000` | Port the dev server and the container listen on. |
| `DEBUG` | `false` | Flask debug mode. Never true in production. |
| `MAX_CONTENT_LENGTH` | `8388608` | Largest accepted request body, in bytes. |
| `DATA_DIR` | `(empty)` | Where uploaded and generated files live. |
| `INSTANCE_DIR` | `(empty)` | Where the SQLite file and instance state live. |
| `LOG_DIR` | `(empty)` | Where rotated log files are written, if file logging is on. |
| `LOG_LEVEL` | `INFO` | DEBUG \| INFO \| WARNING \| ERROR. |
| `LOG_JSON` | `true` | true emits one JSON object per line; false is human-readable. |
| `REQUEST_ID_HEADER` | `X-Request-ID` | Header echoed on every response and stamped on every log line. |
| `SHOTAPI_URL` | `http://127.0.0.1:8000` | Base URL the CLI talks to; also accepted as --url. |

## Measured, not estimated

Produced on this checkout by `pytest --cov` and by booting `wsgi.py` and issuing one real GET per documented path. The commands are recorded in [`docs/EVIDENCE.md`](docs/EVIDENCE.md).

| Signal | Value |
| --- | --- |
| Tests | **22 / 22 passed** (2.2 s, exit 0) |
| Line coverage | **60.8%** — 432 of 678 statements |
| Source | 15 files / 1,473 lines |
| Test code | 4 files / 221 lines |
| Documented paths | 3 in the spec, 2 GET |
| Live probe | 13 GET requests to the booted app, **10 answered 200** |
| Median latency | **8.2 ms** (single uncached request, dev server) |
| Slowest / fastest | 160.0 ms `/` / 4.3 ms `/readyz` |
| Bytes served | 25.7 KB across 13 responses |
| Screenshots | 9 captured |

## How a request flows

```text
client
  │  HTTP
  ▼
wsgi.py ──▶ shotapi/app.py:get_app()
                │  reads config once (shotapi/config.py)
                │  registers the `shot` blueprint
                ▼
           route handler
             ├──▶ shotapi/models.py        tables, via Flask-SQLAlchemy
             ├──▶ shotapi/errors.py        raises typed errors → one JSON envelope
             └──▶ shotapi/observability.py JSON log line + X-Request-ID
```

Every response carries `X-Request-ID`, and the matching log line is written once at the end of the request with the status and duration, so a report of "it failed" is one `grep` away from the traceback.

## Architecture

```
shotforge/
├── src/shotapi/
│   ├── http.py                         379  HTTP plumbing for shotapi: correlation ids, access l
│   ├── _app.py                         215  
│   ├── config.py                       172  Environment-driven configuration for shotapi
│   ├── observability.py                169  Structured logging and request correlation for shota
│   ├── app.py                          119  Application factory for shotapi
│   ├── errors.py                       108  Typed application errors and their HTTP mapping for 
│   ├── cli.py                          105  Command line client for shotapi
│   ├── shot/api.py                      66  
│   ├── paths.py                         52  Filesystem layout for shotapi
│   ├── shot/cache.py                    33  
│   ├── models.py                        26  
│   ├── shot/capture.py                  19  
├── openapi/shotforge.yaml                 the contract of record
├── schema/shotforge.sql                   the DDL
├── tests/                       the suite that has to stay green
├── docs/EVIDENCE.md             the recorded live route walk
├── Dockerfile                   multi-stage build
└── wsgi.py                      entry point
```

The package keeps one shape across the service: `config.py` reads the environment once, `observability.py` emits structured JSON logs carrying a request id, `errors.py` turns exceptions into a single JSON envelope, `models.py` holds the tables, and the `shot/` package holds the routes.

## Quality gates

| Gate | Command | Threshold |
| --- | --- | --- |
| Suite | `pytest -q` | all green |
| Coverage | `pytest --cov` | floor in `pyproject.toml`, set below the measured value |
| Lint | `ruff check src tests` | zero findings |
| Format | `ruff format --check src tests` | zero reformats |
| Types | `mypy src` | zero errors |
| Security | `bandit -c pyproject.toml -r src` | reviewed skip list, no unreviewed finding |
| Live routes | boot `wsgi.py`, one GET per documented path | no 5xx, no undocumented guard |

CI runs the first six on Python 3.11, 3.12 and 3.13 on every push to `main`, plus a container build — [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Development

```sh
pip install -e ".[dev]"
python -m pytest -q                      # the suite
python -m pytest --cov                   # with the coverage floor
python -m ruff check src tests           # lint
python -m ruff format --check src tests  # formatting
python -m mypy src                       # types
python -m bandit -c pyproject.toml -r src  # security
pre-commit install                       # the same checks on commit
```

Dependabot opens grouped PRs for the dev tooling weekly and for actions and the base image monthly.

## Deploy

```sh
docker build -t shotforge .
docker run --rm -p 8000:8000 --env-file .env.example shotforge
```

A `docker-compose.yml` is included for a local run with a volume for the SQLite file. The image runs as a non-root user and serves through gunicorn.

## Limits, stated rather than hidden

- Requires Chrome or Chromium on the host; the service does not bundle a browser.
- Cache entries are keyed by URL, format, viewport and full-page flag — not by cookie or header.

## License

MIT — see [LICENSE](LICENSE).
