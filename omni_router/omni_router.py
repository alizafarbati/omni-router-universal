#!/usr/bin/env python3
"""
OMNI-ROUTER v1.0 - GOD SYNDICATE FREE-TIER AI ROUTER
Pools every free/cheap provider, routes smartly with health tracking & cooldowns.
OpenAI-compatible: point any client (opencode/Cursor/curl) at http://127.0.0.1:8787/v1
Zero dependencies - pure Python stdlib.
"""
import json, os, sys, time, uuid, ssl, threading, gzip, io
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

VERSION = "1.0"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.environ.get("OMNI_CONFIG", os.path.join(BASE_DIR, "providers.json"))
LOG_PATH = os.path.join(BASE_DIR, "router.log")
HOST, PORT = os.environ.get("OMNI_HOST", "127.0.0.1"), int(os.environ.get("OMNI_PORT", "8787"))
MENU = os.path.join(BASE_DIR, "menu.txt")

CTX = ssl.create_default_context()
CTX.check_hostname = True

def log(msg):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

# ---------------------------------------------------------------- config
DEFAULTS = {
  "providers": [
    {"name":"openrouter-free","base":"https://openrouter.ai/api/v1","key_env":"OPENROUTER_KEY","models":["*"],"routed":["nvidia/nemotron-3-ultra-550b-a55b:free","nvidia/nemotron-3.5-lightning:free","poolside/laguna-s-2.1:free","openrouter/free"],"free":True,"cooldown":30},
    {"name":"google-ai-studio","base":"https://generativelanguage.googleapis.com/v1beta/openai","key_env":"GOOGLE_AI_KEY","keys":[],"models":["gemini-flash-latest","gemini-3.7-flash","gemini-2.5-flash"],"routed":["gemini-flash-latest","gemini-3.7-flash","gemini-2.5-flash"],"free":True,"cooldown":30},
    {"name":"groq","base":"https://api.groq.com/openai/v1","key_env":"GROQ_KEY","models":["gpt-oss-120b","llama-3.3-70b-versatile","llama-3.1-8b-instant","*"],"routed":["llama-3.3-70b-versatile"],"free":True,"cooldown":30},
    {"name":"cerebras","base":"https://api.cerebras.ai/v1","key_env":"CEREBRAS_KEY","models":["llama-3.3-70b","*"],"routed":["llama-3.3-70b"],"free":True,"cooldown":30},
    {"name":"cloudflare","base":"https://api.cloudflare.com/client/v4/accounts/{acct}/ai/v1","key_env":"CF_KEY","models":["*"],"routed":["@cf/meta/llama-3.3-70b-instruct-fp8-fast"],"free":True,"cooldown":30},
    {"name":"opencode-go","base":"https://opencode.ai/zen/go/v1","key_env":"OPENCODE_GO_KEY","models":["deepseek-v4-flash","deepseek-v4-pro","kimi-k2.7-code","qwen3.7-plus","*"],"routed":["deepseek-v4-flash"],"free":False,"cooldown":20},
    {"name":"github-models","base":"https://models.github.ai/inference","key_env":"GH_PAT","models":["gpt-4.1","gpt-4o-mini","*"],"free":True,"cooldown":30},
    {"name":"novita","base":"https://api.novita.ai/v3/openai","key_env":"NOVITA_KEY","models":["*"],"free":False,"cooldown":20},
    {"name":"mistral","base":"https://api.mistral.ai/v1","key_env":"MISTRAL_KEY","models":["*"],"free":True,"cooldown":30},
    {"name":"deepseek","base":"https://api.deepseek.com/v1","key_env":"DEEPSEEK_KEY","models":["deepseek-chat","deepseek-reasoner"],"free":False,"cooldown":15}
  ]
}

def load_config():
    cfg = DEFAULTS
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception as e:
            log(f"config parse error, using defaults: {e}")
    kv = {}
    auth = os.path.join(os.path.expanduser("~"), ".local", "share", "opencode", "auth.json")
    if os.path.exists(auth):
        try:
            with open(auth, encoding="utf-8") as f:
                a = json.load(f)
            if a.get("openrouter"): kv["OPENROUTER_KEY"] = a["openrouter"]["key"]
            if a.get("opencode-go"): kv["OPENCODE_GO_KEY"] = a["opencode-go"]["key"]
            if a.get("deepseek"): kv["DEEPSEEK_KEY"] = a["deepseek"]["key"]
            if a.get("openai"): kv["OPENAI_KEY"] = a["openai"]["key"]
            if a.get("nvidia"): kv["NVIDIA_KEY"] = a["nvidia"]["key"]
        except Exception as e:
            log(f"auth.json read error: {e}")
    for p in cfg.get("providers", []):
        env = p.get("key_env", "")
        if env and env in kv and not os.environ.get(env):
            os.environ[env] = kv[env]
    return cfg

CFG = load_config()
PROVIDERS = CFG.get("providers", DEFAULTS["providers"])

# ---------------------------------------------------------------- expand multi-key providers
EXPANDED = []
for p in PROVIDERS:
    keys = list(p.get("keys") or [])
    envk = os.environ.get(p.get("key_env",""), "")
    if envk:
        keys.insert(0, envk)
    if not keys:
        keys = [None]
    for i, k in enumerate(keys):
        e = dict(p)
        e["name"] = f'{p["name"]}[{i}]' if len(keys) > 1 else p["name"]
        e.pop("keys", None)
        e["api_key"] = k
        EXPANDED.append(e)
PROVIDERS = EXPANDED

# ---------------------------------------------------------------- state
STATE = {}
for p in PROVIDERS:
    STATE[p["name"]] = {
        "status":"untested","next":0.0,"fails":0,"ok":0,"fail":0,"last_err":"","cooldown":p.get("cooldown",30)
    }
LOCK = threading.Lock()
MENU_ITEMS = {}

