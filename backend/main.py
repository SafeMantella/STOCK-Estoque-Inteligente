import os

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from erros import validation_exception_handler
from routers import auth, estoque, items, lista, stock, users

# O schema do banco é gerenciado pelo Alembic: rode `uv run alembic upgrade head`
# antes de subir a API (não há mais create_all na inicialização).

app = FastAPI(
    title="STOCK - Estoque Inteligente",
    description="API REST para gerenciamento de estoque doméstico e lista de compras automática.",
    version="2.0.0",
)

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


@app.get("/")
def root():
    return {"mensagem": "STOCK API v2.0 - acesse /docs para a documentação"}
