from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from auth import get_current_user, require_admin
from database import get_db
from models import Item, Usuario
from schemas import ItemCreate, ItemOut

router = APIRouter(prefix="/api/items", tags=["items"])


@router.post("", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
def create_item(body: ItemCreate, db: Session = Depends(get_db), _: object = Depends(require_admin)):
    item = Item(descricao=body.descricao, categoria=body.categoria)
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
    _: Usuario = Depends(get_current_user),
):
    q = db.query(Item)
    if cod_item:
        q = q.filter(Item.cod_item == cod_item)
    if descricao:
        q = q.filter(Item.descricao.ilike(f"%{descricao}%"))
    if categoria:
        q = q.filter(Item.categoria.ilike(f"%{categoria}%"))
    return q.order_by(Item.cod_item.desc()).all()