# ---------------------------------------------------------------- metrics + virtual keys + request log
METRICS = {"requests_total": 0, "requests_failed": 0, "tokens_in": 0, "tokens_out": 0, "provider_counts": {}, "started_at": time.time()}
REQUEST_LOG = []  # last 100: {ts, model, provider, tokens_in, tokens_out, ms, status}
REQUEST_LOG_LOCK = threading.Lock()


def _log_request(model, provider, tokens_in, tokens_out, ms, status):
    with REQUEST_LOG_LOCK:
        REQUEST_LOG.append({"ts": time.time(), "model": model, "provider": provider, "tokens_in": tokens_in or 0, "tokens_out": tokens_out or 0, "ms": ms or 0, "status": status})
        if len(REQUEST_LOG) > 100:
            del REQUEST_LOG[0]


def _load_virtual_keys():
    # file: configs/virtual_keys.json  or env OMNI_VIRTUAL_KEYS (json)
    env = os.environ.get("OMNI_VIRTUAL_KEYS", "").strip()
    if env:
        try:
            d = json.loads(env)
            return d.get("keys", d) if isinstance(d, dict) else {}
        except Exception:
            pass
    for cand in (os.path.join(BASE_DIR, "..", "configs", "virtual_keys.json"), os.path.join(BASE_DIR, "virtual_keys.json")):
        cand = os.path.abspath(cand)
        if os.path.exists(cand):
            try:
                with open(cand, encoding="utf-8") as f:
                    d = json.load(f)
                return d.get("keys", d) if isinstance(d, dict) else {}
            except Exception:
                pass
    return {}


VIRTUAL_KEYS = _load_virtual_keys()

# per-key rate-limit state: key -> {window_start, count, daily_count, daily_reset}
VK_STATE = {}
VK_LOCK = threading.Lock()


def _check_virtual_key(headers):
    if not VIRTUAL_KEYS:
        return None, None  # open mode
    hl = {str(k).lower(): str(v) for k, v in (headers or {}).items()}
    auth = hl.get("authorization", "") or hl.get("x-api-key", "")
    # Bearer sk-...  or bare key
    tok = auth[7:].strip() if auth.lower().startswith("bearer ") else auth.strip()
    if not tok or tok not in VIRTUAL_KEYS:
        return False, tok
    # optional per-key RPM / daily limits
    cfg = VIRTUAL_KEYS[tok] if isinstance(VIRTUAL_KEYS[tok], dict) else {}
    rpm = int(cfg.get("rpm", 0) or 0)
    daily = int(cfg.get("daily_limit", 0) or 0)
    now = time.time()
    with VK_LOCK:
        st = VK_STATE.setdefault(tok, {"window_start": now, "count": 0, "daily_count": 0, "daily_reset": now})
        # daily reset (24h rolling)
        if now - st["daily_reset"] >= 86400:
            st["daily_count"] = 0
            st["daily_reset"] = now
        if daily and st["daily_count"] >= daily:
            return "daily", tok
        # rpm window (60s)
        if now - st["window_start"] >= 60:
            st["window_start"] = now
            st["count"] = 0
        if rpm and st["count"] >= rpm:
            return "rpm", tok
        st["count"] += 1
        st["daily_count"] += 1
    return True, tok


def _record_metrics(provider, usage):
    with LOCK:
        METRICS["requests_total"] += 1
        METRICS["provider_counts"][provider] = METRICS["provider_counts"].get(provider, 0) + 1
        if usage:
            METRICS["tokens_in"] += int(usage.get("prompt_tokens", 0) or 0)
            METRICS["tokens_out"] += int(usage.get("completion_tokens", 0) or 0)

def _is_retryable_status(code):
    return code in (429, 502, 503, 504, 529)


def mark(name, ok, err=""):
    with LOCK:
        s = STATE[name]
        if ok:
            s["status"] = "ok"; s["ok"] += 1; s["fails"] = 0
        else:
            s["fail"] += 1; s["fails"] += 1; s["last_err"] = str(err)[:200]
            cd = s["cooldown"] * min(16, max(1, 2**(s["fails"]-1)))
            s["next"] = time.time() + cd
            s["status"] = f"cooling({int(cd)}s)"
            log(f"  FAIL {name}: {err}")

def healthy(p):
    s = STATE[p["name"]]
    if s["status"] == "cooling" and time.time() < s["next"]:
        return False
    if p.get("enabled") is False:
        return False
    if not p.get("api_key"):
        return False
    return True

def matches(p, model):
    ms = p.get("models", ["*"])
    if "*" in ms: return True
    return model in ms

def routed_model(p, smart=True):
    if smart:
        rm = p.get("routed") or p.get("models", ["*"])
        for m in rm:
            if m != "*":
                return m
    return None


CAP_ROUTERS = {
    "router-code": "coding", "router-reason": "reasoning", "router-reasoning": "reasoning",
    "router-vision": "vision", "router-fast": "fast", "router-long": "long-context",
}


def smart_target_model(model):
    """For router-* capability aliases, return the best currently-healthy free model for that capability.
    Returns (model_id, provider_name) or None if none available."""
    cap = CAP_ROUTERS.get(model)
    if cap:
        best = CAPABILITIES.get(cap, [])
        for p in candidate_order_smart():
            if not healthy(p):
                continue
            rm = p.get("routed") or []
            for m in rm:
                if m in best:
                    return m, p["name"]
            # also check models list
            for m in p.get("models", []):
                if m != "*" and m in best:
                    return m, p["name"]
        return None
    return None


