from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from auth import get_current_user, hash_password, require_admin
from database import get_db
from models import Estoque, Usuario
from schemas import UsuarioCreate, UsuarioOut

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def create_user(body: UsuarioCreate, db: Session = Depends(get_db)):
    existing = db.query(Usuario).filter(Usuario.email == body.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    cod_estoque = body.cod_estoque

    if not cod_estoque:
        if not body.descricao_estoque:
            raise HTTPException(
                status_code=400,
                detail="Informe cod_estoque ou descricao_estoque para criar um novo estoque",
            )
        novo_estoque = Estoque(descricao=body.descricao_estoque)
        db.add(novo_estoque)
        db.flush()
        cod_estoque = novo_estoque.cod_estoque
    else:
        est = db.query(Estoque).filter(Estoque.cod_estoque == cod_estoque).first()
        if not est:
            raise HTTPException(status_code=404, detail="Estoque não encontrado")

    user = Usuario(
        nome=body.nome,
        email=body.email,
        senha=hash_password(body.senha),
        permissao="usuario",
        cod_estoque=cod_estoque,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("", response_model=list[UsuarioOut])
def list_users(
    nome: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    permissao: Optional[str] = Query(None),
    cod_usuario: Optional[int] = Query(None),
    cod_estoque: Optional[int] = Query(None),
    local: bool = Query(False, description="Filtrar apenas usuários do estoque do usuário logado"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    # Usuários não-admin só podem listar usuários do próprio estoque
    if getattr(current_user, "permissao", None) != "admin":
        local = True
        cod_estoque = None

    q = db.query(Usuario)
    if local:
        q = q.filter(Usuario.cod_estoque == current_user.cod_estoque)
    if nome:
        q = q.filter(Usuario.nome.ilike(f"%{nome}%"))
    if email:
        q = q.filter(Usuario.email.ilike(f"%{email}%"))
    if permissao:
        q = q.filter(Usuario.permissao.ilike(f"%{permissao}%"))
    if cod_usuario:
        q = q.filter(Usuario.cod_usuario == cod_usuario)
    if cod_estoque:
        q = q.filter(Usuario.cod_estoque == cod_estoque)
    return q.order_by(Usuario.cod_usuario.desc()).all()


@router.get("/me", response_model=UsuarioOut)
def get_me(current_user: Usuario = Depends(get_current_user)):
    return current_user
