import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

import limite
from auth import get_current_user, require_admin
from database import get_db
from models import ConviteEstoque, Estoque, ItemEstoque, Usuario
from schemas import ConviteInfoOut, ConviteOut, EntrarEstoqueRequest, EstoqueCreate, EstoqueOut, MeuEstoqueOut

router = APIRouter(prefix="/api/estoque", tags=["estoque"])

CONVITE_VALIDADE = timedelta(days=7)


def _utc(dt: datetime) -> datetime:
    # SQLite devolve datetime sem fuso; tudo é gravado em UTC.
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _resumo(db: Session, user: Usuario) -> MeuEstoqueOut:
    est = db.query(Estoque).filter(Estoque.cod_estoque == user.cod_estoque).first()
    membros = db.query(Usuario).filter(Usuario.cod_estoque == user.cod_estoque).count()
    itens = db.query(ItemEstoque).filter(ItemEstoque.cod_estoque == user.cod_estoque).count()
    sou_dono = est.cod_dono == user.cod_usuario
    dono = db.query(Usuario).filter(Usuario.cod_usuario == est.cod_dono).first() if est.cod_dono else None
    return MeuEstoqueOut(
        cod_estoque=est.cod_estoque,
        descricao=est.descricao,
        cod_dono=est.cod_dono,
        dono_nome=dono.nome if dono else None,
        sou_dono=sou_dono,
        membros=membros,
        itens=itens,
        # Dono só pode trocar se o estoque dele estiver vazio e sem outros moradores
        pode_trocar=(not sou_dono) or (itens == 0 and membros <= 1),
    )


BLOQUEIO_DONO = (
    "Você é dono de um estoque que já tem itens ou outros moradores. Entrar em outro estoque "
    "deixaria o seu sem dono. Use outra conta para aceitar este convite."
)


def validar_convite(db: Session, codigo: str, chaves_limite: list | None = None) -> ConviteEstoque:
    """Devolve o convite ou 400 com o motivo (não existe, já usado, expirado).

    Com chaves_limite, aplica o limite de tentativas erradas (429) contra adivinhação de códigos.
    """
    if chaves_limite:
        limite.checar(chaves_limite)
    try:
        return _validar_convite(db, codigo)
    except HTTPException:
        if chaves_limite:
            limite.registrar_falha(chaves_limite)
        raise


def _validar_convite(db: Session, codigo: str) -> ConviteEstoque:
    convite = db.query(ConviteEstoque).filter(ConviteEstoque.codigo == (codigo or "").strip()).first()
    if not convite:
        raise HTTPException(status_code=400, detail="Código de convite não encontrado. Confira se digitou certo.")
    if convite.usado_por is not None:
        raise HTTPException(status_code=400, detail="Este convite já foi usado. Peça um novo código para quem convidou.")
    if _utc(convite.expira_em) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Este convite expirou. Peça um novo código para quem convidou.")
    return convite


def _checar_pode_aceitar(db: Session, convite: ConviteEstoque, user: Usuario) -> None:
    if convite.cod_estoque == user.cod_estoque:
        raise HTTPException(status_code=400, detail="Você já faz parte deste estoque")
    if not _resumo(db, user).pode_trocar:
        raise HTTPException(status_code=409, detail=BLOQUEIO_DONO)


def usar_convite(db: Session, codigo: str, user: Usuario, chaves_limite: list | None = None) -> None:
    """Valida o convite, põe o usuário no estoque dele e marca o convite como usado (sem commit).

    Aceita usuário ainda não persistido (cadastro): nesse caso ele é inserido aqui.
    """
    convite = validar_convite(db, codigo, chaves_limite)
    agora = datetime.now(timezone.utc)
    user.cod_estoque = convite.cod_estoque
    if user.cod_usuario is None:
        db.add(user)
        db.flush()
    convite.usado_por = user.cod_usuario
    convite.usado_em = agora


@router.post("", response_model=EstoqueOut, status_code=status.HTTP_201_CREATED)
def create_estoque(
    body: EstoqueCreate,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
):
    est = Estoque(descricao=body.descricao)
    db.add(est)
    db.commit()
    db.refresh(est)
    return est


@router.get("", response_model=list[EstoqueOut])
def list_estoques(db: Session = Depends(get_db), _: object = Depends(require_admin)):
    return db.query(Estoque).order_by(Estoque.cod_estoque).all()


@router.get("/meu", response_model=MeuEstoqueOut)
def meu_estoque(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    return _resumo(db, current_user)


@router.post("/convites", response_model=ConviteOut, status_code=status.HTTP_201_CREATED)
def gerar_convite(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    est = db.query(Estoque).filter(Estoque.cod_estoque == current_user.cod_estoque).first()
    if not est or est.cod_dono != current_user.cod_usuario:
        raise HTTPException(status_code=403, detail="Apenas o dono do estoque pode gerar convites")
    agora = datetime.now(timezone.utc)
    convite = ConviteEstoque(
        codigo=secrets.token_urlsafe(9),
        cod_estoque=est.cod_estoque,
        criado_por=current_user.cod_usuario,
        criado_em=agora,
        expira_em=agora + CONVITE_VALIDADE,
    )
    db.add(convite)
    db.commit()
    return ConviteOut(codigo=convite.codigo, cod_estoque=est.cod_estoque, expira_em=agora + CONVITE_VALIDADE)


@router.get("/convites/{codigo}", response_model=ConviteInfoOut)
def consultar_convite(
    codigo: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Mostra de qual casa é o convite antes de aceitar (erro claro se não puder aceitar)."""
    convite = validar_convite(db, codigo, limite.chaves(request, "convite", current_user.email))
    _checar_pode_aceitar(db, convite, current_user)
    est = db.query(Estoque).filter(Estoque.cod_estoque == convite.cod_estoque).first()
    dono = db.query(Usuario).filter(Usuario.cod_usuario == est.cod_dono).first() if est.cod_dono else None
    return ConviteInfoOut(
        codigo=convite.codigo,
        cod_estoque=est.cod_estoque,
        descricao=est.descricao,
        dono_nome=dono.nome if dono else None,
        expira_em=_utc(convite.expira_em),
    )


@router.post("/entrar", response_model=MeuEstoqueOut)
def entrar_com_convite(
    body: EntrarEstoqueRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    # Aceitar convite exige estar logado (e confirmação no frontend). Não é mais
    # possível pelo login, que trocava o estoque do usuário sem aviso.
    ks = limite.chaves(request, "convite", current_user.email)
    _checar_pode_aceitar(db, validar_convite(db, body.codigo_convite, ks), current_user)
    usar_convite(db, body.codigo_convite, current_user)
    db.commit()
    db.refresh(current_user)
    return _resumo(db, current_user)
