# Changelog

## [0.5.0] - 2026-08-21

### Added
- **Helm chart** (helm/omni-router) — proper chart with helm lint + helm template CI.
- **Examples** (examples/curl.sh, python_openai.py, claude_code.sh).
- **Community health** — CODE_OF_CONDUCT.md, issue/PR templates.

### Fixed
- Valid-key hang: fast 429 with Retry-After if all providers cooling (no more 10s hang).
- Coverage: mocked provider tests so CI actually exercises routing.



## [0.4.1] - 2026-08-21

### Fixed
- **Lint**: split imports, remove unused sys/io (E401, F401).
- **DoS hardening**: 413 Request Too Large for bodies >200KB.
- **Honest docs**: README now says honest ~10M free / ~210M with Go sub instead of inflated 600M per free tier.
- **Tests**: mocked provider tests so CI actually exercises routing (was 31% → 38% coverage, 53 tests).

## [0.4.0] - 2026-08-21

### Added
- **Grafana dashboard** (configs/grafana-dashboard.json).
- **Auto model-catalog refresh** from OpenRouter (hourly, OMNI_AUTO_REFRESH=0 to disable).
- **K8s manifest** (configs/k8s-manifest.yaml) with secrets + probes.
- Full setup guide + API reference + FAQ in README.

### Changed
- Branding: Built by Ali Zafar.



All notable changes to this project will be documented in this file.

## [0.2.0] - 2026-08-21

### Added
- **PyPI packaging** (`pyproject.toml`, `pip install omni-router`, `omni-router` CLI entry point).
- **Docker** (`Dockerfile` + `docker-compose.yml` with healthcheck).
- **CI** (`.github/workflows/ci.yml` â€” 3-OS matrix Ã— 3 Python versions + Docker smoke test).
- **Tests** (`tests/test_router.py` â€” unit + live integration: translation, routing, model discovery, health, metrics).
- **Prometheus `/metrics`** (`/metrics`, `/v1/metrics`) â€” `omni_router_requests_total`, `tokens_input/output`, `uptime`, `provider_requests`.
- **Cost ledger** â€” per-provider request counts and token totals surfaced in `/metrics` and `/health`.
- **Virtual API keys** â€” optional per-client isolation via `configs/virtual_keys.json` or `OMNI_VIRTUAL_KEYS` (RPM + daily limits, 401/429 gating).
- `SECURITY.md`, `CONTRIBUTING.md`, `CHANGELOG.md`.

### Changed
- README upgraded to advanced reference (badges, arch diagram, provider matrix, advanced config, troubleshooting, roadmap).

## [0.1.0] - 2026-08-21

- Initial public release â€” smart free-tier router (Gemini Ã—3 rotation, OpenRouter 20 free models, NVIDIA NIM, Go sub, capability routing, OpenAI + Anthropic dual API, gateway discovery, health dashboard).



