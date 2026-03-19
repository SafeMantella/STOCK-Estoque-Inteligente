from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import get_current_user
from database import get_db
from models import ItemEstoque, Usuario
from schemas import CompraRequest, ListaItemOut

router = APIRouter(prefix="/api/lista", tags=["lista"])


@router.get("", response_model=list[ListaItemOut])
def gerar_lista(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    itens = (
        db.query(ItemEstoque)
        .filter(
            ItemEstoque.cod_estoque == current_user.cod_estoque,
            ItemEstoque.qtd_desejada > ItemEstoque.qtd_estoque,
        )
        .all()
    )
    return [
        ListaItemOut(
            cod_item=ie.cod_item,
            descricao=ie.item.descricao,
            categoria=ie.item.categoria,
            qtd_desejada=ie.qtd_desejada,
            qtd_estoque=ie.qtd_estoque,
            qtd_a_comprar=ie.qtd_desejada - ie.qtd_estoque,
        )
        for ie in itens
    ]


@router.post("/comprar")
def registrar_compra(
    body: CompraRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    ie = (
        db.query(ItemEstoque)
        .filter(
            ItemEstoque.cod_item == body.cod_item,
            ItemEstoque.cod_estoque == current_user.cod_estoque,
        )
        .first()
    )
    if not ie:
        raise HTTPException(status_code=404, detail="Item não encontrado no estoque")

    ie.qtd_estoque += body.qtd_comprada
    db.commit()
    return {"mensagem": "Compra registrada com sucesso", "qtd_estoque": ie.qtd_estoque}
