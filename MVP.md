# STOCK — Estado do MVP (rodada 1)

> Atualizado em 30/09/2026 (branch `develop`). Avaliação feita rodando a aplicação localmente
> (backend FastAPI + SQLite em `:8000`, frontend estático em `:3000`), com chamadas `curl` na API
> e um teste de ponta a ponta no navegador (Chrome headless) percorrendo todas as telas abaixo.

**Produto:** gerenciador de estoque **doméstico** (a dispensa da casa). A pessoa registra o que tem em casa
e a quantidade mínima que quer manter; o sistema **gera a lista de compras automaticamente** com tudo que
está abaixo do mínimo, e quem mora junto compartilha o mesmo estoque.

## 1. Fluxo mínimo do MVP

| # | Passo | Status | Evidência |
|---|-------|--------|-----------|
| 1 | **Criar conta** | ✅ funciona | Tela `pages/cadastroUsuario.html` → `POST /api/users`. Senha mínima de 8 caracteres (validada no navegador e na API: 422). Após o cadastro o usuário já entra logado. |
| 2 | **Login / logout** | ✅ funciona | `index.html` → `POST /api/auth/login` (JWT, 8 h, guardado no `localStorage`); "Sair" em `menu.html` limpa a sessão. Senha errada mostra "Email ou senha incorretos" (antes a página só recarregava). |
| 3 | **Criar a dispensa (estoque)** | 🟡 parcial | Criada automaticamente no cadastro (campo opcional "Nome do seu estoque"; padrão "Estoque de <nome>") e o usuário vira **dono** (`estoque.cod_dono`). `GET /api/estoque/meu` mostra nome, dono e nº de membros (exibido no menu). **Falta:** renomear, ter mais de uma dispensa por pessoa. `POST /api/estoque` é só para admin (tela "DEV"). |
| 4 | **Cadastrar produtos** | 🟡 parcial | Menu → "Cadastrar Novo Item" (`pages/cadastroItem.html`) → `POST /api/items`. Liberado para qualquer usuário logado nesta rodada (antes exigia admin e **não existia forma de criar admin**, então o catálogo ficava sempre vazio). **Problemas:** catálogo é **global** (todas as casas veem os itens de todas), aceita duplicados, não dá para editar/excluir, não tem unidade (kg, L, un). |
| 5 | **Adicionar itens à dispensa** (mínimo desejado + quantidade atual) | ✅ funciona | "Listar Itens" / "Buscar Itens" → botão "Adicionar" → `POST /api/stock`. Agora aceita quantidade atual **0** (item que acabou, vai direto para a lista). Item repetido → 409. |
| 6 | **Definir / alterar quantidades** | 🟡 parcial | "Meu Estoque" (`pages/estoque.html`) → `PUT /api/stock/{cod_item}` altera mínimo e atual. **Falta:** botões "+1 / −1 (consumi)", remover item da dispensa (não existe `DELETE`), histórico. O `PUT` grava valor absoluto: se duas pessoas editam ao mesmo tempo, a última sobrescreve. |
| 7 | **Lista de compras automática** (itens abaixo do mínimo) | ✅ funciona | "Lista de Compras" (`pages/listaCompras.html`) → `GET /api/lista`: todo item com `qtd_desejada > qtd_estoque` aparece com `qtd_a_comprar = desejada − atual`. Testado: Leite (mín 6, atual 0) e Arroz (mín 2, atual 1) entraram; Café (mín 1, atual 2) não. A lista é **calculada na hora** (não é salva). |
| 8 | **Registrar a compra** | 🟡 parcial | Botão "Comprar" → `POST /api/lista/comprar` soma a quantidade comprada ao estoque e o item sai da lista. **Falta:** marcar vários itens de uma vez / "comprei tudo", lista salva com check-off durante a ida ao mercado (tabelas `listacompra`/`listaitem` existem mas não são usadas). |
| 9 | **Compartilhar a dispensa com quem mora junto** | ✅ funciona (novo) | Menu → "Usuários em seu estoque / Convidar" (`pages/usuarios.html`). O **dono** gera um código (`POST /api/estoque/convites`, `secrets.token_urlsafe`, **uso único, 7 dias**) e copia o código ou o link `…/pages/cadastroUsuario.html?convite=<código>`. A outra pessoa entra informando o código no **cadastro**, no **login** (campo opcional) ou nessa mesma tela (`POST /api/estoque/entrar`). Membros não veem o botão de convite (403 na API). Reuso/código inválido → 400. **Falta:** listar/revogar convites, remover membro, sair do estoque, transferir o papel de dono. |

