#!/bin/sh
# Comando de início em produção (Docker ou host sem Docker):
#   1. aplica as migrations pendentes (alembic upgrade head)
#   2. sobe API + frontend (mesma origem) na porta $PORT (padrão 8000)
# Variáveis: DATABASE_URL, SECRET_KEY (obrigatórias), CORS_ORIGINS, PORT, WEB_CONCURRENCY.
# Sem Docker, rode dentro do ambiente do uv:  cd backend && uv run --no-dev sh start.sh
set -e
cd "$(dirname "$0")"
alembic upgrade head
# --proxy-headers: o host termina o HTTPS num proxy e repassa X-Forwarded-Proto/For.
exec uvicorn main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --workers "${WEB_CONCURRENCY:-1}" \
  --proxy-headers \
  --forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-*}"
