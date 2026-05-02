# STOCK - Estoque Inteligente

## Project Overview

STOCK is a **residential inventory management and automatic shopping list generator** web application. Originally built as a TCC (Trabalho de Conclusão de Curso) project at IFMS (Instituto Federal de Mato Grosso do Sul) by Pedro Arfux and Vitor Gabriel.

The application was **originally written in PHP + MySQL** and is currently being **refactored to Python (FastAPI) + PostgreSQL** on the `refactor/python-fastapi` branch.

### Core Business Logic
- Users manage household pantries ("dispensas"/estoques)
- Multiple users can share the same estoque
- Each item in an estoque has `qtd_desejada` (desired qty) and `qtd_estoque` (current qty)
- The system **automatically generates shopping lists** when `qtd_desejada > qtd_estoque`
- Shopping list calculates `qtd_a_comprar = qtd_desejada - qtd_estoque`

## Tech Stack

### Backend (Python)
- **Framework**: FastAPI v0.115.5
- **ORM**: SQLAlchemy 2.0.36
- **Database**: PostgreSQL (via psycopg2-binary)
- **Auth**: JWT tokens (python-jose) + bcrypt (passlib) with SHA1 legacy fallback
- **Validation**: Pydantic v2 with email support
- **Migrations**: Alembic 1.14.0 (listed but `create_all` is used in practice)
- **Server**: Uvicorn

### Frontend
- **HTML5** + **Vanilla JavaScript** (no framework)
- **CSS**: Bootstrap 5.3.3 (CDN) + `frontend/css/custom.css`
- **API calls**: fetch-based wrapper in `frontend/js/api.js`
- **Auth**: localStorage-based token/session in `frontend/js/auth.js`
- **Served via**: `python -m http.server 3000`

## Project Architecture

```
STOCK-Estoque-Inteligente/
├── backend/
│   ├── main.py              # FastAPI app entry, CORS, router registration
│   ├── database.py          # SQLAlchemy engine, session, Base
│   ├── models.py            # 6 ORM models (Estoque, Item, Usuario, ItemEstoque, ListaCompra, ListaItem)
│   ├── schemas.py           # Pydantic schemas for all request/response models
│   ├── auth.py              # JWT, bcrypt, SHA1 fallback, get_current_user, require_admin
│   ├── requirements.txt     # Python dependencies
│   └── routers/
│       ├── auth.py          # POST /api/auth/login
│       ├── users.py         # POST /api/users, GET /api/users, GET /api/users/me
│       ├── estoque.py       # POST /api/estoque, GET /api/estoque (admin)
│       ├── items.py         # POST /api/items (admin), GET /api/items
│       ├── stock.py         # GET/POST/PUT /api/stock (user's items in estoque)
│       └── lista.py         # GET /api/lista (shopping list), POST /api/lista/comprar
├── frontend/
│   ├── index.html           # Login page (entry point)
│   ├── menu.html            # Main menu (post-login)
│   ├── css/custom.css       # Custom styles (green theme, CSS vars)
│   ├── js/
│   │   ├── api.js           # apiCall() wrapper, showMsg(), API_BASE config
│   │   └── auth.js          # requireAuth(), getUser(), isAdmin(), logout()
│   └── pages/               # 15 HTML pages (estoque, lista, cadastro, buscar, etc.)
├── .env                     # DATABASE_URL, SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES
├── API.md                   # Detailed API docs & DB schema (migration guide from PHP)
├── tcc.sql                  # Original MySQL schema (6 tables, legacy)
└── [legacy PHP files]       # processa.php, connection.php, config.php, etc.
```

## Git Branching

- **`main`**: Original PHP+MySQL implementation (legacy)
- **`refactor/python-fastapi`** (current): Active refactored version with FastAPI backend + vanilla JS frontend

## Database Schema

6 tables with clear relationships:

| Table | Purpose | Key Relationships |
|---|---|---|
| `estoque` | Storage locations/pantries | Has many usuarios, itemestoques, listacompras |
| `item` | Product catalog | Has many itemestoques, listaitens |
| `usuario` | Users with auth | Belongs to estoque; has `permissao` (admin/usuario) |
| `itemestoque` | Pivot: items in a specific estoque | Composite PK (cod_item, cod_estoque); tracks qtd_desejada/qtd_estoque |
| `listacompra` | Shopping list headers | Belongs to estoque; has status (aberta/fechada) |
| `listaitem` | Shopping list line items | Composite PK (cod_item, cod_lista); has status (pendente/comprado) |

