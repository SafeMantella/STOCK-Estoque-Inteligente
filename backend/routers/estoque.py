import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import get_current_user, require_admin
from database import get_db
from models import ConviteEstoque, Estoque, Usuario
from schemas import ConviteOut, EntrarEstoqueRequest, EstoqueCreate, EstoqueOut, MeuEstoqueOut

router = APIRouter(prefix="/api/estoque", tags=["estoque"])

CONVITE_VALIDADE = timedelta(days=7)


def _utc(dt: datetime) -> datetime:
    # SQLite devolve datetime sem fuso; tudo é gravado em UTC.
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def usar_convite(db: Session, codigo: str, user: Usuario) -> None:
    """Valida o convite, põe o usuário no estoque dele e marca o convite como usado (sem commit).

    Aceita usuário ainda não persistido (cadastro): nesse caso ele é inserido aqui.
    """
    convite = db.query(ConviteEstoque).filter(ConviteEstoque.codigo == (codigo or "").strip()).first()
    agora = datetime.now(timezone.utc)
    if not convite or convite.usado_por is not None or _utc(convite.expira_em) < agora:
        raise HTTPException(status_code=400, detail="Código de convite inválido, expirado ou já utilizado")
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
    est = db.query(Estoque).filter(Estoque.cod_estoque == current_user.cod_estoque).first()
    membros = db.query(Usuario).filter(Usuario.cod_estoque == current_user.cod_estoque).count()
    return MeuEstoqueOut(
        cod_estoque=est.cod_estoque,
        descricao=est.descricao,
        cod_dono=est.cod_dono,
        sou_dono=est.cod_dono == current_user.cod_usuario,
        membros=membros,
    )


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


@router.post("/entrar", response_model=MeuEstoqueOut)
def entrar_com_convite(
    body: EntrarEstoqueRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    usar_convite(db, body.codigo_convite, current_user)
    db.commit()
    db.refresh(current_user)
    return meu_estoque(db, current_user)