def candidate_order_smart():
    """Smart ordering: google-ai-studio ALWAYS first (primary), then free providers, then paid.
    Multi-key entries grouped so all keys of one provider come before next provider."""
    groups = {}
    order_names = []
    for p in PROVIDERS:
        grp = p["name"].rsplit("[", 1)[0]
        if grp not in groups:
            groups[grp] = []
            order_names.append(grp)
        groups[grp].append(p)

    def sort_key(grp):
        if grp == "google-ai-studio":
            return 0
        if any(x.get("free") for x in groups[grp]):
            return 1
        return 2
    ordered = sorted(order_names, key=sort_key)
    out = []
    for g in ordered:
        out.extend(groups[g])
    return out

def candidates(model, smart):
    order = []
    pool = candidate_order_smart() if smart else PROVIDERS
    cap_target = smart_target_model(model) if model in CAP_ROUTERS else None
    cap = CAP_ROUTERS.get(model)
    for p in pool:
        if not healthy(p):
            continue
        if cap:
            # any provider carrying a model with this capability is a candidate (ordered: free first, then paid)
            rm = (p.get("routed") or []) + [m for m in p.get("models", []) if m != "*"]
            capable = [m for m in rm if m in CAPABILITIES.get(cap, [])]
            if not capable:
                continue
            order.append((p, capable[0]))
        elif cap_target:
            tm, tprov = cap_target
            if p["name"].rsplit("[", 1)[0] != tprov:
                continue
            if not matches(p, tm) and not (p.get("routed") and tm in p["routed"]):
                continue
            order.append((p, tm))
        elif smart or matches(p, model):
            order.append((p, None))
    if not smart and not cap_target and not cap:
        order = [(p, None) for p, _ in order]
        explicit = [x for x in order if model in x[0].get("models", [])]
        star = [x for x in order if x not in explicit]
        order = explicit + star
    return order

