# OmniRouter — Smart Free-Tier AI Router

Pool **every free AI provider** into one OpenAI- and Anthropic-compatible endpoint.
Try providers one-by-one, fail over automatically, rotate multiple keys per account,
and auto-pick the **best model for the job** — all for $0.

Point **any** client (Claude Code, OpenCode, Codex, Cursor, curl) at one local URL and it
silently routes through whatever free provider is healthy, rotating accounts and models
as quotas fill up.

---

## ✨ Features

- **Free-first failover** — tries Gemini → OpenRouter free → NVIDIA NIM → Groq/Cerebras/
  Cloudflare/GitHub → your paid fallbacks, in smart order.
- **Per-key rotation** — multiple API keys per provider (e.g. 3 Google accounts) are
  tried one-by-one; exhausted keys (429) get a long circuit-breaker cooldown, healthy
  ones stay in rotation.
- **Capability routing** — `router-code`, `router-reason`, `router-vision`,
  `router-fast`, `router-long` auto-pick the best free model for the task.
- **Smart fallback** — if an explicit model fails everywhere, it degrades to the auto-chain
  instead of erroring.
- **Dual API** — serves both OpenAI `/v1/chat/completions` and Anthropic `/v1/messages`
  (full tool-call + SSE streaming translation). Works as a drop-in for Claude Code.
- **Gateway model discovery** — `/v1/models` returns the full catalog in both OpenAI and
  Anthropic formats, so Claude Code lists every model in its `/model` picker.
- **Health dashboard** — `/health` shows live per-key status, ok/fail counts, cooldowns.
- **Zero hard dependencies** — stdlib-only core; optional `curl_cffi` for browser-identical
  TLS (beats Cloudflare bot checks).
- **Cross-platform** — Windows / Linux / macOS.

---

## 🚀 Quick Start

```bash
# 1. Install optional (recommended) transport to beat Cloudflare bot detection
pip install -r requirements.txt

# 2. Configure your API keys (env vars, or a local gitignored providers.json)
export GOOGLE_AI_KEY="..."
export OPENROUTER_KEY="sk-or-v1-..."
export NVIDIA_NIM_KEY="..."
export GROQ_KEY="..."
# ... any of the providers below ...

# 3. Start the router
python omni_router/omni_router.py          # or: scripts/omni-router.sh  /  omni-router.cmd

# 4. Use it
curl http://127.0.0.1:8787/v1/models
```

You can also copy `configs/providers.example.json` to `configs/providers.json` (gitignored)
and put API keys in the `keys` arrays — same format, secrets stay off GitHub.

---

## 🔌 Connect Clients

**OpenAI-compatible** (OpenCode, Codex, Cursor, SDKs):
```
base_url = http://127.0.0.1:8787/v1
api_key  = anything
model    = router-auto
```

**Claude Code** (Anthropic interface):
```bash
export ANTHROPIC_BASE_URL="http://127.0.0.1:8787"
export ANTHROPIC_API_KEY="omni-router-local"
export ANTHROPIC_MODEL="router-auto"
claude
```
or add to `~/.claude/settings.json` → `env` block. All 40+ models then show up in
Claude Code's `/model` picker.

---

## 🧠 Smart Model Aliases

| Alias | Auto-picks |
|---|---|
| `router-auto` | smart free-first failover (default) |
| `router-code` | best free coder (Dots3 512K / Nemotron-Ultra → DeepSeek/Kimi) |
| `router-reason` | best reasoning (GLM-5.2 / Gemini → DeepSeek-reasoner) |
| `router-vision` | vision-capable models |
| `router-fast` | lowest-latency models |
| `router-long` | longest-context (1M) models |
| `router-smart` | alias of router-auto |

Or use any explicit model ID from `/v1/models` (e.g. `nvidia/nemotron-3-ultra-550b-a55b:free`).

---

## 🗂 Providers Supported

Built-in presets (see `configs/providers.example.json`):

| Provider | Free tier | API key |
|---|---|---|
| Google AI Studio | Gemini Flash family (free, per-project quota) | `GOOGLE_AI_KEY` |
| OpenRouter | 20 free models, 50 req/day (1000/day with $10) | `OPENROUTER_KEY` |
| NVIDIA NIM | DeepSeek V4, Kimi-K3, GLM-5.2 | `NVIDIA_NIM_KEY` |
| Groq | Llama 3.3 70B, GPT-OSS | `GROQ_KEY` |
| Cerebras | Llama 3.3 70B (~1M tok/day) | `CEREBRAS_KEY` |
| Cloudflare | Workers AI (10k neurons/day) | `CF_KEY` + `CF_ACCOUNT_ID` |
| GitHub Models | GPT-4.1 (via PAT) | `GH_PAT` |
| Mistral | free Experiment tier | `MISTRAL_KEY` |
| OpenCode Go | 27 models (~$60/mo incl.) | `OPENCODE_GO_KEY` |
| Novita | referral credits | `NOVITA_KEY` |
| DeepSeek | direct paid API | `DEEPSEEK_KEY` |

Add any OpenAI-compatible endpoint by appending a provider block — comes alive the moment
a key is set.

---

## 🔒 Security

- **No secrets committed.** Keys come from environment variables or a gitignored local
  `providers.json`. The example config ships with empty `keys` arrays.
- The router binds to `127.0.0.1` only (set `OMNI_HOST` to change).
- Free-tier providers may train on your data — keep sensitive data on paid/private routes.

---

## 📄 License

MIT © 2026 Ali Zafar. See [LICENSE](LICENSE).

---

*Built to stack every free AI into one infinite hose. HAIL GOD SYNDICATE.*
