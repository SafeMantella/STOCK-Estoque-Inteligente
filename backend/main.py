import os
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException

from database import get_db
from erros import validation_exception_handler
from routers import auth, estoque, items, lista, stock, users

# O schema do banco é gerenciado pelo Alembic: rode `uv run alembic upgrade head`
# antes de subir a API (não há mais create_all na inicialização).

app = FastAPI(
    title="STOCK - Estoque Inteligente",
    description="API REST para gerenciamento de estoque doméstico e lista de compras automática.",
    version="2.0.0",
)

# CORS só é necessário quando o frontend está em outra origem (dev: :3000 -> :8000).
# Em produção o FastAPI serve o frontend e a API na mesma origem (ver FRONTEND_DIR).
# Origens separadas por vírgula (ex.: "http://localhost:3000,http://192.168.0.10:3000")
allowed_origins = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(RequestValidationError, validation_exception_handler)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(estoque.router)
app.include_router(items.router)
app.include_router(stock.router)
app.include_router(lista.router)


# Commit publicado: GIT_COMMIT (build arg do Dockerfile) ou a variável que o host define sozinho
# (Render, Railway, Coolify). Vazia conta como não definida (o ARG do Dockerfile é vazio por padrão).
VARIAVEIS_COMMIT = ("GIT_COMMIT", "RENDER_GIT_COMMIT", "RAILWAY_GIT_COMMIT_SHA", "SOURCE_COMMIT")


def commit_publicado() -> str:
    for nome in VARIAVEIS_COMMIT:
        valor = os.getenv(nome, "").strip()
        if valor:
            return valor
    return "desconhecido"


@app.get("/api/health", tags=["health"])
def health(db: Session = Depends(get_db)):
    """Verificação de saúde para o host (load balancer / health check): testa o banco
    e informa o commit publicado, para conferir se o deploy é o esperado."""
    commit = commit_publicado()
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(
            status_code=503, content={"status": "erro", "banco": "indisponível", "commit": commit}
        )
    return {"status": "ok", "banco": "ok", "commit": commit}


class FrontendFiles(StaticFiles):
    """Arquivos do frontend; não expõe arquivos ocultos nem notas internas (.md)."""

    async def get_response(self, path, scope):
        partes = path.replace("\\", "/").split("/")
        if path.endswith(".md") or any(p.startswith(".") and p not in (".", "") for p in partes):
            raise StarletteHTTPException(status_code=404)
        return await super().get_response(path, scope)


# Frontend estático na mesma origem: "/" -> index.html, "/pages/..." etc.; "/api" continua
# sendo a API (as rotas acima têm prioridade sobre este mount). FRONTEND_DIR permite apontar
# para outro diretório (a imagem Docker usa /app/frontend).
FRONTEND_DIR = Path(os.getenv("FRONTEND_DIR", Path(__file__).resolve().parent.parent / "frontend"))
if FRONTEND_DIR.is_dir():
    app.mount("/", FrontendFiles(directory=FRONTEND_DIR, html=True), name="frontend")
else:
    @app.get("/")
    def root():
        return {"mensagem": "STOCK API v2.0 - acesse /docs para a documentação"}