# ---------------------------------------------------------------- upstream call
def call_upstream(p, path, headers, payload, timeout=90):
    base = p["base"]
    if "{acct}" in base:
        acct = os.environ.get("CF_ACCOUNT_ID","")
        base = base.replace("{acct}", acct)
    url = base.rstrip("/") + path
    key = p.get("api_key") or os.environ.get(p.get("key_env",""), "")
    hdrs = dict(headers)
    hdrs["Authorization"] = f"Bearer {key}"
    hdrs["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    hdrs["Accept"] = "application/json, text/event-stream"
    hdrs.pop("Host", None)
    hdrs.pop("Content-Length", None)
    try:
        from curl_cffi import requests as cr
        want_stream = bool(payload and payload.get("stream"))
        if payload is not None:
            resp = cr.post(url, json=payload, headers=hdrs,
                           impersonate="chrome124", timeout=timeout, stream=want_stream)
        else:
            resp = cr.get(url, headers=hdrs, impersonate="chrome124", timeout=timeout)
        ct = resp.headers.get("Content-Type","")
        if "text/event-stream" in ct:
            # stream: but if upstream already errored, read the error body
            if hasattr(resp, "status_code") and resp.status_code >= 400:
                try:
                    err = resp.text.encode() or b""
                except Exception:
                    err = b""
                return resp, ct, err
            return resp, ct, True
        return resp, ct, resp.content
    except ImportError:
        pass
    # stdlib fallback
    body = json.dumps(payload).encode() if payload is not None else None
    req = Request(url, data=body, headers=hdrs, method="POST" if payload is not None else "GET")
    resp = urlopen(req, timeout=timeout, context=CTX)
    ct = resp.headers.get("Content-Type","")
    if "text/event-stream" in ct:
        return resp, ct, True
    raw = resp.read()
    if resp.headers.get("Content-Encoding") == "gzip":
        raw = gzip.decompress(raw)
    return resp, ct, raw

def stream_body(resp):
    # curl_cffi response
    if hasattr(resp, "iter_content"):
        for chunk in resp.iter_content(chunk_size=4096):
            if not chunk:
                break
            yield chunk
        return
    # stdlib response
    while True:
        chunk = resp.read(4096)
        if not chunk:
            break
        yield chunk

# ---------------------------------------------------------------- router core
def route(path, headers, payload, model, smart=False):
    attempts = []
    # capability alias resolution: router-code/router-reason/router-vision/router-fast/router-long
    cap_target = smart_target_model(model) if model in CAP_ROUTERS else None
    for entry in candidates(model, smart):
        p, forced_model = entry
        attempts.append(p["name"])
        jp = dict(payload)
        if smart:
            em = routed_model(p)
            if forced_model:
                em = forced_model
            elif cap_target:
                tm, tprov = cap_target
                if p["name"].rsplit("[", 1)[0] == tprov:
                    em = tm
            jp["model"] = em if em else model
        t0 = time.time()
        resp = ct = body = None
        success = False
        for _retry in range(2):
            try:
                resp, ct, body = call_upstream(p, path, headers, jp)
            except (HTTPError, URLError, OSError) as e:
                if _retry == 0:
                    log(f"    retry {p['name']} (network) after 1s: {e}")
                    time.sleep(1)
                    continue
                mark(p["name"], False, e)
                if isinstance(e, HTTPError) and e.code == 401:
                    with LOCK:
                        STATE[p["name"]]["next"] = time.time() + 3600
                break
            # check HTTP status
            if hasattr(resp, "status_code") and resp.status_code >= 400:
                if _is_retryable_status(resp.status_code) and _retry == 0:
                    try:
                        ra = resp.headers.get("Retry-After") or resp.headers.get("retry-after") or "1"
                        wait = min(int(str(ra).split(",")[0].strip()), 5)
                    except Exception:
                        wait = 1
                    log(f"    retry {p['name']} after {wait}s (HTTP {resp.status_code})")
                    time.sleep(wait)
                    continue
                err_txt = body[:300] if not isinstance(body, bool) else b""
                log(f"    provider {p['name']} -> HTTP {resp.status_code}: {err_txt[:200]}")
                mark(p["name"], False, f"HTTP {resp.status_code} {err_txt[:150]}")
                if resp.status_code in (401, 403, 429):
                    with LOCK:
                        STATE[p["name"]]["next"] = time.time() + 3600
                elif resp.status_code in (502, 503, 504, 529):
                    with LOCK:
                        STATE[p["name"]]["next"] = time.time() + 30
                break
            success = True
            break
        if not success:
            time.sleep(0.25)
            continue
        # success
        mark(p["name"], True)
        # metrics: parse usage if non-stream
        usage = None
        if not isinstance(body, bool):
            try:
                _j = json.loads(body)
                usage = _j.get("usage")
            except Exception:
                pass
        _record_metrics(p["name"], usage)
        return {"provider":p["name"], "response":resp, "ct":ct, "body":body,
                "stream": isinstance(body, bool), "attempts":attempts, "ms":int((time.time()-t0)*1000)}
    return {"error":"ALL_PROVIDERS_FAILED","attempts":attempts}


def route_with_fallback(path, headers, payload, model, smart=False):
    """Try explicit route; if ALL matched providers fail (quota/limits), fall back to smart auto-chain."""
    result = route(path, headers, payload, model, smart=smart)
    if "error" in result and not smart:
        # explicit model failed everywhere -> retry as smart (any healthy free provider)
        log(f"  FALLBACK: explicit '{model}' failed ({result['attempts']}) -> smart auto-chain")
        fb = route(path, headers, payload, model, smart=True)
        if "error" not in fb:
            fb["fallback_from"] = model
            return fb
        result["attempts"] = result.get("attempts", []) + ["->smart:"] + fb.get("attempts", [])
    return result

# ---------------------------------------------------------------- handlers
def anthropic_to_openai(payload):
    """Translate Anthropic Messages API request -> OpenAI chat.completions."""
    o = dict(payload)
    msgs = []
    sys = payload.get("system")
    if sys:
        if isinstance(sys, str):
            sys_text = sys
        else:
            sys_text = "".join(b.get("text", "") for b in sys if isinstance(b, dict) and b.get("type") == "text")
        if sys_text:
            msgs.append({"role": "system", "content": sys_text})
    o.pop("system", None)
    for m in payload.get("messages", []):
        role = m.get("role")
        content = m.get("content")
        tool_calls, tool_results, text_parts, images = [], [], [], []
        if isinstance(content, str):
            text_parts.append(content)
        elif isinstance(content, list):
            for b in content:
                if not isinstance(b, dict):
                    continue
                bt = b.get("type")
                if bt == "text":
                    text_parts.append(b.get("text", ""))
                elif bt == "image":
                    src = b.get("source", {})
                    media = src.get("media_type", "image/png")
                    data = src.get("data", "")
                    images.append({"type": "image_url", "image_url": {"url": f"data:{media};base64,{data}"}})
                elif bt == "tool_use":
                    tool_calls.append({"id": b.get("id", ""), "type": "function",
                                       "function": {"name": b.get("name", ""),
                                                    "arguments": json.dumps(b.get("input", {}))}})
                elif bt == "tool_result":
                    trc = b.get("content", "")
                    if isinstance(trc, list):
                        trc = "".join(x.get("text", "") for x in trc if isinstance(x, dict) and x.get("type") == "text")
                    tool_results.append({"role": "tool", "tool_call_id": b.get("tool_use_id", ""), "content": str(trc)})
        if role == "assistant":
            if tool_calls:
                msgs.append({"role": "assistant", "content": "".join(text_parts) or None, "tool_calls": tool_calls})
            else:
                msgs.append({"role": "assistant", "content": "".join(text_parts)})
        elif role == "user":
            if images:
                if text_parts:
                    images.insert(0, {"type": "text", "text": "".join(text_parts)})
                msgs.append({"role": "user", "content": images})
            else:
                msgs.append({"role": "user", "content": "".join(text_parts)})
        else:
            msgs.append({"role": role, "content": "".join(text_parts)})
        msgs.extend(tool_results)
    o["messages"] = msgs
    if payload.get("tools"):
        o["tools"] = [{"type": "function", "function": {"name": t.get("name"),
                       "description": t.get("description", ""), "parameters": t.get("input_schema", {})}}
                      for t in payload["tools"] if isinstance(t, dict) and t.get("name")]
    if payload.get("tool_choice"):
        tc = payload["tool_choice"]
        if isinstance(tc, dict):
            o["tool_choice"] = "required" if tc.get("type") in ("any", "required") else "auto"
        else:
            o["tool_choice"] = tc
    o.pop("thinking", None)
    o.pop("metadata", None)
    return o


def openai_to_anthropic(obj, model):
    """Translate OpenAI chat.completions response -> Anthropic Messages response."""
    choice = obj.get("choices", [{}])[0]
    msg = choice.get("message", {})
    content = []
    text = msg.get("content")
    if text:
        content.append({"type": "text", "text": text})
    for tc in (msg.get("tool_calls") or []):
        try:
            inp = json.loads(tc["function"].get("arguments", "{}"))
        except Exception:
            inp = {}
        content.append({"type": "tool_use", "id": tc.get("id", ""),
                        "name": tc["function"].get("name", ""), "input": inp})
    fr = choice.get("finish_reason")
    if not content and msg.get("tool_calls"):
        sr = "tool_use"
    else:
        sr = {"stop": "end_turn", "length": "max_tokens", "tool_calls": "tool_use",
              "function_call": "tool_use"}.get(fr, "end_turn")
    usage = obj.get("usage", {})
    return {"id": obj.get("id", "msg_" + uuid.uuid4().hex[:12]), "type": "message",
            "role": "assistant", "model": obj.get("model", model), "content": content,
            "stop_reason": sr, "stop_sequence": None,
            "usage": {"input_tokens": usage.get("prompt_tokens", 0),
                      "output_tokens": usage.get("completion_tokens", 0)}}


def iter_anthropic_stream(stream_iter, model):
    """Translate OpenAI SSE chunk stream -> Anthropic SSE events (yields bytes)."""
    msg_id = "msg_" + uuid.uuid4().hex[:12]
    def ev(name, data):
        return (f"event: {name}\ndata: {json.dumps(data)}\n\n").encode()
    yield ev("message_start", {"type": "message_start", "message": {
        "id": msg_id, "type": "message", "role": "assistant", "model": model,
        "content": [], "stop_reason": None, "stop_sequence": None,
        "usage": {"input_tokens": 0, "output_tokens": 0}}})
    buf = b""
    text_open = False
    tools_state = {}   # oai index -> {anthropic_index, id, name}
    next_block = 0
    got_finish = False
    for chunk in stream_iter:
        if not chunk:
            continue
        buf += chunk
        while b"\n" in buf:
            line, _, buf = buf.partition(b"\n")
            line = line.strip()
            if not line.startswith(b"data:"):
                continue
            data = line[5:].strip()
            if data == b"[DONE]":
                continue
            try:
                obj = json.loads(data)
            except Exception:
                continue
            choices = obj.get("choices") or []
            if not choices:
                continue
            delta = choices[0].get("delta", {}) or {}
            idx = choices[0].get("index", 0)
            # text deltas
            txt = delta.get("content")
            if txt:
                if not text_open:
                    yield ev("content_block_start", {"type": "content_block_start",
                            "index": next_block, "content_block": {"type": "text", "text": ""}})
                    text_open = True
                    next_block += 1
                yield ev("content_block_delta", {"type": "content_block_delta",
                        "index": next_block - 1, "delta": {"type": "text_delta", "text": txt}})
            # tool call deltas
            for tc in (delta.get("tool_calls") or []):
                tcidx = tc.get("index", 0)
                fn = tc.get("function", {}) or {}
                if tcidx not in tools_state:
                    tools_state[tcidx] = {"ant_idx": next_block, "id": tc.get("id", ""), "name": fn.get("name", "")}
                    yield ev("content_block_start", {"type": "content_block_start",
                            "index": next_block, "content_block": {"type": "tool_use",
                            "id": tc.get("id", ""), "name": fn.get("name", ""), "input": {}}})
                    next_block += 1
                if fn.get("arguments"):
                    yield ev("content_block_delta", {"type": "content_block_delta",
                            "index": tools_state[tcidx]["ant_idx"],
                            "delta": {"type": "input_json_delta", "partial_json": fn["arguments"]}})
            if choices[0].get("finish_reason"):
                got_finish = True
    # close open blocks
    if text_open:
        yield ev("content_block_stop", {"type": "content_block_stop", "index": next_block - 1})
    for s in tools_state.values():
        yield ev("content_block_stop", {"type": "content_block_stop", "index": s["ant_idx"]})
    yield ev("message_delta", {"type": "message_delta", "delta": {"stop_reason": "end_turn" if not got_finish else "tool_use" if tools_state else "end_turn"},
                               "usage": {"output_tokens": 0}})
    yield ev("message_stop", {"type": "message_stop"})


def route_anthropic(handler, payload, is_stream):
    model = payload.get("model", "router-auto")
    smart = model in ("router-smart", "router-auto") or model.startswith("router-")
    oai = anthropic_to_openai(payload)
    oai.pop("max_tokens", None)
    oai["max_tokens"] = min(payload.get("max_tokens", 4096), 4096)
    if is_stream:
        oai["stream"] = True
    log(f"  ANTHROPIC->OAI model={model} payload={json.dumps(oai)[:600]}")
    result = route_with_fallback("/chat/completions", {}, oai, model, smart=smart)
    if "error" in result:
        log(f"  ANTHROPIC-ROUTE FAILED model={model} smart={smart}")
        log(f"    translated payload: {json.dumps(oai)[:800]}")
        body = json.dumps({"type": "error", "error": {"type": "router_error",
                "message": f"all providers failed: {result['attempts']}"}}).encode()
        handler.send_response(503)
        handler.send_header("Content-Type", "application/json")
        handler.send_header("X-Router-Provider", "none")
        handler.send_header("X-Router-Attempts", ",".join(result["attempts"]))
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)
        _log_request(model, "none", 0, 0, 0, "failed")
        with LOCK:
            METRICS["requests_failed"] += 1
        return True
    r = result["response"]
    status = int(getattr(r, "status_code") or getattr(r, "status") or 200)
    # request log for anthropic
    try:
        _ub = result.get("body", b"")
        _u = json.loads(_ub).get("usage", {}) if not isinstance(_ub, bool) and _ub else {}
        _log_request(model, result["provider"], _u.get("prompt_tokens", 0), _u.get("completion_tokens", 0), result.get("ms", 0), "ok")
    except Exception:
        _log_request(model, result["provider"], 0, 0, result.get("ms", 0), "ok")
    handler.send_response(status)
    handler.send_header("X-Router-Provider", result["provider"])
    handler.send_header("X-Router-Attempts", ",".join(result["attempts"]))
    handler.send_header("X-Router-Latency-ms", str(result["ms"]))
    if is_stream:
        handler.send_header("Content-Type", "text/event-stream")
        handler.send_header("Transfer-Encoding", "chunked")
        handler.end_headers()
        try:
            for evbytes in iter_anthropic_stream(stream_body(r), result.get("model", model)):
                try:
                    handler.wfile.write(b"%x\r\n" % len(evbytes) + evbytes + b"\r\n")
                    handler.wfile.flush()
                except Exception:
                    break
            handler.wfile.write(b"0\r\n\r\n")
            handler.wfile.flush()
        except Exception:
            pass
    else:
        body = result["body"] if not isinstance(result["body"], bool) else b""
        try:
            obj = json.loads(body)
            out = json.dumps(openai_to_anthropic(obj, result.get("model", model))).encode()
        except Exception:
            out = body
        handler.send_header("Content-Type", "application/json")
        handler.send_header("Content-Length", str(len(out)))
        handler.end_headers()
        handler.wfile.write(out)
    return True


