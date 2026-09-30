from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ── Estoque ──────────────────────────────────────────────────────────────────

class EstoqueCreate(BaseModel):
    descricao: str

class EstoqueOut(BaseModel):
    cod_estoque: int
    descricao: str

    class Config:
        from_attributes = True

class MeuEstoqueOut(BaseModel):
    cod_estoque: int
    descricao: str
    cod_dono: Optional[int] = None
    sou_dono: bool
    membros: int
    itens: int
    # Pode aceitar convite de outro estoque sem deixar este órfão
    pode_trocar: bool

class ConviteOut(BaseModel):
    codigo: str
    cod_estoque: int
    expira_em: datetime

class EntrarEstoqueRequest(BaseModel):
    codigo_convite: str


# ── Item (catálogo) ───────────────────────────────────────────────────────────

class ItemCreate(BaseModel):
    descricao: str = Field(min_length=1, max_length=300)
    categoria: str = Field(min_length=1, max_length=300)

class ItemOut(BaseModel):
    cod_item: int
    descricao: str
    categoria: str

    class Config:
        from_attributes = True


# ── Usuario ───────────────────────────────────────────────────────────────────

SENHA_MIN = 8

class UsuarioCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=50)
    email: EmailStr
    senha: str = Field(min_length=SENHA_MIN)
    # Sem convite: cria um estoque NOVO e o usuário vira dono.
    # Com convite: entra no estoque de quem gerou o convite.
    # (cod_estoque/permissao não são mais aceitos no cadastro público.)
    descricao_estoque: Optional[str] = None
    codigo_convite: Optional[str] = None

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
