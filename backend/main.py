from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from routers import auth, estoque, items, lista, stock, users

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="STOCK - Estoque Inteligente",
    description="API REST para gerenciamento de estoque doméstico e lista de compras automática.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(estoque.router)
app.include_router(items.router)
app.include_router(stock.router)
app.include_router(lista.router)


@app.get("/")
def root():
    return {"mensagem": "STOCK API v2.0 - acesse /docs para a documentação"}