## API Endpoints Summary

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/auth/login` | Public | Login, returns JWT + user metadata |
| `POST` | `/api/users` | Public | Register user (optionally creates estoque) |
| `GET` | `/api/users` | Admin | List/search users |
| `GET` | `/api/users/me` | User | Get current user info |
| `POST` | `/api/estoque` | Public | Create a new estoque |
| `GET` | `/api/estoque` | Admin | List all estoques |
| `POST` | `/api/items` | Admin | Add item to catalog |
| `GET` | `/api/items` | User | Search items catalog |
| `GET` | `/api/stock` | User | List user's estoque items |
| `POST` | `/api/stock` | User | Add item to user's estoque |
| `PUT` | `/api/stock/{cod_item}` | User | Update item quantities |
| `GET` | `/api/lista` | User | Generate shopping list |
| `POST` | `/api/lista/comprar` | User | Register a purchase (updates estoque) |

## Authentication & Authorization

- **JWT tokens** stored in `localStorage` on the frontend
- Token payload contains `sub` = `cod_usuario`
- Password hashing: **bcrypt** (primary) with **SHA1 fallback** for legacy MySQL users (auto-migrates on login)
- Two permission levels: `admin` and `usuario`
- `get_current_user` dependency extracts user from JWT
- `require_admin` dependency enforces admin-only access
- Token expiry: 480 minutes (8 hours) by default

## Key Patterns & Conventions

### Backend
- All API routes are prefixed with `/api/`
- Router modules in `backend/routers/` use `APIRouter` with prefix and tags
- Database sessions managed via `get_db()` generator dependency
- Response models use `from_attributes = True` (Pydantic v2 ORM mode)
- Portuguese used in: model fields, error messages, schema names
- English used in: code structure, variable names where idiomatic

### Frontend
- Every protected page calls `requireAuth()` at script start
- `apiCall(method, path, body)` handles auth headers, 401 redirects, error parsing
- `showMsg(text, type)` displays Bootstrap alerts in `#msg-area` divs
- User session data in localStorage: token, nome, permissao, cod_estoque, cod_usuario
- Admin features revealed via `isAdmin()` check (`display:none` → `display:block`)
- All pages use Bootstrap grid system (container-fluid, row, col-md-*)

### CSS/Design
- Green theme: `--btn-green: #2de510`, `--btn-hover: #91ff80`
- Gray background: `--bg-color: #e2e2e2`
- Custom class `.btn-stock` for primary actions
- Input styling with hover-to-white effect

## Environment Variables

```env
DATABASE_URL=postgresql://postgres:PASSWORD@localhost:5432/stock
SECRET_KEY=troque-esta-chave-em-producao
ACCESS_TOKEN_EXPIRE_MINUTES=480
```

## Running the Project

```bash
# Backend (terminal 1)
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
# → http://localhost:8000 (API) | http://localhost:8000/docs (Swagger)

# Frontend (terminal 2)
cd frontend
python -m http.server 3000
# → http://localhost:3000
```

> **Note**: Database tables are auto-created on first backend startup via `Base.metadata.create_all()`. No manual migrations needed.

## Legacy Code

The root directory contains legacy PHP files from the original implementation:
- `processa.php` — Monolithic request handler (all business logic)
- `connection.php` / `config.php` — MySQL connection
- `tcc.sql` — Original MySQL schema
- Various `.html` files — Old frontend pages
- Multiple `css*/` directories — Old stylesheets

These files are kept for reference but are **not part of the active refactored version**.

## Known Considerations

1. **CORS is wide open** (`allow_origins=["*"]`) — needs restricting for production
2. **No Alembic migrations configured** yet despite being in requirements.txt
3. **`estoque` creation endpoint is public** — potential security concern
4. **No password complexity validation** on user registration
5. **Frontend uses `http://localhost:8000/api`** hardcoded in `api.js` — needs env-based config for deployment
6. **No tests** exist yet
7. **`ListaCompra` and `ListaItem` models exist** but the shopping list logic in `routers/lista.py` queries `ItemEstoque` directly (the list tables are unused in the refactored version so far)