MODEL_META = {
    "router-auto": ("Router Auto - smart free-first failover", "primary"),
    "router-smart": ("Router Smart - alias of router-auto", "primary"),
    "gemini-flash-latest": ("Gemini Flash Latest - Google (3-account rotation)", "google"),
    "gemini-3.7-flash": ("Gemini 3.7 Flash - Google", "google"),
    "gemini-2.5-flash": ("Gemini 2.5 Flash - Google", "google"),
    "dots-studio/dots-3-note-preview:free": ("Dots 3 Note 280B MoE 512K ctx - OpenRouter free (top coder)", "openrouter"),
    "nvidia/nemotron-3-ultra-550b-a55b:free": ("Nemotron 3 Ultra 550B 1M ctx - OpenRouter free", "openrouter"),
    "nvidia/nemotron-3-super-120b-a12b:free": ("Nemotron 3 Super 120B - OpenRouter free", "openrouter"),
    "nvidia/nemotron-3.5-lightning:free": ("Nemotron 3.5 Lightning 1M ctx - OpenRouter free (fastest)", "openrouter"),
    "poolside/laguna-s-2.1:free": ("Laguna S 2.1 262K - OpenRouter free (coder)", "openrouter"),
    "poolside/laguna-xs-2.1:free": ("Laguna XS 2.1 262K - OpenRouter free", "openrouter"),
    "z-ai/glm-5.2:free": ("GLM 5.2 256K - OpenRouter free (reasoning)", "openrouter"),
    "cohere/north-mini-code:free": ("North Mini Code 256K - OpenRouter free (code)", "openrouter"),
    "google/gemma-4-31b-it:free": ("Gemma 4 31B 262K - OpenRouter free", "openrouter"),
    "google/gemma-4-26b-a4b-it:free": ("Gemma 4 26B 262K - OpenRouter free", "openrouter"),
    "openai/gpt-oss-20b:free": ("GPT-OSS 20B 131K - OpenRouter free", "openrouter"),
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free": ("Nemotron Nano Omni 30B - OpenRouter free", "openrouter"),
    "nvidia/nemotron-3-nano-30b-a3b:free": ("Nemotron Nano 30B - OpenRouter free", "openrouter"),
    "nvidia/nemotron-nano-12b-v2-vl:free": ("Nemotron Nano 12B VL - OpenRouter free (vision)", "openrouter"),
    "nvidia/nemotron-nano-9b-v2:free": ("Nemotron Nano 9B - OpenRouter free", "openrouter"),
    "liquid/lfm-2.5-2.6b:free": ("LFM 2.5 2.6B 128K - OpenRouter free", "openrouter"),
    "openrouter/free": ("OpenRouter Auto-Free - smartest free model per prompt", "openrouter"),
    "deepseek-ai/deepseek-v4-flash-0731": ("DeepSeek V4 Flash - NVIDIA NIM", "nvidia-nim"),
    "deepseek-ai/deepseek-coder-6.7b-instruct": ("DeepSeek Coder 6.7B - NVIDIA NIM", "nvidia-nim"),
    "moonshotai/kimi-k3": ("Kimi K3 (3T frontier) - NVIDIA NIM", "nvidia-nim"),
    "moonshotai/kimi-k2.6": ("Kimi K2.6 - NVIDIA NIM", "nvidia-nim"),
    "deepseek-v4-flash": ("DeepSeek V4 Flash - OpenCode Go sub", "opencode-go"),
    "deepseek-v4-pro": ("DeepSeek V4 Pro - OpenCode Go sub", "opencode-go"),
    "kimi-k2.7-code": ("Kimi K2.7 Code - OpenCode Go sub", "opencode-go"),
    "qwen3.7-plus": ("Qwen 3.7 Plus - OpenCode Go sub", "opencode-go"),
    "deepseek-chat": ("DeepSeek Chat - direct paid API", "deepseek"),
    "deepseek-reasoner": ("DeepSeek Reasoner - direct paid API", "deepseek"),
    "gpt-oss-120b": ("GPT-OSS 120B - Groq free", "groq"),
    "llama-3.3-70b-versatile": ("Llama 3.3 70B Versatile - Groq free", "groq"),
    "llama-3.1-8b-instant": ("Llama 3.1 8B Instant - Groq free", "groq"),
    "llama-3.3-70b": ("Llama 3.3 70B - Cerebras", "cerebras"),
    "gpt-4.1": ("GPT 4.1 - GitHub Models", "github"),
    "gpt-4o-mini": ("GPT-4o Mini - GitHub Models", "github"),
}

