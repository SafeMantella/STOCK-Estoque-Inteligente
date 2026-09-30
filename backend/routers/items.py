from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import Item, Usuario
from schemas import ItemCreate, ItemOut

router = APIRouter(prefix="/api/items", tags=["items"])


@router.post("", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
def create_item(
    body: ItemCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    # Qualquer morador cadastra produtos, sempre no catálogo do próprio estoque
    descricao = body.descricao.strip()
    if not descricao:
        raise HTTPException(status_code=422, detail="Informe a descrição do item")
    duplicado = (
        db.query(Item)
        .filter(Item.cod_estoque == current_user.cod_estoque, func.lower(Item.descricao) == descricao.lower())
        .first()
    )
    if duplicado:
        raise HTTPException(status_code=409, detail=f"Já existe um item \"{duplicado.descricao}\" no seu catálogo")
    item = Item(descricao=descricao, categoria=body.categoria.strip(), cod_estoque=current_user.cod_estoque)
    db.add(item)
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
    q = db.query(Item).filter(Item.cod_estoque == current_user.cod_estoque)
    if cod_item:
        q = q.filter(Item.cod_item == cod_item)
    if descricao:
        q = q.filter(Item.descricao.ilike(f"%{descricao}%"))
    if categoria:
        q = q.filter(Item.categoria.ilike(f"%{categoria}%"))
    return q.order_by(Item.cod_item.desc()).all()