**Antes desta rodada** o passo 9 era feito digitando o `cod_estoque` (número sequencial) no cadastro público — qualquer pessoa entrava na dispensa de qualquer outra. Isso foi removido: o cadastro público **sempre cria um estoque novo**.

## 2. Como rodar localmente

Caminho usado nesta máquina (**sem Docker**; ver observação sobre Docker abaixo):

```bash
git clone https://github.com/SafeMantella/STOCK-Estoque-Inteligente.git
cd STOCK-Estoque-Inteligente
git checkout develop

# backend (SQLite + uv)
cp backend/.env.example backend/.env
# edite backend/.env:
#   DATABASE_URL=sqlite:///./stock.db
#   SECRET_KEY=<saída de: python3 -c "import secrets; print(secrets.token_hex(32))">
cd backend
uv run uvicorn main:app --host 0.0.0.0 --port 8000      # cria .venv e instala deps sozinho
# API: http://localhost:8000  |  Swagger: http://localhost:8000/docs

# frontend (outro terminal, a partir da raiz)
cd frontend
python3 -m http.server 3000 --bind 0.0.0.0
# App: http://localhost:3000
```

Sem uv: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000` dentro de `backend/`.

Em segundo plano (como está rodando nesta máquina, logs em `/workspace/stock-logs/`):

```bash
cd backend  && setsid nohup uv run uvicorn main:app --host 0.0.0.0 --port 8000 > /workspace/stock-logs/backend.log 2>&1 < /dev/null &
cd frontend && setsid nohup python3 -m http.server 3000 --bind 0.0.0.0 > /workspace/stock-logs/frontend.log 2>&1 < /dev/null &
```

Observações:
- Abrindo o frontend na porta 3000, o `js/api.js` chama `http://<mesmo host>:8000/api`. O CORS do backend libera
  `http://localhost:3000` e `http://127.0.0.1:3000`; para acessar por outro endereço (ex.: IP da rede) defina
  `CORS_ORIGINS=http://192.168.0.10:3000` no `backend/.env`.
- Não há migrations: se já existia um banco de versão anterior, apague-o (`rm backend/stock.db`) — as tabelas novas
  (`convite_estoque`, coluna `estoque.cod_dono`) só são criadas em banco novo.
- **Docker Compose** (`docker compose up -d --build`, Postgres) continua disponível para quem tem Docker funcional.
  Nesta máquina o Docker foi instalado e o daemon subiu, mas a rede entre containers não funcionou (o backend não
  alcança o Postgres: timeout TCP; regras de firewall `iptables-legacy` do host com `FORWARD DROP`). Por isso foi usado
  o caminho SQLite + uv.
- Admin (páginas "DEV" do menu) só existe se promovido direto no banco:
  `sqlite3 backend/stock.db "UPDATE usuario SET permissao='admin' WHERE email='...';"`. Não é necessário para o MVP.
- O validador de e-mail recusa domínios reservados (`@teste.test`, `@x.local`); use algo como `@exemplo.com.br` nos testes.

## 3. O que falta para o MVP (priorizado)

**P0 — necessário antes de alguém usar de verdade**
1. **Migrations (Alembic)** no lugar de `create_all`: esta rodada já mudou o schema; um Postgres existente não recebe
   `estoque.cod_dono` nem `convite_estoque` e quebra.
2. **Catálogo por estoque**: adicionar `cod_estoque` em `item` (hoje uma casa vê os produtos cadastrados por todas as
   outras) e evitar duplicados; idealmente "cadastrar produto e já adicionar à dispensa" em um passo só.
3. **`SECRET_KEY` obrigatória**: hoje, sem `.env`, o backend usa `change-me-in-production` (`backend/auth.py`) e o
   compose usa `troque-esta-chave-em-producao` → qualquer um forja tokens. Deve falhar ao subir sem chave.
