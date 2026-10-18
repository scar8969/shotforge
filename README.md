<p align="center">
  <img src="docs/assets/screens/root.png" alt="shotforge running" width="900">
</p>

<h1 align="center">shotforge</h1>

<p align="center"><b>A screenshot API with per-key quotas and an honest 502.</b></p>

<p align="center">
  <a href="#quality-gates"><img src="https://img.shields.io/badge/tests-22%20passed-2ea44f" alt="tests: 22 passed"></a> <a href="#quality-gates"><img src="https://img.shields.io/badge/coverage-60.8%-yellow" alt="coverage: 60.8%"></a> <a href="#api"><img src="https://img.shields.io/badge/routes-10%20answered-0969da" alt="routes: 10 answered"></a> <a href="#requirements"><img src="https://img.shields.io/badge/python-3.11%2B-3776ab" alt="python: 3.11+"></a> <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-2ea44f" alt="license: MIT"></a>
</p>

shotforge renders a URL to an image through a headless browser, caches the result on disk, and enforces a hard per-key quota. When no renderer can start it returns 502 with the reason instead of an empty PNG.

---

**Contents** &nbsp;·&nbsp; [Why](#why-this-exists) &nbsp;·&nbsp; [What it does](#what-it-does) &nbsp;·&nbsp; [Quickstart](#quickstart) &nbsp;·&nbsp; [API](#api) &nbsp;·&nbsp; [Screenshots](#screenshots) &nbsp;·&nbsp; [Measured](#measured-not-estimated) &nbsp;·&nbsp; [Architecture](#architecture) &nbsp;·&nbsp; [Quality gates](#quality-gates) &nbsp;·&nbsp; [Deploy](#deploy) &nbsp;·&nbsp; [Limits](#limits-stated-rather-than-hidden)

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

The same work from the CLI:

```sh
python -m shotapi.cli --help
```

Commands: `shot`, `usage`, `newkey`.

A first request:

```sh
curl -s http://127.0.0.1:8000/api/shot | head
```

## Requirements

- Python **3.11+** — CI runs 3.11, 3.12 and 3.13.
- Runtime dependencies: `Flask>=3.0`, `Flask-SQLAlchemy>=3.1`, `SQLAlchemy>=2.0`, `PyYAML>=6.0`, `playwright`.
- No JavaScript build step: every page is server-rendered Jinja.

## API

Every route below is in [`openapi/shotforge.yaml`](openapi/shotforge.yaml) and is exercised by the live probe recorded in [`docs/EVIDENCE.md`](docs/EVIDENCE.md).

| Method | Path | What it does |
| --- | --- | --- |
| `GET` | `/api/shot` | capture |
| `POST` | `/api/keys` | create key |
| `GET` | `/api/keys/<id>/usage` | usage |

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

## Measured, not estimated

These numbers were produced on this checkout by `pytest --cov` and by booting `wsgi.py` and issuing one real GET per documented path. The commands are in [`docs/EVIDENCE.md`](docs/EVIDENCE.md).

| Signal | Value |
| --- | --- |
| Tests | **22 / 22 passed** (2.2 s, exit 0) |
| Line coverage | **60.8%** — 432 of 678 statements |
| Source | 15 files / 1,470 lines |
| Test code | 4 files / 221 lines |
| Documented paths | 3 in the spec, 2 GET |
| Live probe | 13 GET requests to the booted app, **10 answered 200** |
| Median latency | **8.2 ms** (single uncached request, dev server) |
| Slowest / fastest | 160.0 ms `/` / 4.3 ms `/readyz` |
| Bytes served | 25.7 KB across 13 responses |
| Screenshots | 9 captured |

## Architecture

```
shotforge/
├── src/shotapi/
│   ├── http.py                         379  HTTP plumbing for shotapi: correlation ids, access l
│   ├── _app.py                         215  
│   ├── config.py                       173  Environment-driven configuration for shotapi
│   ├── observability.py                169  Structured logging and request correlation for shota
│   ├── app.py                          119  Application factory for shotapi
│   ├── errors.py                       108  Typed application errors and their HTTP mapping for 
│   ├── cli.py                          101  Command line client for shotapi
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
| Coverage | `pytest --cov` | floor set in `pyproject.toml` from the measured value |
| Lint | `ruff check src tests` | zero findings |
| Format | `ruff format --check src tests` | zero reformats |
| Types | `mypy src` | zero errors |
| Security | `bandit -c pyproject.toml -r src` | reviewed skip list, no unreviewed finding |
| Live routes | boot `wsgi.py`, one GET per documented path | no 5xx, no undocumented guard |

CI runs the first six on Python 3.11, 3.12 and 3.13 for every push to `main`, plus a container build. See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Deploy

```sh
docker build -t shotforge .
docker run --rm -p 8000:8000 --env-file .env.example shotforge
```

Configuration is environment-only — every variable is documented in [`.env.example`](.env.example), and the service refuses to start with a production secret missing.

## Limits, stated rather than hidden

- Requires Chrome or Chromium on the host; the service does not bundle a browser.
- Cache entries are keyed by URL, format, viewport and full-page flag — not by cookie or header.

## License

MIT — see [LICENSE](LICENSE).
