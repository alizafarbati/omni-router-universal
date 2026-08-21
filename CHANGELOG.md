# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2026-08-21

### Added
- **PyPI packaging** (`pyproject.toml`, `pip install omni-router`, `omni-router` CLI entry point).
- **Docker** (`Dockerfile` + `docker-compose.yml` with healthcheck).
- **CI** (`.github/workflows/ci.yml` — 3-OS matrix × 3 Python versions + Docker smoke test).
- **Tests** (`tests/test_router.py` — unit + live integration: translation, routing, model discovery, health, metrics).
- **Prometheus `/metrics`** (`/metrics`, `/v1/metrics`) — `omni_router_requests_total`, `tokens_input/output`, `uptime`, `provider_requests`.
- **Cost ledger** — per-provider request counts and token totals surfaced in `/metrics` and `/health`.
- **Virtual API keys** — optional per-client isolation via `configs/virtual_keys.json` or `OMNI_VIRTUAL_KEYS` (RPM + daily limits, 401/429 gating).
- `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md`.

### Changed
- README upgraded to advanced reference (badges, arch diagram, provider matrix, advanced config, troubleshooting, roadmap).

## [0.1.0] - 2026-08-21

- Initial public release — smart free-tier router (Gemini ×3 rotation, OpenRouter 20 free models, NVIDIA NIM, Go sub, capability routing, OpenAI + Anthropic dual API, gateway discovery, health dashboard).
