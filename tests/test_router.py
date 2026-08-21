"""
OmniRouter — comprehensive test suite
- Unit tests: always run, no network, no router needed
- Integration tests: auto-skip if router not running on :8787
- Covers: translation, routing, providers, metrics, harnesses
"""
import json
import urllib.request
import urllib.error
import pytest
import omni_router.omni_router as r

def _router_live(timeout=3):
    try:
        with urllib.request.urlopen("http://127.0.0.1:8787/health", timeout=timeout) as resp:
            return json.load(resp).get("status") == "ok"
    except Exception:
        return False

def _require_router():
    if not _router_live():
        pytest.skip("router not running on :8787")

def _has_live_provider():
    return any(p.get("api_key") for p in r.PROVIDERS)

def _health():
    with urllib.request.urlopen("http://127.0.0.1:8787/health", timeout=5) as resp:
        return json.load(resp)

def _models(headers=None):
    req = urllib.request.Request("http://127.0.0.1:8787/v1/models", headers=headers or {})
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.load(resp)

# =============================================================
#  UNIT
# =============================================================
def test_syntax_and_version():
    assert r.VERSION

def test_model_meta_has_router_aliases():
    assert "router-auto" in r.MODEL_META
    assert r.CAP_ROUTERS["router-code"] == "coding"

def test_capabilities_not_empty():
    for cap in ("coding", "reasoning", "vision", "fast", "long-context"):
        assert r.CAPABILITIES[cap]

def test_model_list_openai_shape():
    ml = r.model_list()
    assert ml["object"] == "list"
    assert len(ml["data"]) >= 20
    ids = {m["id"] for m in ml["data"]}
    assert "router-auto" in ids
    assert "gemini-flash-latest" in ids

def test_model_list_anthropic_shape():
    ml = r.model_list_anthropic()
    assert "data" in ml and "has_more" in ml
    assert len(ml["data"]) >= 20
    assert any(m["type"] == "model" for m in ml["data"])

def test_anthropic_to_openai_system_and_messages():
    payload = {"model": "router-auto", "max_tokens": 100, "system": "You are terse.", "messages": [{"role": "user", "content": "hello"}]}
    oai = r.anthropic_to_openai(payload)
    assert any(m["role"] == "system" for m in oai["messages"])
    assert oai["messages"][-1]["content"] == "hello"
    assert "system" not in oai

def test_anthropic_to_openai_system_as_blocks():
    payload = {"model": "router-auto", "max_tokens": 100, "system": [{"type": "text", "text": "You are helpful."}, {"type": "text", "text": " Be brief."}], "messages": [{"role": "user", "content": "hi"}]}
    oai = r.anthropic_to_openai(payload)
    sys_msgs = [m for m in oai["messages"] if m["role"] == "system"]
    assert len(sys_msgs) == 1
    assert "You are helpful." in sys_msgs[0]["content"]

def test_anthropic_to_openai_tool_use_becomes_tool_calls():
    payload = {"model": "router-auto", "max_tokens": 100, "messages": [{"role": "assistant", "content": [{"type": "tool_use", "id": "to_1", "name": "Bash", "input": {"cmd": "ls"}}]}]}
    oai = r.anthropic_to_openai(payload)
    assert oai["messages"][0].get("tool_calls")
    assert oai["messages"][0]["tool_calls"][0]["function"]["name"] == "Bash"

def test_anthropic_to_openai_tool_result_becomes_tool_role():
    payload = {"model": "router-auto", "max_tokens": 100, "messages": [{"role": "user", "content": [{"type": "tool_result", "tool_use_id": "to_1", "content": "file.txt"}]}]}
    oai = r.anthropic_to_openai(payload)
    assert any(m["role"] == "tool" and m["tool_call_id"] == "to_1" for m in oai["messages"])

def test_anthropic_to_openai_tools_mapping():
    payload = {"model": "router-auto", "max_tokens": 100, "messages": [{"role": "user", "content": "hi"}], "tools": [{"name": "get_weather", "description": "x", "input_schema": {"type": "object", "properties": {"city": {"type": "string"}}}}]}
    oai = r.anthropic_to_openai(payload)
    assert oai["tools"][0]["type"] == "function"
    assert oai["tools"][0]["function"]["name"] == "get_weather"

def test_anthropic_to_openai_image_block():
    payload = {"model": "router-auto", "max_tokens": 100, "messages": [{"role": "user", "content": [{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "abc123"}}]}]}
    oai = r.anthropic_to_openai(payload)
    assert oai["messages"][0]["content"][0]["type"] == "image_url"

def test_anthropic_to_openai_strips_thinking_and_metadata():
    payload = {"model": "router-auto", "max_tokens": 100, "thinking": {"type": "enabled"}, "metadata": {"user_id": "123"}, "messages": [{"role": "user", "content": "hi"}]}
    oai = r.anthropic_to_openai(payload)
    assert "thinking" not in oai
    assert "metadata" not in oai

