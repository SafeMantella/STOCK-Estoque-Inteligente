from typing import Optional
from pydantic import BaseModel, EmailStr


# ── Estoque ──────────────────────────────────────────────────────────────────

class EstoqueCreate(BaseModel):
    descricao: str

class EstoqueOut(BaseModel):
    cod_estoque: int
    descricao: str

    class Config:
        from_attributes = True


# ── Item (catálogo) ───────────────────────────────────────────────────────────

class ItemCreate(BaseModel):
    descricao: str
    categoria: str

class ItemOut(BaseModel):
    cod_item: int
    descricao: str
    categoria: str

    class Config:
        from_attributes = True


# ── Usuario ───────────────────────────────────────────────────────────────────

class UsuarioCreate(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    permissao: Optional[str] = "usuario"
    cod_estoque: Optional[int] = None
    descricao_estoque: Optional[str] = None  # cria estoque novo se informado

class UsuarioOut(BaseModel):
    cod_usuario: int
    nome: str
    email: str
    permissao: str
    cod_estoque: int

    class Config:
        from_attributes = True


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    senha: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    permissao: str
    nome: str
    cod_estoque: int
    cod_usuario: int


# ── ItemEstoque ───────────────────────────────────────────────────────────────

class ItemEstoqueCreate(BaseModel):
    cod_item: int
    qtd_desejada: int
    qtd_estoque: int

class ItemEstoqueUpdate(BaseModel):
    qtd_desejada: Optional[int] = None
    qtd_estoque: Optional[int] = None

class ItemEstoqueOut(BaseModel):
    cod_item: int
    cod_estoque: int
    qtd_desejada: int
    qtd_estoque: int
    descricao: str
    categoria: str

    class Config:
        from_attributes = True


# ── Lista de Compras ──────────────────────────────────────────────────────────

class ListaItemOut(BaseModel):
    cod_item: int
    descricao: str
    categoria: str
    qtd_desejada: int
    qtd_estoque: int
    qtd_a_comprar: int

class CompraRequest(BaseModel):
    cod_item: int
    qtd_comprada: int
