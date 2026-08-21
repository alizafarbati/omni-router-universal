# Contributing to OmniRouter

Thanks for your interest! Contributions — issues, PRs, docs, and ideas — are welcome.

## Getting Started
1. Fork the repo and clone it.
2. Create a branch: `git checkout -b feature/your-feature`.
3. Make changes, keeping the core **stdlib-only** when possible (`curl_cffi` is optional).
4. Ensure it still runs: `python omni_router/omni_router.py`.
5. Commit with a clear message and push. Open a pull request.

## Guidelines
- **No secrets** — never commit API keys, tokens, or personal paths.
- Keep the router **cross-platform** (Windows/Linux/macOS).
- Preserve the **dual API** (OpenAI + Anthropic) contract.
- Match the existing style (Google-ish Python, 4-space indent).

## Ideas for contribution
- Auto model-catalog refresh from provider APIs
- Prometheus `/metrics` + token/cost ledger
- Admin web UI
- Docker / K8s deployment files
- PyPI packaging
- More providers, more capability tags

Thanks for hacking on the free-AI switchboard. 🚀