def test_openai_to_anthropic_text_and_tool_use():
    obj = {"id": "chatcmpl-1", "model": "router-auto", "choices": [{"message": {"role": "assistant", "content": "hi", "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "Bash", "arguments": '{"cmd":"ls"}'}}]}, "finish_reason": "tool_calls"}], "usage": {"prompt_tokens": 10, "completion_tokens": 5}}
    out = r.openai_to_anthropic(obj, "router-auto")
    assert out["type"] == "message"
    assert any(b["type"] == "tool_use" for b in out["content"])
    assert out["usage"]["input_tokens"] == 10

def test_openai_to_anthropic_text_only():
    obj = {"id": "chatcmpl-2", "model": "gemini-flash-latest", "choices": [{"message": {"role": "assistant", "content": "hello"}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 5, "completion_tokens": 2}}
    out = r.openai_to_anthropic(obj, "gemini-flash-latest")
    assert out["content"][0]["type"] == "text"
    assert out["stop_reason"] == "end_turn"

def test_openai_to_anthropic_max_tokens_stop():
    obj = {"id": "x", "model": "m", "choices": [{"message": {"role": "assistant", "content": "hi"}, "finish_reason": "length"}], "usage": {}}
    out = r.openai_to_anthropic(obj, "m")
    assert out["stop_reason"] == "max_tokens"

def test_candidates_smart_is_free_first():
    ordered = r.candidate_order_smart()
    assert ordered[0]["name"].split("[")[0] == "google-ai-studio"

def test_smart_target_model_coding():
    tgt = r.smart_target_model("router-code")
    assert tgt is not None
    assert tgt[0] in r.CAPABILITIES["coding"]

def test_smart_target_model_reasoning():
    tgt = r.smart_target_model("router-reason")
    assert tgt is not None
    assert tgt[0] in r.CAPABILITIES["reasoning"]

def test_provider_config_has_required_fields():
    for p in r.PROVIDERS:
        assert "name" in p and "base" in p
        assert "models" in p or "routed" in p

def test_route_with_fallback_exists():
    assert callable(r.route_with_fallback)

def test_metrics_text_format():
    txt = r._metrics_text()
    assert "omni_router_requests_total" in txt
    assert "omni_router_uptime_seconds" in txt

def test_virtual_keys_open_mode_when_empty():
    if not r.VIRTUAL_KEYS:
        ok, _ = r._check_virtual_key({"Authorization": "Bearer anything"})
        assert ok is None

# =============================================================
#  INTEGRATION
# =============================================================
def test_health_endpoint_live():
    _require_router()
    h = _health()
    assert h["status"] == "ok"
    assert "providers" in h

def test_models_endpoint_openai_live():
    _require_router()
    ml = _models()
    assert ml["object"] == "list"
    assert len(ml["data"]) >= 20

def test_models_endpoint_anthropic_live():
    _require_router()
    ml = _models(headers={"anthropic-version": "2023-06-01"})
    assert "data" in ml
    assert any("display_name" in m for m in ml["data"])

def test_models_claude_ua_returns_anthropic():
    _require_router()
    ml = _models(headers={"User-Agent": "claude-cli/2.1.237 (Claude Code)"})
    assert "data" in ml

def test_metrics_endpoint_live():
    _require_router()
    with urllib.request.urlopen("http://127.0.0.1:8787/metrics", timeout=5) as resp:
        body = resp.read().decode()
    assert "omni_router_requests_total" in body
    assert "omni_router_tokens_input" in body

def test_health_has_per_key_entries():
    _require_router()
    h = _health()
    assert any(k.startswith("google-ai-studio") for k in h["providers"])

def test_health_has_all_providers():
    _require_router()
    h = _health()
    for must in ("openrouter-free", "google-ai-studio", "opencode-go"):
        assert any(must in k for k in h["providers"])

# =============================================================
#  HARNESS — every agentic tool (skip in CI without keys, lenient on 502/503)
# =============================================================
def test_harness_openai_chat_completions():
    _require_router()
    if not _has_live_provider():
        pytest.skip("no provider keys (CI without secrets)")
    payload = json.dumps({"model": "router-auto", "messages": [{"role": "user", "content": "Reply exactly: HARNESS-OK"}], "max_tokens": 10}).encode()
    req = urllib.request.Request("http://127.0.0.1:8787/v1/chat/completions", data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.load(resp)
        assert resp.status == 200
        assert "choices" in body
    except urllib.error.HTTPError as e:
        assert e.code in (429, 502, 503)
        body = json.load(e)
        assert "error" in body

def test_harness_anthropic_messages():
    _require_router()
    if not _has_live_provider():
        pytest.skip("no provider keys (CI without secrets)")
    payload = json.dumps({"model": "router-auto", "max_tokens": 20, "messages": [{"role": "user", "content": "Reply exactly: HARNESS-OK"}]}).encode()
    req = urllib.request.Request("http://127.0.0.1:8787/v1/messages", data=payload, headers={"Content-Type": "application/json", "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.load(resp)
        assert body["type"] == "message"
    except urllib.error.HTTPError as e:
        assert e.code in (429, 502, 503)
        body = json.load(e)
        assert "error" in body

def test_harness_anthropic_with_system():
    _require_router()
    if not _has_live_provider():
        pytest.skip("no provider keys (CI without secrets)")
    payload = json.dumps({"model": "router-auto", "max_tokens": 20, "system": "You are terse.", "messages": [{"role": "user", "content": "Say hi"}]}).encode()
    req = urllib.request.Request("http://127.0.0.1:8787/v1/messages", data=payload, headers={"Content-Type": "application/json", "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.load(resp)
        assert body["type"] == "message"
    except urllib.error.HTTPError as e:
        assert e.code in (429, 502, 503)

def test_harness_anthropic_with_tools():
    _require_router()
    if not _has_live_provider():
        pytest.skip("no provider keys (CI without secrets)")
    payload = json.dumps({"model": "router-auto", "max_tokens": 50, "tools": [{"name": "get_weather", "description": "x", "input_schema": {"type": "object", "properties": {"city": {"type": "string"}}}}], "messages": [{"role": "user", "content": "Use get_weather for Lahore"}]}).encode()
    req = urllib.request.Request("http://127.0.0.1:8787/v1/messages", data=payload, headers={"Content-Type": "application/json", "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.load(resp)
        assert body["type"] == "message"
        assert isinstance(body["content"], list)
    except urllib.error.HTTPError as e:
        assert e.code in (429, 502, 503)
