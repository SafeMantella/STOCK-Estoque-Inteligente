from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from auth import authenticate_user, create_access_token
import limite
from database import get_db
from schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    # Limite de tentativas erradas por IP e por e-mail (429), conferido antes da senha
    ks = limite.chaves(request, "login", body.email)
    limite.checar(ks)
    user = authenticate_user(db, body.email, body.senha)
    if not user:
        limite.registrar_falha(ks)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
        )
    token = create_access_token({"sub": str(user.cod_usuario)})
    return TokenResponse(
        access_token=token,
        permissao=user.permissao,
        nome=user.nome,
        cod_estoque=user.cod_estoque,
        cod_usuario=user.cod_usuario,
    )
