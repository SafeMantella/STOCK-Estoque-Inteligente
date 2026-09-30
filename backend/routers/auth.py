from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth import authenticate_user, create_access_token
from database import get_db
from routers.estoque import usar_convite
from schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, body.email, body.senha)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
        )
    if body.codigo_convite:
        # Usuário existente entrando no estoque de quem convidou
        usar_convite(db, body.codigo_convite, user)
        db.commit()
        db.refresh(user)
    token = create_access_token({"sub": str(user.cod_usuario)})
    return TokenResponse(
        access_token=token,
        permissao=user.permissao,
        nome=user.nome,
        cod_estoque=user.cod_estoque,
        cod_usuario=user.cod_usuario,
    )
