from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import case, select, update
from sqlalchemy.orm import Session, joinedload

from auth import get_current_user
from database import get_db
from models import Item, ItemEstoque, Usuario
from routers.items import checar_nome_livre, criar_item, flush_ou_409
from texto import normalizar_nome
from schemas import AjusteRequest, ItemEstoqueCreate, ItemEstoqueOut, ItemEstoqueUpdate, NovoItemEstoque

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


def _item_do_estoque(db: Session, cod_item: int, user: Usuario) -> ItemEstoque:
    ie = (
        db.query(ItemEstoque)
        .join(ItemEstoque.item)
        .filter(ItemEstoque.cod_item == cod_item, ItemEstoque.cod_estoque == user.cod_estoque,
                Item.excluido_em.is_(None))
        .first()
    )
    if not ie:
        # também para item excluído (por você ou por outro morador)
        raise HTTPException(status_code=404, detail="Item não encontrado no seu estoque")
    return ie


@router.get("", response_model=list[ItemEstoqueOut])
def list_stock(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    itens = (
        db.query(ItemEstoque)
        .join(ItemEstoque.item)
        .options(joinedload(ItemEstoque.item))
        .filter(ItemEstoque.cod_estoque == current_user.cod_estoque, Item.excluido_em.is_(None))
        .order_by(Item.descricao)
        .all()
    )
    return [_build_out(ie) for ie in itens]


@router.post("", response_model=ItemEstoqueOut, status_code=status.HTTP_201_CREATED)
def add_to_stock(
    body: ItemEstoqueCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    item = (
        db.query(Item)
        .filter(Item.cod_item == body.cod_item, Item.cod_estoque == current_user.cod_estoque,
                Item.excluido_em.is_(None))
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado no catálogo")
    existing = (
        db.query(ItemEstoque)
        .filter(ItemEstoque.cod_item == body.cod_item, ItemEstoque.cod_estoque == current_user.cod_estoque)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Este item já está no seu estoque")

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


@router.post("/novo-item", response_model=ItemEstoqueOut, status_code=status.HTTP_201_CREATED)
def novo_item_no_estoque(
    body: NovoItemEstoque,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Cadastra o produto no catálogo da casa e já coloca na dispensa (um passo só)."""
    item = criar_item(db, current_user.cod_estoque, body.descricao, body.categoria)
    ie = ItemEstoque(
        cod_item=item.cod_item,
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
    """Edita quantidades (valor absoluto) e/ou nome e categoria do item."""
    ie = _item_do_estoque(db, cod_item, current_user)
    if body.qtd_desejada is not None:
        ie.qtd_desejada = body.qtd_desejada
    if body.qtd_estoque is not None:
        ie.qtd_estoque = body.qtd_estoque
    if body.descricao is not None:
        ie.item.nome_normalizado = checar_nome_livre(db, current_user.cod_estoque, body.descricao, ie.cod_item)
        ie.item.descricao = body.descricao.strip()
    if body.categoria is not None:
        ie.item.categoria = body.categoria.strip()
    flush_ou_409(db)
    db.commit()
    db.refresh(ie)
    return _build_out(ie)


@router.post("/{cod_item}/ajuste", response_model=ItemEstoqueOut)
def ajustar_quantidade(
    cod_item: int,
    body: AjusteRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Soma delta (ex.: +1 / -1) à quantidade em casa, de forma atômica e nunca abaixo de 0.

    Um único UPDATE ... SET qtd_estoque = max(qtd_estoque + delta, 0): dois moradores
    ajustando ao mesmo tempo não perdem alterações (diferente do PUT, que grava valor absoluto).
    """
    novo = ItemEstoque.qtd_estoque + body.delta
    r = db.execute(
        update(ItemEstoque)
        .where(
            ItemEstoque.cod_item == cod_item,
            ItemEstoque.cod_estoque == current_user.cod_estoque,
            ItemEstoque.cod_item.in_(select(Item.cod_item).where(Item.excluido_em.is_(None))),
        )
        .values(qtd_estoque=case((novo < 0, 0), else_=novo))
        .execution_options(synchronize_session=False)
    )
    if r.rowcount == 0:
        db.rollback()
        raise HTTPException(status_code=404, detail="Item não encontrado no seu estoque")
    db.commit()
    ie = _item_do_estoque(db, cod_item, current_user)
    db.refresh(ie)
    return _build_out(ie)


@router.delete("/{cod_item}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_item(
    cod_item: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Tira o item da dispensa e do catálogo da casa (exclusão lógica: dá para desfazer).

    Marca item.excluido_em; as quantidades ficam guardadas para POST /{cod_item}/restaurar.
    """
    ie = _item_do_estoque(db, cod_item, current_user)
    ie.item.excluido_em = datetime.now(timezone.utc)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{cod_item}/restaurar", response_model=ItemEstoqueOut)
def restaurar_item(
    cod_item: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Desfaz a exclusão (qualquer morador da mesma casa). 409 se já existe outro ativo com o nome."""
    ie = (
        db.query(ItemEstoque)
        .join(ItemEstoque.item)
        .filter(ItemEstoque.cod_item == cod_item, ItemEstoque.cod_estoque == current_user.cod_estoque,
                Item.cod_estoque == current_user.cod_estoque)
        .first()
    )
    if not ie:
        raise HTTPException(status_code=404, detail="Item não encontrado no seu estoque")
    item = ie.item
    if item.excluido_em is None:
        return _build_out(ie)  # já está ativo: nada a desfazer
    outro = (
        db.query(Item)
        .filter(Item.cod_estoque == item.cod_estoque, Item.nome_normalizado == normalizar_nome(item.descricao),
                Item.excluido_em.is_(None), Item.cod_item != item.cod_item)
        .first()
    )
    if outro:
        raise HTTPException(
            status_code=409,
            detail=f'Não deu para desfazer: já existe "{outro.descricao}" no estoque. Edite ou exclua esse antes.',
        )
    item.excluido_em = None
    flush_ou_409(db)
    db.commit()
    db.refresh(ie)
    return _build_out(ie)
