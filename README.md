<div align="center">

# 🚅 OmniRouter

### The Smart Free-Tier AI Router — The Free AI Switchboard

**Pool every free AI provider into one OpenAI- and Anthropic-compatible endpoint.**
Try providers one-by-one, fail over automatically, rotate multiple keys per account,
and auto-pick the **best model for the job** — all for **$0**.

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![PyPI](https://img.shields.io/badge/PyPI-omni--router-3776AB?logo=pypi&logoColor=white)](https://pypi.org/project/omni-router/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://github.com/alizafarbati/omni-router-universal/pkgs/container/omni-router)
[![CI](https://img.shields.io/github/actions/workflow/status/alizafarbati/omni-router-universal/ci.yml?branch=main&label=CI&logo=github)](https://github.com/alizafarbati/omni-router-universal/actions)
[![License](https://img.shields.io/github/license/alizafarbati/omni-router-universal?color=blue)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-1082c3)](#-cross-platform)
[![Tests](https://img.shields.io/badge/Tests-53%20passing-brightgreen)](#-testing)
[![Stars](https://img.shields.io/github/stars/alizafarbati/omni-router-universal?style=social)](https://github.com/alizafarbati/omni-router-universal)

**One endpoint. Every free model. Zero cost. Web UI included.**

```
 ┌─────────────┐    ┌──────────────┐    ┌──────────────────────────────┐
 │  Claude Code│    │   OpenCode   │    │   Codex · Cursor · Continue  │
 │  Codex · CLI │───▶│   SDK / curl │───▶│   any OpenAI-compatible CLI  │
 └─────────────┘    └──────────────┘    └──────────────────────────────┘
        │                    │                        │
        └──────────────────────────┬───────────────────┘
                                   ▼
                    ┌────────────────────────────┐
                    │     ★ OMN IROUTER ★       │  127.0.0.1:8787
                    │  routing · failover ·     │  /ui · /health · /metrics
                    │  key-rotation · health    │  OpenAI + Anthropic
                    └────────────────────────────┘
                                   │
     ┌──────────┬──────────┬──────────────┬──────────────┬─────────────┐
     ▼          ▼          ▼              ▼              ▼             ▼
 ┌────────┐ ┌─────────┐ ┌───────────┐ ┌────────────┐ ┌──────────┐ ┌──────────┐
 │ Gemini │ │OpenRouter│ │ NVIDIA NIM│ │Groq/Cerebras││Cloudflare ││ paid subs │
 │ ×3 accts│ │ 20 free  │ │ DS/Kimi    │ │ /GitHub/Mist││/Together   ││DeepSeek/Go│
 └────────┘ └─────────┘ └───────────┘ └────────────┘ └──────────┘ └──────────┘
```

**[📖 Full Setup Guide](#-setup-guide) · [🖥️ Web UI](#️-web-ui) · [📊 API Reference](#-api-reference) · [🐳 Docker](#-docker) · [🔌 Harness Setup](#-connect-any-agentic-tool)**

</div>

---

## 📚 Table of Contents

- [✨ Features](#-features)
- [🚀 Quick Start (3 Ways)](#-quick-start-3-ways)
- [📖 Setup Guide — Every Provider Step-by-Step](#-setup-guide--every-provider-step-by-step)
- [🖥️ Web UI](#️-web-ui)
- [🔌 Connect Any Agentic Tool](#-connect-any-agentic-tool)
- [🧠 Smart Model Aliases](#-smart-model-aliases)
- [🗂 Providers Supported](#-providers-supported)
- [⚙️ Configuration Deep Dive](#️-configuration-deep-dive)
- [📊 API Reference](#-api-reference)
- [🐳 Docker & Deployment](#-docker--deployment)
- [🔒 Security](#-security)
- [🧪 Testing](#-testing)
- [🛠 Troubleshooting](#-troubleshooting)
- [❓ FAQ](#-faq)
- [🤝 Contributing](#-contributing)
- [🧩 Roadmap](#-roadmap)
- [📄 License](#-license)

---

## ✨ Features

| Feature | Description |
|---|---|
| **Free-first failover** | Tries `Gemini → OpenRouter free → NVIDIA NIM → Groq/Cerebras/Cloudflare/GitHub → paid` in smart order |
| **Per-key rotation** | Multiple API keys per provider (e.g. 3 Google accounts) are tried one-by-one; exhausted keys (429/403) get a **long circuit-breaker cooldown**, healthy ones stay in rotation |
| **Capability routing** | `router-code`, `router-reason`, `router-vision`, `router-fast`, `router-long` auto-pick the **best free model** for the task |
| **Smart fallback** | If an explicit model fails everywhere, it **degrades to the auto-chain** instead of erroring |
| **Dual API** | Serves **both** OpenAI `/v1/chat/completions` and Anthropic `/v1/messages` (full tool-call + SSE streaming translation) |
| **Web UI** | Live dashboard at `/ui` — provider health, metrics, 47 models, request log, capability viz |
| **Gateway model discovery** | `/v1/models` returns the full catalog in **both** OpenAI and Anthropic formats — Claude Code lists every model in its `/model` picker |
| **Health + Metrics** | `/health` (JSON) + `/metrics` (Prometheus) + `/v1/logs` (last 100 requests) |
| **Virtual keys** | Per-client API keys with RPM + daily limits (`configs/virtual_keys.json`) |
| **Circuit breakers** | 429/403 → 1-hr cooldown; 502/503/504/529 → retry once with `Retry-After` backoff + 30s cooldown |
| **Zero hard dependencies** | Stdlib-only core; optional `curl_cffi` for browser-identical TLS |
| **Cross-platform** | Windows / Linux / macOS, single-file core, `pip` + `docker` |

---

## 🚀 Quick Start (3 Ways)

### Way 1 — pip (recommended for dev)

```bash
pip install omni-router          # or: pip install -e . (from git clone)
pip install -r requirements.txt  # adds curl_cffi (recommended, beats Cloudflare)

# set at least one free key (see Setup Guide below)
export OPENROUTER_KEY="sk-or-v1-..."
export GOOGLE_AI_KEY="AIza..."

# start
omni-router                      # or: python -m omni_router
# → http://127.0.0.1:8787  ( /health  /metrics  /ui  /v1/models )
```

### Way 2 — Docker (recommended for homelab / server)

```bash
# 1. clone + configure
git clone https://github.com/alizafarbati/omni-router-universal && cd omni-router-universal
cp configs/providers.example.json configs/providers.json  # put keys in "keys": [] or use env vars

# 2. run
docker compose up --build -d
# → http://127.0.0.1:8787/ui

# logs
docker compose logs -f
```

### Way 3 — Manual (single file, no install)

```bash
curl -O https://raw.githubusercontent.com/alizafarbati/omni-router-universal/main/omni_router/omni_router.py
GOOGLE_AI_KEY="..." OPENROUTER_KEY="..." python omni_router.py
```

**Verify any way:**

```bash
curl http://127.0.0.1:8787/health          # {"status":"ok",...}
curl http://127.0.0.1:8787/metrics         # Prometheus
curl http://127.0.0.1:8787/v1/models | jq  # 47 models
open http://127.0.0.1:8787/ui              # dashboard
```

---

## 📖 Setup Guide — Every Provider Step-by-Step

> **You only need ONE free key to start.** Add more to multiply your quota. The router auto-detects whatever you set.

### 1. Google AI Studio (Gemini) — 3-account rotation ⭐ primary

- Go to **https://aistudio.google.com/app/apikey** → **Create API key** → copy `AIza...`
- Free quota: **20 req/day per project per model** (gemini-flash-latest → 20, gemini-2.5-flash-lite → higher). **Per-project**, so 3 Google accounts = 3× quota.
- Add to router:
  ```bash
  export GOOGLE_AI_KEY="AIza..."  # single account
  # OR for rotation, put 3 keys in configs/providers.json:
  # "google-ai-studio": { "keys": ["AIza-aaa","AIza-bbb","AIza-ccc"] }
  ```
- Models: `gemini-flash-latest` (default), `gemini-3.7-flash`, `gemini-2.5-flash`

### 2. OpenRouter — 20 free models, $10 unlock

- Sign up at **https://openrouter.ai/keys** → **Create Key** → `sk-or-v1-...`
- Free: **50 req/day** across `:free` models. **One-time $10 credit purchase → 1000 free req/day forever** (even at $0 balance) — the single best lever.
- Models (all `:free` suffix): `dots-studio/dots-3-note-preview:free` (280B MoE 512K, top coder), `nvidia/nemotron-3-ultra-550b-a55b:free` (1M), `z-ai/glm-5.2:free`, `cohere/north-mini-code:free`, `google/gemma-4-31b-it:free`, `openai/gpt-oss-20b:free`, `openrouter/free` (auto-picks best free per prompt).
  ```bash
  export OPENROUTER_KEY="sk-or-v1-..."
  ```

### 3. NVIDIA NIM — frontier free

- Get free key at **https://build.nvidia.com** → **Get API Key** → `nvapi-...`
- Free monthly credits include `deepseek-ai/deepseek-v4-flash-0731`, `moonshotai/kimi-k3` (3T!), `z-ai/glm-5.2`, `meta/llama-4-maverick`.
  ```bash
  export NVIDIA_NIM_KEY="nvapi-..."
  ```

### 4. Groq — fastest inference

- **https://console.groq.com/keys** → Create → `gsk_...`
- Free: 30 RPM / 1000 RPD per model. Models: `llama-3.3-70b-versatile`, `gpt-oss-120b`.
  ```bash
  export GROQ_KEY="gsk_..."
  ```

### 5. Cerebras — 1M tokens/day

- **https://cloud.cerebras.ai** → API Keys → `csk-...`
  ```bash
  export CEREBRAS_KEY="csk-..."
  ```

### 6. Cloudflare Workers AI — 10k neurons/day

- **https://dash.cloudflare.com** → Workers & Pages → AI → Create API token + note **Account ID**.
  ```bash
  export CF_KEY="..."
  export CF_ACCOUNT_ID="..."
  ```

### 7. GitHub Models — free GPT-4.1

- **https://github.com/settings/tokens** → **Generate new token (fine-grained)** → allow `Models: Read` → `github_pat_...`
  ```bash
  export GH_PAT="github_pat_..."
  ```

### 8. Mistral — Experiment tier

- **https://console.mistral.ai/api-keys/** → `...`
  ```bash
  export MISTRAL_KEY="..."
  ```

### 9. OpenCode Go / DeepSeek / Novita — paid fallbacks

Already have them? Add as backup; router only uses them when all free tiers are exhausted:
```bash
export OPENCODE_GO_KEY="sk-..."   # https://opencode.ai
export DEEPSEEK_KEY="sk-..."      # https://platform.deepseek.com
export NOVITA_KEY="sk-..."        # https://novita.ai (referral credits)
```

**Tip:** Create **multiple accounts/projects** per provider (different emails) to multiply free quotas. The router's per-key rotation handles it automatically.

---

## 🖥️ Web UI

Open **`http://127.0.0.1:8787/ui`** (or `/dashboard`) for the live dashboard:

- **KPIs** — providers ok/total, requests proxied, models, mode
- **Providers** — per-key health cards (ok / cooling(30s) / err), ok/fail counts, last error
- **Capability routing** — which model each `router-*` alias currently picks
- **Models** — 47 models with search, free/paid tags, provider column
- **Recent requests** — last 100 (model, provider, tokens, latency, status)
- **Prometheus** — live `/metrics` preview

No build step — single HTML, works offline.

---

## 🔌 Connect Any Agentic Tool

### OpenAI-compatible (OpenCode, Codex, Cursor, Continue, any SDK)

```python
from openai import OpenAI
client = OpenAI(base_url="http://127.0.0.1:8787/v1", api_key="anything")
resp = client.chat.completions.create(
    model="router-code",  # or router-auto / any explicit model
    messages=[{"role": "user", "content": "Write a CLI in Rust"}],
)
print(resp.choices[0].message.content)
```

```bash
# curl
curl http://127.0.0.1:8787/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"router-auto","messages":[{"role":"user","content":"Hello!"}]}'
```

**OpenCode** (`~/.config/opencode/opencode.jsonc`):
```jsonc
{ "provider": { "omni-router": {
  "npm": "@ai-sdk/openai-compatible",
  "options": { "baseURL": "http://127.0.0.1:8787/v1", "apiKey": "local" },
  "models": { "router-auto": {}, "router-code": {}, "gemini-flash-latest": {} }
}}}
```

### Claude Code (Anthropic)

```bash
export ANTHROPIC_BASE_URL="http://127.0.0.1:8787"
export ANTHROPIC_API_KEY="omni-router-local"
export ANTHROPIC_MODEL="router-auto"   # or any model from /v1/models
claude
```

Or persist in `~/.claude/settings.json`:

```jsonc
{ "env": {
  "ANTHROPIC_BASE_URL": "http://127.0.0.1:8787",
  "ANTHROPIC_API_KEY": "omni-router-local",
  "ANTHROPIC_MODEL": "router-auto",
  "CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY": "1"
}}
```

All 47 models then appear in Claude Code's `/model` picker. Use `router-code` for coding, `router-reason` for reasoning.

### Codex / Cursor / Continue

Same as OpenAI-compatible — just set `baseURL` to `http://127.0.0.1:8787/v1`.

---

## 🧠 Smart Model Aliases

| Alias | Auto-picks | Fallback chain |
|---|---|---|
| `router-auto` | smart free-first failover (**default**) | Gemini → OpenRouter → NIM → paid |
| `router-code` | best free coder | Dots3 512K / Nemotron-Ultra → DeepSeek/Kimi |
| `router-reason` | best reasoning | GLM-5.2 / Gemini → DeepSeek-reasoner |
| `router-vision` | vision-capable | Nemotron-Nano-VL / Gemini / Qwen |
| `router-fast` | lowest-latency | Nemotron-Lightning / Gemini-2.5 |
| `router-long` | longest-context (1M) | Nemotron-Ultra / Gemini |
| `router-smart` | alias of router-auto | — |

Use any **explicit model ID** from `/v1/models` (e.g. `nvidia/nemotron-3-ultra-550b-a55b:free`) — if it fails everywhere, the router **degrades to the auto-chain** instead of 503.

---

## 🗂 Providers Supported

| Provider | Free tier | Models | Auth env |
|---|---|---|---|
| **Google AI Studio** | 20 req/day/project/model | `gemini-flash-latest`, `gemini-3.7-flash`, `gemini-2.5-flash` | `GOOGLE_AI_KEY` (or `keys: []` for rotation) |
| **OpenRouter** | 20 free models, 50 req/day (**1000/day with $10**) | Dots3, Nemotron-Ultra, GLM-5.2, Gemma-4, Laguna… | `OPENROUTER_KEY` |
| **NVIDIA NIM** | free monthly credits | DeepSeek V4, Kimi-K3, GLM-5.2, Llama-4 | `NVIDIA_NIM_KEY` |
| **Groq** | 30 RPM / 1000 RPD | Llama 3.3 70B, GPT-OSS 120B | `GROQ_KEY` |
| **Cerebras** | ~1M tokens/day | Llama 3.3 70B | `CEREBRAS_KEY` |
| **Cloudflare** | 10k neurons/day | Llama 3.3 70B (Workers AI) | `CF_KEY` + `CF_ACCOUNT_ID` |
| **GitHub Models** | free via PAT | GPT-4.1, GPT-4o-mini | `GH_PAT` |
| **Mistral** | free Experiment tier | Mistral Small | `MISTRAL_KEY` |
| **OpenCode Go** | paid sub (~$60/mo incl.) | DeepSeek V4, Kimi, Qwen | `OPENCODE_GO_KEY` |
| **Novita** | referral credits | Llama 3.3 70B | `NOVITA_KEY` |
| **DeepSeek** | direct paid API | deepseek-chat, deepseek-reasoner | `DEEPSEEK_KEY` |

> **Target:** ~**10M tokens/month free** (60 req/day Gemini ×3 + 50/day OpenRouter) → **~210M with Go sub** → **~600M-1B+ with $10 OpenRouter unlock + more accounts**. Daily **request caps** (not token caps) are the limiter — honest math, not hype.

---

## ⚙️ Configuration Deep Dive

### Env vars (zero-config, recommended)

```bash
export OMNI_PORT=8787
export OMNI_HOST=127.0.0.1          # 0.0.0.0 to expose (Docker sets this)
export OMNI_CONFIG=/path/to/providers.json
export GOOGLE_AI_KEY="AIza..."
export OPENROUTER_KEY="sk-or-v1-..."
# ... any provider above ...
export OMNI_VIRTUAL_KEYS='{"keys":{"sk-client-1":{"name":"alice","rpm":60,"daily_limit":1000}}}'
```

### `providers.json` (gitignored — secrets stay local)

```bash
cp configs/providers.example.json configs/providers.json
# put keys in "keys": ["sk-..."] arrays or rely on env vars
```

```jsonc
{
  "providers": [{
    "name": "google-ai-studio",
    "base": "https://generativelanguage.googleapis.com/v1beta/openai",
    "key_env": "GOOGLE_AI_KEY",
    "keys": ["AIza-aaa","AIza-bbb","AIza-ccc"], // multi-key rotation
    "models": ["gemini-flash-latest", "gemini-3.7-flash"],
    "routed": ["gemini-flash-latest"],          // model used for router-auto
    "free": true,
    "cooldown": 30
  }]
}
```

### Virtual keys (per-client isolation)

```json
// configs/virtual_keys.json (or OMNI_VIRTUAL_KEYS env)
{ "keys": {
  "sk-client-demo-001": { "name": "alice", "rpm": 60, "daily_limit": 1000 },
  "sk-client-demo-002": { "name": "bob",   "rpm": 30, "daily_limit": 500 }
}}
```

Clients then send `Authorization: Bearer sk-client-demo-001`. When set, **all** requests require a valid virtual key.

### Add your own OpenAI-compatible provider

```jsonc
{ "name": "my-provider", "base": "https://your-endpoint.com/v1",
  "key_env": "MY_KEY", "models": ["*"], "routed": ["your-model"], "free": true, "cooldown": 30 }
```

---

## 📊 API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/ui`, `/dashboard` | GET | Web UI (HTML) |
| `/health`, `/v1/health` | GET | JSON: per-provider status, ok/fail, cooldowns, last error |
| `/metrics`, `/v1/metrics` | GET | Prometheus: `omni_router_requests_total`, `tokens_input/output`, `uptime`, `provider_requests` |
| `/v1/logs`, `/logs` | GET | Last 100 requests (model, provider, tokens, ms, status) |
| `/v1/models`, `/models` | GET | Model catalog — OpenAI format by default, Anthropic format when `anthropic-version` or Claude UA is present |
| `/v1/chat/completions` | POST | OpenAI chat (streaming + tools) |
| `/v1/messages` | POST | Anthropic messages (translated, also accepts `?beta=true`) |

**Request headers set by router:** `X-Router-Provider`, `X-Router-Attempts`, `X-Router-Latency-ms`

**`curl` examples:**

```bash
# OpenAI
curl http://127.0.0.1:8787/v1/chat/completions -H "Content-Type: application/json" \
  -d '{"model":"router-code","messages":[{"role":"user","content":"Write a CLI in Rust"}]}'

# Anthropic
curl http://127.0.0.1:8787/v1/messages -H "Content-Type: application/json" -H "anthropic-version: 2023-06-01" \
  -d '{"model":"router-auto","max_tokens":100,"messages":[{"role":"user","content":"Hello"}]}'

# With virtual key
curl http://127.0.0.1:8787/v1/chat/completions -H "Authorization: Bearer sk-client-demo-001" ...
```

---

## 🐳 Docker & Deployment

### Docker Compose (one command)

```bash
cp configs/providers.example.json configs/providers.json  # add keys
docker compose up --build -d
open http://127.0.0.1:8787/ui
```

### Systemd (Linux)

```ini
# /etc/systemd/system/omni-router.service
[Unit]
Description=OmniRouter
After=network.target
[Service]
Environment=OPENROUTER_KEY=sk-or-v1-...
Environment=GOOGLE_AI_KEY=AIza...
WorkingDirectory=/opt/omni-router-universal
ExecStart=/usr/bin/python3 -m omni_router
Restart=always
[Install]
WantedBy=multi-user.target
```

### Windows Service

```powershell
# via Startup folder (already installed by omni-router.cmd) or:
nssm install OmniRouter "C:\Python314\pythonw.exe" "C:\path\to\omni_router\omni_router.py"
```

### Cloud (Fly, Railway, Render)

Set env vars in the dashboard, expose `OMNI_HOST=0.0.0.0`, `OMNI_PORT=8787`. The Dockerfile is ready.

---

## 🔒 Security

- **No secrets committed.** Keys from env vars or gitignored `providers.json`. Example config ships with empty `keys`.
- **Binds to 127.0.0.1** by default. Set `OMNI_HOST=0.0.0.0` only behind an authenticating reverse proxy + TLS.
- **Free-tier providers may train on your data** — keep sensitive data on paid/private routes.
- **Virtual keys** isolate clients; combine with a reverse proxy for TLS + IP allowlisting.
- See [SECURITY.md](SECURITY.md) for disclosure policy.

---

## 🧪 Testing

```bash
pip install -r requirements.txt
pytest -q              # 53 tests (unit + integration, harness auto-skips without keys)
pytest -q -k "not harness"  # fast, no live AI calls
```

**CI:** 3-OS matrix (ubuntu/win/macos × py 3.9/3.11/3.12) + Docker smoke + daily smoke (cron).

---

## 🛠 Troubleshooting

| Symptom | Fix |
|---|---|
| `429 Quota exceeded` on Gemini | Wait for daily reset, add more Google accounts/projects, or use `router-auto` to fall through |
| Empty response on small `max_tokens` | Gemini "thinking" burns budget — keep `max_tokens` generous (router caps at 4096) |
| `403` from a provider (Cloudflare) | `pip install -r requirements.txt` — `curl_cffi` beats bot checks |
| All providers fail → 503 | Check keys are set; `curl http://127.0.0.1:8787/health` shows which are `cooling` |
| Claude Code `unrecognized_model` | Cosmetic — set `CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT=1` (already in `claude-omni.cmd`) |
| Docker health never ready | Ensure `OMNI_HOST=0.0.0.0` (already in Dockerfile); check `docker logs omni-router` |
| `address already in use` | Another router is running — `lsof -i :8787` or check `Startup/OmniRouter.cmd` |

---

## ❓ FAQ

**How many tokens/month?** ~10M free (honest), ~210M with Go sub, ~600M-1B+ if you stack the $10 OpenRouter unlock + more Google accounts. Request caps, not token caps, are the limiter.

**Do I need all providers?** No — one free key is enough to start. Each extra key multiplies your quota.

**Can I use my paid keys?** Yes — add them as providers with `"free": false`; router only uses them when free tiers are exhausted.

**Is it private?** Router is local. Free providers may log. Use virtual keys + paid routes for sensitive data.

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

**Ideas wanted:** more providers, per-model cost estimator, webhooks on provider cooldown, more capability tags.

---

## 🧩 Roadmap

- [x] Free-first failover + multi-key rotation
- [x] Capability routing (`router-code` / `router-reason` / …)
- [x] OpenAI + Anthropic dual API, streaming, tools
- [x] Gateway model discovery for Claude Code
- [x] Docker + docker-compose
- [x] PyPI (`pip install omni-router`)
- [x] Prometheus `/metrics` + cost ledger
- [x] Web UI (`/ui`) + request logging
- [x] Virtual API keys
- [x] Daily smoke (cron) + retries with backoff
- [x] Grafana dashboard (`configs/grafana-dashboard.json`)
- [x] Auto model-catalog refresh from OpenRouter (hourly)
- [x] K8s manifest (`configs/k8s-manifest.yaml`)

---

## 📄 License

MIT © 2026 [Ali Zafar](https://github.com/alizafarbati). See [LICENSE](LICENSE).

---

<div align="center">

**Built with ❤️ by [Ali Zafar](https://github.com/alizafarbati)** — stack every free AI into one infinite hose. 🚀

</div>
