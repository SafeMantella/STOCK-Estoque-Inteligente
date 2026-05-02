from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from auth import get_current_user
from database import get_db
from models import Item, ItemEstoque, Usuario
from schemas import ItemEstoqueCreate, ItemEstoqueOut, ItemEstoqueUpdate

router = APIRouter(prefix="/api/stock", tags=["stock"])


def _build_out(ie: ItemEstoque) -> ItemEstoqueOut:
    return ItemEstoqueOut(
        cod_item=ie.cod_item,
        cod_estoque=ie.cod_estoque,
        qtd_desejada=ie.qtd_desejada,
        qtd_estoque=ie.qtd_estoque,
        descricao=ie.item.descricao,
        categoria=ie.item.categoria,
    )


@router.get("", response_model=list[ItemEstoqueOut])
def list_stock(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    itens = (
        db.query(ItemEstoque)
        .options(joinedload(ItemEstoque.item))
        .filter(ItemEstoque.cod_estoque == current_user.cod_estoque)
        .all()
    )
    return [_build_out(ie) for ie in itens]


@router.post("", response_model=ItemEstoqueOut, status_code=status.HTTP_201_CREATED)
def add_to_stock(
    body: ItemEstoqueCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    item = db.query(Item).filter(Item.cod_item == body.cod_item).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado no catálogo")

    existing = (
        db.query(ItemEstoque)
        .filter(
            ItemEstoque.cod_item == body.cod_item,
            ItemEstoque.cod_estoque == current_user.cod_estoque,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Item já adicionado ao estoque")

    # Validação server-side para impedir quantidades negativas ou zero
    if body.qtd_desejada is None or body.qtd_desejada <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Quantidade desejada deve ser maior que zero",
        )
    if body.qtd_estoque is None or body.qtd_estoque <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Quantidade em estoque deve ser maior que zero",
        )

    ie = ItemEstoque(
        cod_item=body.cod_item,
        cod_estoque=current_user.cod_estoque,
        qtd_desejada=body.qtd_desejada,
        qtd_estoque=body.qtd_estoque,
    )
    db.add(ie)
    db.commit()
    db.refresh(ie)
    return _build_out(ie)


@router.put("/{cod_item}", response_model=ItemEstoqueOut)
def update_stock_item(
    cod_item: int,
    body: ItemEstoqueUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    ie = (
        db.query(ItemEstoque)
        .filter(
            ItemEstoque.cod_item == cod_item,
            ItemEstoque.cod_estoque == current_user.cod_estoque,
        )
        .first()
    )
    if not ie:
        raise HTTPException(status_code=404, detail="Item não encontrado no estoque")

    # Validação server-side para impedir atualização com quantidades negativas
    if body.qtd_desejada is not None and body.qtd_desejada < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Quantidade desejada não pode ser negativa",
        )
    if body.qtd_estoque is not None and body.qtd_estoque < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Quantidade em estoque não pode ser negativa",
        )

    if body.qtd_desejada is not None:
        ie.qtd_desejada = body.qtd_desejada
    if body.qtd_estoque is not None:
        ie.qtd_estoque = body.qtd_estoque

    db.commit()
    db.refresh(ie)
    return _build_out(ie)