4. **Remover / editar item da dispensa** (`DELETE /api/stock/{cod_item}`, editar nome/categoria).
5. **Ajuste relativo de quantidade** (`+1`, `−1 consumi`) feito no banco de forma atômica, em vez de sobrescrever o
   valor absoluto (evita perder alterações de dois moradores ao mesmo tempo).

**P1 — completa a experiência do MVP**
6. **Gestão de membros**: listar/revogar convites, remover membro, sair do estoque, transferir dono. Hoje, se o dono
   entra em outro estoque com convite, o estoque antigo fica sem ninguém que possa convidar.
7. **Lista de compras salva** com check-off durante a compra e "comprei tudo" (usar ou remover `ListaCompra`/`ListaItem`).
8. **Unidades e decimais** (kg, L, un; 0,5 kg) — hoje só inteiros sem unidade.
9. **UX**: mensagens de validação em português (hoje vêm do Pydantic em inglês, ex.: "String should have at least 8
   characters"), esconder IDs técnicos nas tabelas, layout de celular (tabelas largas), confirmação ao comprar.
10. **Segurança de conta**: limite de tentativas de login, recuperação de senha.

**P2 — depois do MVP**
11. Histórico de movimentações (entradas/saídas) e sugestões de mínimo.
12. Testes automatizados (API) e CI.
13. Deploy (URL de API por configuração, Bootstrap local em vez de CDN, JWT em cookie `httpOnly`).
14. Limpar legado: páginas "DEV"/admin, `permissao` global, fallback de senha SHA1, `tcc.sql`.

**Proposta de refatoração do modelo de dados (não feita nesta rodada):**
`usuario_estoque (cod_usuario, cod_estoque, papel: dono|membro)` no lugar de `usuario.cod_estoque` (permite mais de uma
dispensa e remove a necessidade de `cod_dono`); `item.cod_estoque` + `unidade`; quantidades `Numeric`; tabela
`movimentacao` (histórico); `listacompra`/`listaitem` usadas de verdade para a lista salva. Tudo via Alembic.

## 4. Bugs e riscos conhecidos

- **Catálogo global** (`item` sem `cod_estoque`): vazamento de dados entre casas e duplicados; qualquer usuário logado
  pode cadastrar itens que aparecem para todos.
- **`SECRET_KEY` padrão** (ver P0.3).
- **Sem migrations** (ver P0.1).
- **XSS**: 6 páginas montavam tabelas com `innerHTML` usando dados da API (nome de usuário, descrição de item) —
  **corrigido nesta rodada** com `esc()` (`frontend/js/api.js`); o risco volta se novas telas usarem `innerHTML` sem escape.
- **Convites**: código de uso único e com validade, mas não pode ser revogado; quem tem o código antes do convidado entra no lugar dele.
- **Dono que troca de estoque** deixa o estoque antigo órfão (ninguém mais pode convidar).
- `PUT /api/stock` sobrescreve valor absoluto (condição de corrida entre moradores).
- `POST /api/stock` exige mínimo desejado > 0.
- Tabelas `listacompra`/`listaitem` criadas mas não usadas.
- Token JWT no `localStorage` (vulnerável se houver XSS) e sem revogação no logout.
- Sem limite de tentativas de login; fallback de senha SHA1 legado em `backend/auth.py`.
- CORS só para `localhost:3000`/`127.0.0.1:3000` por padrão (outros endereços precisam de `CORS_ORIGINS`).
- Bootstrap vem de CDN: sem internet as telas ficam sem estilo.
- A tela "SAC" (`pages/contato.html`) não envia nada para o backend.
- Sem testes automatizados.

## 5. Mudanças feitas nesta rodada (branch `develop`)

- Rodar sem Docker: SQLite via `DATABASE_URL`, `backend/pyproject.toml` + `uv.lock` (`uv run`), frontend :3000 → API :8000,
  CORS configurável, README corrigido (branch `refactor/python-fastapi` não existe).
- Dono do estoque + convites de uso único; cadastro público não aceita mais `cod_estoque`/`permissao`.
- Senha mínima de 8; qualquer usuário logado cadastra itens; quantidade atual 0 permitida.
- Login com senha errada mostra o erro; login automático após cadastro.
- Escape de HTML nas 6 telas com `innerHTML`.