# capability-tagged routing: models mapped to what they're BEST at
CAPABILITIES = {
    "coding": ["dots-studio/dots-3-note-preview:free", "cohere/north-mini-code:free",
               "poolside/laguna-s-2.1:free", "poolside/laguna-xs-2.1:free",
               "nvidia/nemotron-3-ultra-550b-a55b:free", "nvidia/nemotron-3-super-120b-a12b:free",
               "kimi-k2.7-code", "deepseek-v4-flash", "deepseek-ai/deepseek-coder-6.7b-instruct",
               "gpt-4.1", "gpt-oss-120b", "qwen3.7-plus", "gpt-4o-mini"],
    "reasoning": ["z-ai/glm-5.2:free", "gemini-flash-latest", "gemini-3.7-flash",
                  "deepseek-reasoner", "deepseek-v4-pro", "deepseek-ai/deepseek-v4-flash-0731"],
    "vision": ["nvidia/nemotron-nano-12b-v2-vl:free", "gemini-flash-latest", "gemini-3.7-flash",
                "qwen3.7-plus", "dots-studio/dots-3-note-preview:free"],
    "fast": ["nvidia/nemotron-3.5-lightning:free", "nvidia/nemotron-nano-9b-v2:free",
             "liquid/lfm-2.5-2.6b:free", "gemini-2.5-flash", "llama-3.1-8b-instant"],
    "long-context": ["nvidia/nemotron-3-ultra-550b-a55b:free", "nvidia/nemotron-3.5-lightning:free",
                     "dots-studio/dots-3-note-preview:free", "gemini-flash-latest", "deepseek-v4-flash"],
}


