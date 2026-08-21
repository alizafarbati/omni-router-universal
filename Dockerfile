# syntax=docker/dockerfile:1
FROM python:3.12-slim

LABEL org.opencontainers.image.title="OmniRouter"
LABEL org.opencontainers.image.description="Smart free-tier AI router — OpenAI + Anthropic dual API"
LABEL org.opencontainers.image.source="https://github.com/alizafarbati/omni-router-universal"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    OMNI_PORT=8787 \
    OMNI_HOST=0.0.0.0

WORKDIR /app

# System deps (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt pyproject.toml README.md ./
COPY omni_router ./omni_router
COPY configs/providers.example.json ./configs/providers.example.json

RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install .

EXPOSE 8787

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -fsS http://127.0.0.1:${OMNI_PORT:-8787}/health || exit 1

CMD ["python", "-m", "omni_router"]
