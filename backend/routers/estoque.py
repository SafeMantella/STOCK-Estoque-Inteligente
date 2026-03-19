from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from auth import require_admin
from database import get_db
from models import Estoque
from schemas import EstoqueCreate, EstoqueOut

router = APIRouter(prefix="/api/estoque", tags=["estoque"])


@router.post("", response_model=EstoqueOut, status_code=status.HTTP_201_CREATED)
def create_estoque(body: EstoqueCreate, db: Session = Depends(get_db)):
    est = Estoque(descricao=body.descricao)
    db.add(est)
    db.commit()
    db.refresh(est)
    return est


@router.get("", response_model=list[EstoqueOut])
def list_estoques(db: Session = Depends(get_db), _: object = Depends(require_admin)):
    return db.query(Estoque).order_by(Estoque.cod_estoque).all()
