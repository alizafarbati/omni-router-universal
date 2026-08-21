#!/usr/bin/env bash
# OmniRouter — curl examples
set -euo pipefail
BASE="http://127.0.0.1:8787"

echo "== health =="
curl -s "$BASE/health" | python -m json.tool

echo -e "\n== models (OpenAI) =="
curl -s "$BASE/v1/models" | python -c "import sys,json; print(f\"{len(json.load(sys.stdin)['data'])} models\")"

echo -e "\n== models (Anthropic) =="
curl -s "$BASE/v1/models" -H "anthropic-version: 2023-06-01" | python -c "import sys,json; print(f\"{len(json.load(sys.stdin)['data'])} models\")"

echo -e "\n== chat (OpenAI) — router-auto =="
curl -s "$BASE/v1/chat/completions" -H "Content-Type: application/json" \
  -d '{"model":"router-auto","messages":[{"role":"user","content":"Say hi in 3 words"}]}' | python -m json.tool

echo -e "\n== chat — router-code (capability) =="
curl -s "$BASE/v1/chat/completions" -H "Content-Type: application/json" \
  -d '{"model":"router-code","messages":[{"role":"user","content":"Write a python function to reverse a string"}]}' | python -m json.tool

echo -e "\n== Anthropic messages =="
curl -s "$BASE/v1/messages" -H "Content-Type: application/json" -H "anthropic-version: 2023-06-01" \
  -d '{"model":"router-auto","max_tokens":50,"messages":[{"role":"user","content":"Say hi"}]}' | python -m json.tool

echo -e "\n== metrics =="
curl -s "$BASE/metrics" | head -20

echo -e "\n== UI ==\nOpen $BASE/ui in your browser"
