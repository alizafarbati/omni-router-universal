# Security Policy

## Supported Versions

| Version | Supported |
|---|---|
| 0.2.x   | ✅ |
| 0.1.x   | ⚠️ best-effort |

## Reporting a Vulnerability

Please **do not** open a public issue for security-sensitive reports.

Email: **alizafarbati@users.noreply.github.com** with subject `[omni-router] security`.

Include:
- Affected version / commit
- Reproduction steps or PoC
- Impact assessment

We aim to acknowledge within **48h** and to ship a fix or mitigation within **7 days** for confirmed high-severity issues. Coordinated disclosure is appreciated.

## Secrets Handling

- **Never commit API keys.** Use environment variables (`GOOGLE_AI_KEY`, `OPENROUTER_KEY`, …) or a local, gitignored `configs/providers.json`.
- The example config (`configs/providers.example.json`) ships with empty `keys` arrays.
- `.gitignore` blocks `providers.json`, `*.env`, and `router.log`.
- If a key is accidentally committed, **rotate it immediately** at the provider dashboard and force-push a cleaned history or open a PR that removes it; then notify maintainers so we can purge caches if needed.

## Hardening Checklist (for self-hosted deploys)

- Bind to `127.0.0.1` by default; only expose via a reverse proxy with TLS if you need remote access.
- Put the router behind an authenticating proxy or enable **virtual keys** (`configs/virtual_keys.json` or `OMNI_VIRTUAL_KEYS` env) to isolate callers.
- Scrape `/metrics` and `/health` from your monitoring; alert on `omni_router_requests_failed` spikes and per-provider `cooling(...)` states.
