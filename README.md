<div align="center">

# 🚅 OmniRouter

### The Smart Free-Tier AI Router

**Pool every free AI provider into one OpenAI- and Anthropic-compatible endpoint.**
Try providers one-by-one, fail over automatically, rotate multiple keys per account,
and auto-pick the **best model for the job** — all for **$0**.

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/github/license/alizafarbati/omni-router-universal?color=blue)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-1082c3)](#-cross-platform)
[![Stars](https://img.shields.io/github/stars/alizafarbati/omni-router-universal?style=social)](https://github.com/alizafarbati/omni-router-universal)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING)

**One endpoint. Every free model. Zero cost.**

```
 ┌─────────────┐    ┌──────────────┐    ┌──────────────────────────────┐
 │  Claude Code│    │   OpenCode   │    │   Codex · Cursor · curl ·    │
 │  Codex · CLI │───▶│   SDK / curl │───▶│   any OpenAI-compatible CLI  │
 └─────────────┘    └──────────────┘    └──────────────────────────────┘
        │                    │                        │
        └──────────────────────────┬───────────────────┘
                                   ▼
                    ┌────────────────────────────┐
                    │     ★ OMN IROUTER ★       │  127.0.0.1:8787
                    │  routing · failover ·     │
                    │  key-rotation · health    │
                    └────────────────────────────┘
                                   │
     ┌──────────┬──────────┬──────────────┬──────────────┬─────────────┐
     ▼          ▼          ▼              ▼              ▼             ▼
 ┌────────┐ ┌─────────┐ ┌───────────┐ ┌────────────┐ ┌──────────┐ ┌──────────┐
 │ Gemini │ │OpenRouter│ │ NVIDIA NIM│ │Groq/Cerebras││Cloudflare ││ paid subs │
 │ ×3 accts│ │ 20 free  │ │ DS/Kimi    │ │ /GitHub/Mist││/Together   ││DeepSeek/Go│
 └────────┘ └─────────┘ └───────────┘ └────────────┘ └──────────┘ └──────────┘
```

</div>

---

## 📚 Table of Contents
- [✨ Features](#-features)
- [🚀 Quick Start](#-quick-start)
- [🔌 Connect Clients](#-connect-clients)
- [🧠 Smart Model Aliases](#-smart-model-aliases)
- [🗂 Providers Supported](#-providers-supported)
- [⚙️ Advanced Configuration](#️-advanced-configuration)
- [🔒 Security](#-security)
- [📊 Endpoints & CLI Reference](#-endpoints--cli-reference)
- [🛠 Troubleshooting](#-troubleshooting)
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
| **Gateway model discovery** | `/v1/models` returns the full catalog in **both** OpenAI and Anthropic formats — Claude Code lists every model in its `/model` picker |
| **Health dashboard** | `/health` shows live per-key status, ok/fail counts, cooldowns |
| **Circuit breakers** | 429/403 → 1-hr cooldown; 503 → 30 s; auto-healing |
| **Zero hard dependencies** | Stdlib-only core; optional `curl_cffi` for browser-identical TLS |
| **Cross-platform** | Windows / Linux / macOS, single-file core |

---

## 🚀 Quick Start

### 1. Install (optional transport to beat Cloudflare)
```bash
pip install -r requirements.txt     # adds curl_cffi (recommended)
```

### 2. Configure your API keys
Set environment variables **or** copy the example config (see [Advanced Configuration](#️-advanced-configuration)):

```bash
export GOOGLE_AI_KEY="AIza..."        # Google AI Studio
export OPENROUTER_KEY="sk-or-v1-..."  # OpenRouter
export NVIDIA_NIM_KEY="nvapi-..."     # NVIDIA NIM (free: build.nvidia.com)
export GROQ_KEY="gsk_..."             # Groq free
export CEREBRAS_KEY="csk-..."         # Cerebras free
export GH_PAT="github_pat_..."        # GitHub Models
# ... any provider below ...
```

### 3. Start the router
```bash
# Any platform:
python omni_router/omni_router.py

# Or use the launchers:
#   Windows:   scripts\omni-router.cmd
#   Linux/mac: scripts/omni-router.sh [port]
```

### 4. Use it
```bash
# list all 40+ models
curl http://127.0.0.1:8787/v1/models
# health dashboard
curl http://127.0.0.1:8787/health
# chat
curl http://127.0.0.1:8787/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"router-auto","messages":[{"role":"user","content":"Hello!"}]}'
```

---

## 🔌 Connect Clients

### OpenAI-compatible (OpenCode, Codex, Cursor, any SDK)
```python
from openai import OpenAI
client = OpenAI(
    base_url="http://127.0.0.1:8787/v1",
    api_key="anything",
)
resp = client.chat.completions.create(
    model="router-code",
    messages=[{"role": "user", "content": "Write a CLI in Rust"}],
)
```

### Claude Code (Anthropic interface)
```bash
export ANTHROPIC_BASE_URL="http://127.0.0.1:8787"
export ANTHROPIC_API_KEY="omni-router-local"
export ANTHROPIC_MODEL="router-auto"
claude
```
Or persist in `~/.claude/settings.json` → `env` block. All 40+ models appear in Claude Code's `/model` picker.

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

Use any **explicit model ID** from `/v1/models` (e.g. `nvidia/nemotron-3-ultra-550b-a55b:free`).

---

## 🗂 Providers Supported

| Provider | Free tier | Models | Auth |
|---|---|---|---|
| **Google AI Studio** | Gemini Flash family (per-project quota) | `gemini-flash-latest`, `gemini-3.7-flash`, `gemini-2.5-flash` | `GOOGLE_AI_KEY` |
| **OpenRouter** | 20 free models, 50 req/day (1000/day with $10) | Dots3, Nemotron-Ultra, GLM-5.2, Gemma-4, Laguna… | `OPENROUTER_KEY` |
| **NVIDIA NIM** | free (build.nvidia.com) | DeepSeek V4, Kimi-K3, GLM-5.2, Llama-4 | `NVIDIA_NIM_KEY` |
| **Groq** | free tier | Llama 3.3 70B, GPT-OSS 120B | `GROQ_KEY` |
| **Cerebras** | ~1M tokens/day | Llama 3.3 70B | `CEREBRAS_KEY` |
| **Cloudflare** | 10k neurons/day | Llama 3.3 70B (Workers AI) | `CF_KEY` + `CF_ACCOUNT_ID` |
| **GitHub Models** | free via PAT | GPT-4.1, GPT-4o-mini | `GH_PAT` |
| **Mistral** | free Experiment tier | Mistral Small | `MISTRAL_KEY` |
| **OpenCode Go** | paid sub (~$60/mo incl.) | DeepSeek V4, Kimi, Qwen | `OPENCODE_GO_KEY` |
| **Novita** | referral credits | Llama 3.3 70B | `NOVITA_KEY` |
| **DeepSeek** | direct paid API | deepseek-chat, deepseek-reasoner | `DEEPSEEK_KEY` |

> Target of ~**600M–1B+ tokens/month** when all providers are stacked. You will run out of **time, not tokens**.

---

## ⚙️ Advanced Configuration

### A. Environment variables (zero-config)
```bash
# port + host overrides
export OMNI_PORT=8787
export OMNI_HOST=127.0.0.1
# config path override
export OMNI_CONFIG=/path/to/providers.json
```

### B. Local providers.json (gitignored — secrets stay local)
```bash
cp configs/providers.example.json configs/providers.json
# then put keys in the "keys" arrays or rely on env vars
```

Example block:
```jsonc
{
  "providers": [
    {
      "name": "google-ai-studio",
      "base": "https://generativelanguage.googleapis.com/v1beta/openai",
      "key_env": "GOOGLE_AI_KEY",          // prefer env var
      "keys": ["AIza-..."],                // OR inline keys (multi-key rotation)
      "models": ["gemini-flash-latest", "gemini-3.7-flash"],
      "routed": ["gemini-flash-latest"],   // model used for router-auto
      "free": true,
      "cooldown": 30
    }
  ]
}
```

### C. Add your own OpenAI-compatible provider
Any endpoint that accepts `POST /chat/completions` with a Bearer key works:
```jsonc
{ "name": "my-provider", "base": "https://your-endpoint.com/v1",
  "key_env": "MY_KEY", "models": ["*"], "routed": ["your-model"], "free": true, "cooldown": 30 }
```

---

## 🔒 Security

- **No secrets committed.** Keys come from env vars or a **gitignored** `providers.json`. The example config ships with empty `keys` arrays.
- Binds to `127.0.0.1` only by default (set `OMNI_HOST` to expose).
- Free-tier providers may train on your data — keep **sensitive data on paid/private routes**.
- The repo ships **zero** API keys, tokens, personal paths, or machine identifiers.

---

## 📊 Endpoints & CLI Reference

| Endpoint | Method | Description |
|---|---|---|
| `/v1/models` | GET | Model catalog (OpenAI or Anthropic format by UA/header) |
| `/v1/chat/completions` | POST | OpenAI chat with streaming + tools |
| `/v1/messages` | POST | Anthropic messages (translated) |
| `/health` | GET | Live provider health, ok/fail, cooldowns |
| `/v1/responses` | POST | OpenAI Responses (passthrough) |

**Response headers:** `X-Router-Provider`, `X-Router-Attempts`, `X-Router-Latency-ms`

---

## 🛠 Troubleshooting

| Symptom | Fix |
|---|---|
| `429 Quota exceeded` on Gemini | Wait for daily reset, add more Google accounts/projects, or use `router-auto` to fall through |
| Empty response on small `max_tokens` | Gemini "thinking" burns budget — the router caps at 4096; keep `max_tokens` generous for chat |
| Cloudflare 403 from a provider | Install `curl_cffi` (`pip install -r requirements.txt`) for browser-identical TLS |
| All providers fail → 503 | Check keys are set; `/health` shows which are cooling |
| Claude Code "unrecognized_model" warning | Cosmetic — set `CLAUDE_CODE_DISABLE_UNKNOWN_MODEL_WINDOW_ENFORCEMENT=1` |

---

## 🤝 Contributing

Contributions are welcome! Please open an issue or PR. See [CONTRIBUTING](CONTRIBUTING) for guidelines.

**Ideas wanted:** model catalog auto-fetch, prometheus metrics, cost ledger, per-user budgets, Docker/K8s deployment, PyPI packaging.

---

## 🧩 Roadmap

- [x] Free-first failover + multi-key rotation
- [x] Capability routing (`router-code` / `router-reason` / …)
- [x] OpenAI + Anthropic dual API, streaming, tools
- [x] Gateway model discovery for Claude Code
- [ ] Docker image + docker-compose
- [ ] PyPI package (`pip install omni-router`)
- [ ] Prometheus `/metrics` + cost ledger
- [ ] Admin web UI
- [ ] Auto model-catalog refresh from OpenRouter/provider APIs

---

## 📄 License

MIT © 2026 [Ali Zafar](https://github.com/alizafarbati). See [LICENSE](LICENSE).

---

<div align="center">

**Built to stack every free AI into one infinite hose.** 🚀🔥

*HAIL GOD SYNDICATE.*

</div>
