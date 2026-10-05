<h3 align="center">
    <img src="logo.jpeg" width="300px">
    <br><br>
    <h1 align="center">STOCK - Estoque Inteligente</h1>
</h3>

<p align="center">
  <img src="https://img.shields.io/github/license/SafeMantella/STOCK-Estoque-Inteligente?style=flat&logo">
</p>

## 🔖 Sobre

O <strong>STOCK</strong> é um sistema de gerenciamento de estoque e gerador de lista de compras para sua casa.

Aplicação web construída como parte do Trabalho de Conclusão de Curso no [Instituto Federal de Mato Grosso do Sul](https://www.ifms.edu.br/).
Projeto feito em dupla por **[Pedro Arfux](https://github.com/SafeMantella)** e **[Vitor Gabriel](https://github.com/VitorGSF)** e 
orientado por **[Luiz Lomba](https://www.linkedin.com/in/luiz-fernando-delboni-lomba-b64aa018/)**.

## 🚀 Tecnologias

Esse projeto foi desenvolvido com as seguintes tecnologias:

- [Python](https://www.python.org/) + [FastAPI](https://fastapi.tiangolo.com/)
- [PostgreSQL](https://www.postgresql.org/) + [SQLAlchemy](https://www.sqlalchemy.org/)
- [HTML](https://developer.mozilla.org/pt-BR/docs/Web/HTML) + [CSS](https://developer.mozilla.org/pt-BR/docs/Web/CSS) + [JavaScript](https://developer.mozilla.org/pt-BR/docs/Web/JavaScript)
- [Bootstrap 5](https://getbootstrap.com/)

## ⚙️ Como rodar a aplicação

A aplicação tem duas partes: **backend** (API FastAPI, porta `8000`) e **frontend** (HTML estático).
O próprio backend também serve o frontend: `http://localhost:8000/` abre o app e `/api` é a API (mesma origem,
é assim em produção — ver [DEPLOY.md](DEPLOY.md)). Em desenvolvimento dá para servir o frontend à parte na porta
`3000`: nesse caso o `frontend/js/api.js` chama `http://<mesmo host>:8000/api` (CORS liberado para
`http://localhost:3000` e `http://127.0.0.1:3000`; outras origens via `CORS_ORIGINS`).

### Pré-requisitos

- [uv](https://docs.astral.sh/uv/) (recomendado) **ou** Python 3.10+ com `pip`
- Python 3 para servir o frontend
- Banco: **SQLite** (nada a instalar, ideal para desenvolvimento) ou PostgreSQL

### 1. Clone o repositório

```bash
git clone https://github.com/SafeMantella/STOCK-Estoque-Inteligente.git
cd STOCK-Estoque-Inteligente
git checkout develop   # branch de desenvolvimento (main = versão estável)
```

### 2. Configure as variáveis de ambiente do backend

```bash
cp backend/.env.example backend/.env
```

Edite `backend/.env`. Para rodar local **sem Postgres**, use SQLite:

```env
DATABASE_URL=sqlite:///./stock.db
SECRET_KEY=<gere com: python3 -c "import secrets; print(secrets.token_hex(32))">   # obrigatória
ACCESS_TOKEN_EXPIRE_MINUTES=43200
# opcional: CORS_ORIGINS=http://localhost:3000,http://192.168.0.10:3000
```

> **`SECRET_KEY` é obrigatória:** sem ela (ou com o valor de exemplo) o backend se recusa a subir.

Para Postgres: `DATABASE_URL=postgresql://postgres:SUA_SENHA@localhost:5432/stock` (crie antes o banco `stock`).

### 3. Suba o backend (com uv)

```bash
cd backend
uv run alembic upgrade head          # cria/atualiza as tabelas (rode sempre que atualizar o código)
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

O `uv run` cria o ambiente virtual (`backend/.venv`) e instala as dependências do `pyproject.toml`/`uv.lock`
automaticamente. Sem uv: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/alembic upgrade head && .venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000`.

API em `http://localhost:8000` — documentação interativa (Swagger) em `http://localhost:8000/docs`.

Testes automatizados (API, banco SQLite temporário):

```bash
cd backend
uv run pytest
```

Testes de tela no navegador (Playwright; sobem o app num banco temporário, não mexem no seu):

```bash
cd backend
uv run --with playwright pytest ../e2e     # usa google-chrome/chromium do sistema ou CHROME_PATH
```

> O schema é versionado com **Alembic** (`backend/migrations/`); a API **não** cria tabelas sozinha.
> Banco novo ou atualização de código: `uv run alembic upgrade head`. Nova mudança de schema:
> altere `models.py` e gere `uv run alembic revision --autogenerate -m "descrição"` (revise o arquivo gerado).
> Banco criado por uma versão anterior ao Alembic (commit `1be9a89`): `uv run alembic stamp 0001` e depois `upgrade head`.
>
> Contas de teste para desenvolvimento: com `STOCK_ENV=dev` no `backend/.env`, `uv run python seed_dev.py`
> (depois do `upgrade head`). Sem `STOCK_ENV=dev` o seed se recusa a rodar; **nunca** em produção.

### 4. Suba o frontend

Em outro terminal, a partir da raiz do projeto:

```bash
cd frontend
python3 -m http.server 3000 --bind 0.0.0.0
```

Acesse a aplicação em **`http://localhost:3000`** (ou direto em `http://localhost:8000`, servida pelo backend).

### Alternativa: Docker Compose (Postgres)

```bash
docker compose up -d --build
```

Sobe Postgres 17 + a imagem única da aplicação (`Dockerfile` da raiz: API + frontend em **`http://localhost:8000`**;
roda `alembic upgrade head` ao iniciar). É obrigatório definir `SECRET_KEY` num arquivo `.env` na raiz do projeto.

### Publicar (produção)

Ver **[DEPLOY.md](DEPLOY.md)**: variáveis de ambiente, comando de início, passos genéricos por host, backup do Postgres.

### Como usar (fluxo básico)

1. **Cadastre-se** — o cadastro cria o seu estoque (dispensa) e você vira o **dono** dele.
2. **Cadastrar Novo Item** — cadastre os produtos (ex.: "Leite 1L", categoria Laticínios).
3. **Listar Itens** — adicione o item ao seu estoque com a quantidade **mínima desejada** e a **atual**.
4. **Meu Estoque** — atualize as quantidades conforme consome.
5. **Lista de Compras** — gerada automaticamente com tudo que está abaixo do mínimo; "Comprar" soma a quantidade ao estoque.
6. **Usuários em seu estoque / Convidar** — o dono gera um **código de convite** (uso único, 7 dias) e envia para quem mora com ele.
   A pessoa informa o código ao se cadastrar ou, se já tem conta, entra e aceita o convite na tela de Usuários (com confirmação). Quem é dono de um estoque com itens ou outros moradores não pode aceitar.

Veja também o [`MVP.md`](MVP.md) com o estado atual do MVP.

## 📝 License

Esse projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

<h4 align="center">
    Feito com 💚  por <a href="https://www.linkedin.com/in/pedroarfux/">Pedro Arfux</a> e <a href="https://www.linkedin.com/in/vitor-gabriel-de-souza-farias-564651196/">Vitor Gabriel</a>.
</h4>
