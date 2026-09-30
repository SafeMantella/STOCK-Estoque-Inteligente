# Imagem única de produção: API FastAPI + frontend estático na mesma origem.
#   docker build -t stock .
#   docker run -p 8000:8000 -e DATABASE_URL=... -e SECRET_KEY=... stock
# Serve para Render, Railway, Fly.io ou qualquer host que rode um Dockerfile.
# Ao iniciar roda `alembic upgrade head` e depois uvicorn em $PORT (ver backend/start.sh).
FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.20 /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app/backend

# Dependências primeiro (camada em cache enquanto uv.lock não mudar); sem as de dev (pytest)
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY backend/ ./
COPY frontend/ /app/frontend/

ENV PATH="/app/.venv/bin:$PATH" \
    FRONTEND_DIR=/app/frontend \
    PORT=8000

RUN useradd --system --no-create-home --uid 10001 stock
USER stock

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8000\")}/api/health', timeout=4)"

CMD ["sh", "start.sh"]
