# Backend Guidelines

## Adding New Endpoints

1. Create or edit a router in `backend/routers/`
2. Use `APIRouter(prefix="/api/<resource>", tags=["<resource>"])`
3. Define Pydantic schemas in `backend/schemas.py` with `from_attributes = True`
4. Add corresponding SQLAlchemy model in `backend/models.py` if needed
5. Register the router in `backend/main.py` via `app.include_router()`
6. Use `Depends(get_current_user)` for authenticated routes
7. Use `Depends(require_admin)` for admin-only routes

## Auth Dependency Pattern

```python
from auth import get_current_user, require_admin
from models import Usuario

# Any logged-in user
def my_endpoint(current_user: Usuario = Depends(get_current_user)):
    estoque_id = current_user.cod_estoque  # user's estoque

# Admin only
def admin_endpoint(_: object = Depends(require_admin)):
    ...
```

## Database Session Pattern

```python
from database import get_db
from sqlalchemy.orm import Session

def my_endpoint(db: Session = Depends(get_db)):
    result = db.query(MyModel).filter(...).all()
```

## Error Handling

- Use `HTTPException` with Portuguese error messages
- Common status codes: 400 (validation), 401 (auth), 403 (forbidden), 404 (not found), 409 (conflict)

## Building Response DTOs from Joins

When the response needs data from related models, build the Pydantic schema manually:

```python
def _build_out(ie: ItemEstoque) -> ItemEstoqueOut:
    return ItemEstoqueOut(
        cod_item=ie.cod_item,
        descricao=ie.item.descricao,  # from relationship
        ...
    )
```