def model_list():
    ids = set()
    for p in PROVIDERS:
        for m in p.get("models", []):
            if m != "*":
                ids.add(m)
    ids.update(MODEL_META.keys())
    ids.update(CAP_ROUTERS.keys())
    ids.update(["openrouter/free"])
    data = [{"id": i, "object": "model", "owned_by": "omni-router"} for i in sorted(ids)]
    return {"object": "list", "data": data}


def model_list_anthropic():
    """Anthropic-format /v1/models - what Claude Code's gateway discovery reads."""
    ids = set()
    for p in PROVIDERS:
        for m in p.get("models", []):
            if m != "*":
                ids.add(m)
    ids.update(MODEL_META.keys())
    ids.update(CAP_ROUTERS.keys())
    ids.update(["openrouter/free"])
    created = 1787200000
    data = []
    for i in sorted(ids):
        disp, owner = MODEL_META.get(i, (i, "omni-router"))
        if i in CAP_ROUTERS:
            disp = f"Router {i.split('-',1)[1].title()} - auto-picks best free model for capability"
        data.append({"id": i, "type": "model", "display_name": disp,
                     "created_at": created})
        created += 1
    return {"data": data, "has_more": False, "first_id": data[0]["id"] if data else None,
            "last_id": data[-1]["id"] if data else None}

def _metrics_text():
    up = int(time.time() - METRICS["started_at"])
    lines = [
        "# HELP omni_router_requests_total Total proxied requests",
        "# TYPE omni_router_requests_total counter",
        f"omni_router_requests_total {METRICS['requests_total']}",
        "# HELP omni_router_requests_failed Total failed requests",
        "# TYPE omni_router_requests_failed counter",
        f"omni_router_requests_failed {METRICS['requests_failed']}",
        "# HELP omni_router_tokens_input Total prompt tokens proxied",
        "# TYPE omni_router_tokens_input counter",
        f"omni_router_tokens_input {METRICS['tokens_in']}",
        "# HELP omni_router_tokens_output Total completion tokens proxied",
        "# TYPE omni_router_tokens_output counter",
        f"omni_router_tokens_output {METRICS['tokens_out']}",
        "# HELP omni_router_uptime_seconds Uptime in seconds",
        "# TYPE omni_router_uptime_seconds gauge",
        f"omni_router_uptime_seconds {up}",
    ]
    for prov, cnt in METRICS["provider_counts"].items():
        safe = prov.replace("-", "_").replace(".", "_").replace("[", "_").replace("]", "")
        lines.append(f'omni_router_provider_requests{{provider="{prov}"}} {cnt}')
    return "\n".join(lines) + "\n"


def handle(handler, path, headers, payload):
    # virtual-key gate (if configured)
    if VIRTUAL_KEYS and path not in ("/health", "/v1/health", "/metrics", "/v1/metrics"):
        ok, tok = _check_virtual_key(headers)
        if ok is False:
            body = json.dumps({"error": {"message": "invalid virtual key", "type": "authentication_error"}}).encode()
            handler.send_response(401)
            handler.send_header("Content-Type", "application/json")
            handler.send_header("Content-Length", str(len(body)))
            handler.end_headers()
            handler.wfile.write(body)
            with LOCK:
                METRICS["requests_failed"] += 1
            return True
        if ok in ("rpm", "daily"):
            body = json.dumps({"error": {"message": f"virtual key rate limited ({ok})", "type": "rate_limit_error"}}).encode()
            handler.send_response(429)
            handler.send_header("Content-Type", "application/json")
            handler.send_header("Content-Length", str(len(body)))
            handler.end_headers()
            handler.wfile.write(body)
            with LOCK:
                METRICS["requests_failed"] += 1
            return True
    if path == "/v1/models" or path == "/models":
        hl = {str(k).lower(): str(v) for k, v in (headers or {}).items()}
        ua = hl.get("user-agent", "")
        if "anthropic-version" in hl or "anthropic" in ua.lower() or "claude" in ua.lower():
            return json.dumps(model_list_anthropic()).encode()
        return json.dumps(model_list()).encode()
    if "messages" in path or "complete" in path or path.rstrip("/").endswith("/v1/messages"):
        if not payload:
            body = json.dumps({"type":"error","error":{"type":"invalid_request","message":"missing body"}}).encode()
            handler.send_response(400); handler.send_header("Content-Type","application/json")
            handler.send_header("Content-Length", str(len(body))); handler.end_headers()
            handler.wfile.write(body); return True
        is_stream = bool(payload.get("stream"))
        return route_anthropic(handler, payload, is_stream)
    if not payload or payload.get("messages") is None and payload.get("prompt") is None:
        return json.dumps({"error":{"message":"missing messages","type":"invalid_request"}}).encode()
    model = payload.get("model","router-auto")
    smart = model in ("router-smart", "router-auto") or model in CAP_ROUTERS or model.startswith("router-")
    jp = dict(payload)
    if smart:
        jp.pop("model", None)
        requested = "router(auto)"
    else:
        requested = model
    jp.pop("max_tokens", None)
    jp["max_tokens"] = min(payload.get("max_tokens", 4096), 4096)
    result = route_with_fallback("/chat/completions", headers, jp, model, smart=smart)
    if "error" in result:
        body = json.dumps({"error":{"message":f"all providers failed: {result['attempts']}","type":"router_error"}}).encode()
        handler.send_response(503)
        handler.send_header("Content-Type","application/json")
        handler.send_header("X-Router-Provider","none")
        handler.send_header("X-Router-Attempts", ",".join(result["attempts"]))
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)
        _log_request(model, "none", 0, 0, 0, "failed")
        with LOCK:
            METRICS["requests_failed"] += 1
        return True
    r = result["response"]
    status = int(getattr(r, "status_code") or getattr(r, "status") or 200)
    # log success
    try:
        _ub = result.get("body", b"")
        _u = json.loads(_ub).get("usage", {}) if not isinstance(_ub, bool) and _ub else {}
        _log_request(model, result["provider"], _u.get("prompt_tokens", 0), _u.get("completion_tokens", 0), result.get("ms", 0), "ok")
    except Exception:
        _log_request(model, result["provider"], 0, 0, result.get("ms", 0), "ok")
    handler.send_response(status)
    ct = r.headers.get("Content-Type") if r.headers else ""
    if ct:
        handler.send_header("Content-Type", ct)
    handler.send_header("X-Router-Provider", result["provider"])
    handler.send_header("X-Router-Attempts", ",".join(result["attempts"]))
    handler.send_header("X-Router-Latency-ms", str(result["ms"]))
    if result["stream"]:
        handler.send_header("Transfer-Encoding","chunked")
        handler.end_headers()
        try:
            for chunk in stream_body(r):
                if not chunk:
                    continue
                try:
                    handler.wfile.write(b"%x\r\n" % len(chunk) + chunk + b"\r\n")
                    handler.wfile.flush()
                except Exception:
                    break
            handler.wfile.write(b"0\r\n\r\n")
            handler.wfile.flush()
        except Exception:
            pass
    else:
        b = result["body"] if not isinstance(result["body"], bool) else b""
        handler.send_header("Content-Length", str(len(b)))
        handler.end_headers()
        handler.wfile.write(b)
    return True

class RouterHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = f"OmniRouter/{VERSION}"
    def log_message(self, *a): pass
    def _read_body(self):
        ln = int(self.headers.get("Content-Length", 0) or 0)
        return self.rfile.read(ln) if ln else None
    def do_GET(self):
        if self.path in ("/metrics", "/v1/metrics"):
            body = _metrics_text().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path in ("/health","/v1/health"):
            body = json.dumps({"status":"ok","version":VERSION,"providers":{k:{"s":STATE[k]["status"],"err":STATE[k]["last_err"],"ok":STATE[k]["ok"],"fail":STATE[k]["fail"]} for k in STATE}}).encode()
            self.send_response(200); self.send_header("Content-Type","application/json")
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return
        if self.path == "/v1/models" or self.path == "/models":
            hl = {str(k).lower(): str(v) for k, v in dict(self.headers).items()}
            ua = hl.get("user-agent", "")
            out = model_list_anthropic() if ("anthropic-version" in hl or "anthropic" in ua.lower() or "claude" in ua.lower()) else model_list()
            body = json.dumps(out).encode()
            self.send_response(200); self.send_header("Content-Type","application/json")
            self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return
        if self.path in ("/ui", "/dashboard", "/ui/", "/dashboard/"):
            dash = os.path.join(BASE_DIR, "dashboard.html")
            # also try parent dir for pip-installed layout
            if not os.path.exists(dash):
                dash = os.path.join(os.path.dirname(BASE_DIR), "omni_router", "dashboard.html")
            if os.path.exists(dash):
                body = open(dash, "rb").read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            body = b"<h1>OmniRouter</h1><p>Dashboard not found. <a href='/health'>/health</a> <a href='/metrics'>/metrics</a></p>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path in ("/v1/logs", "/logs"):
            with REQUEST_LOG_LOCK:
                logs = list(REQUEST_LOG)
            body = json.dumps({"logs": logs, "count": len(logs)}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        log(f"  404 GET {self.path}")
        self.send_response(404); self.send_header("Content-Length","0"); self.end_headers()
    def do_POST(self):
        raw = self._read_body()
        payload = None
        if raw:
            try: payload = json.loads(raw.decode("utf-8"))
            except Exception:
                body = json.dumps({"error":{"message":"bad json"}}).encode()
                self.send_response(400); self.send_header("Content-Type","application/json")
                self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return
        log(f"  REQ {self.path} UA={self.headers.get('User-Agent','')[:60]}")
        try:
            done = handle(self, self.path, dict(self.headers), payload)
        except BrokenPipeError:
            return
        except Exception as e:
            log(f"  HANDLER ERROR: {type(e).__name__}: {e}")
            body = json.dumps({"error":{"message":str(e),"type":"router_internal"}}).encode()
            try:
                self.send_response(500); self.send_header("Content-Type","application/json")
                self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
            except Exception:
                pass

def main():
    log(f"OMNI-ROUTER {VERSION} starting on http://{HOST}:{PORT}  (config: {CONFIG_PATH})")
    for p in PROVIDERS:
        key = (p.get("api_key") or os.environ.get(p.get("key_env",""), ""))[:8] + "..." if (p.get("api_key") or os.environ.get(p.get("key_env",""), "")) else ""
        log(f"  provider: {p['name']:<24} key={'SET('+key+')' if key else 'MISSING':<20} models={p.get('models')}")
    try:
        srv = ThreadingHTTPServer((HOST, PORT), RouterHandler)
        log("READY. Point opencode/curl at http://127.0.0.1:8787/v1")
        srv.serve_forever()
    except KeyboardInterrupt:
        log("shutdown")
    except OSError as e:
        log(f"FATAL cannot bind {HOST}:{PORT}: {e}")

if __name__ == "__main__":
    main()