#!/usr/bin/env bash
# OmniRouter — Claude Code examples
set -euo pipefail

export ANTHROPIC_BASE_URL="http://127.0.0.1:8787"
export ANTHROPIC_API_KEY="omni-router-local"

echo "== Claude Code via OmniRouter (router-auto) =="
echo 'test' | claude -p "Say hi in 3 words." --max-turns 1

echo ""
echo "== With explicit model =="
echo 'test' | claude -p "Write a python hello world." --model "router-code" --max-turns 1

echo ""
echo "== List models (gateway discovery) =="
curl -s http://127.0.0.1:8787/v1/models -H "anthropic-version: 2023-06-01" | python -c "import sys,json; print('\n'.join(m['id'] for m in json.load(sys.stdin)['data'][:10]))"

echo ""
echo "== Dashboard =="
echo "Open http://127.0.0.1:8787/ui"
