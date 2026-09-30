from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import Item, Usuario
from schemas import ItemCreate, ItemOut
from texto import normalizar_nome

router = APIRouter(prefix="/api/items", tags=["items"])


def _erro_duplicado(existente: Optional[Item]) -> HTTPException:
    nome = f' "{existente.descricao}"' if existente else " com esse nome"
    return HTTPException(status_code=409, detail=f"Já existe um item{nome} no catálogo da sua casa")


def checar_nome_livre(db: Session, cod_estoque: int, descricao: str, ignorar_cod_item: Optional[int] = None) -> str:
    """Valida a descrição e devolve o nome normalizado; 409 se já existir na casa."""
    descricao = (descricao or "").strip()
    if not descricao:
        raise HTTPException(status_code=422, detail="Informe a descrição do item")
    norm = normalizar_nome(descricao)
    q = db.query(Item).filter(Item.cod_estoque == cod_estoque, Item.nome_normalizado == norm,
                              Item.excluido_em.is_(None))
    if ignorar_cod_item is not None:
        q = q.filter(Item.cod_item != ignorar_cod_item)
    existente = q.first()
    if existente:
        raise _erro_duplicado(existente)
    return norm


def criar_item(db: Session, cod_estoque: int, descricao: str, categoria: str) -> Item:
    """Adiciona o item ao catálogo da casa (sem commit). 409 em nome duplicado."""
    norm = checar_nome_livre(db, cod_estoque, descricao)
    item = Item(descricao=descricao.strip(), categoria=categoria.strip(), cod_estoque=cod_estoque,
                nome_normalizado=norm)
    db.add(item)
    flush_ou_409(db)
    return item


def flush_ou_409(db: Session) -> None:
    # O índice único parcial (cod_estoque, nome_normalizado) WHERE excluido_em IS NULL
    # protege contra corrida entre moradores
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise _erro_duplicado(None)


@router.post("", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
def create_item(
    body: ItemCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    # Qualquer morador cadastra produtos, sempre no catálogo do próprio estoque
    item = criar_item(db, current_user.cod_estoque, body.descricao, body.categoria)
    db.commit()
    db.refresh(item)
    return item


@router.get("", response_model=list[ItemOut])
def list_items(
    cod_item: Optional[int] = Query(None),
    descricao: Optional[str] = Query(None),
    categoria: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    q = db.query(Item).filter(Item.cod_estoque == current_user.cod_estoque, Item.excluido_em.is_(None))
    if cod_item:
        q = q.filter(Item.cod_item == cod_item)
    if descricao:
        q = q.filter(Item.descricao.ilike(f"%{descricao}%"))
    if categoria:
        q = q.filter(Item.categoria.ilike(f"%{categoria}%"))
    return q.order_by(Item.cod_item.desc()).all()
