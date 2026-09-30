# STOCK — Estado do MVP

> Atualizado em 30/09/2026 — rodada 2, lotes A (segurança/dados) e B (migrations + UX) (branch `develop`). Avaliação feita rodando a aplicação localmente
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
| 4 | **Cadastrar produtos** | ✅ funciona | Menu → "Cadastrar Novo Item" (`pages/cadastroItem.html`): nome, categoria, **"Mínimo que quero ter"** e **"Tenho agora"** → `POST /api/stock/novo-item` cria o item e já o põe na dispensa numa transação só. **Catálogo por casa** (`item.cod_estoque`). Nome único por casa **ignorando acento, maiúsculas e espaços** ("Café 500g" = "cafe  500G"): coluna `item.nome_normalizado` + `UNIQUE(cod_estoque, nome_normalizado)`; duplicado → 409 "Já existe um item chamado … nesta casa". Editar nome/categoria e excluir: ver passo 6. **Falta:** unidade (kg, L, un). |
| 5 | **Adicionar itens à dispensa** (mínimo desejado + quantidade atual) | ✅ funciona | No cadastro (passo 4) ou, para item que já está no catálogo da casa, "Listar Itens" / "Buscar Itens" → "Adicionar" → `POST /api/stock`. Agora aceita quantidade atual **0** (item que acabou, vai direto para a lista). Item repetido → 409. |
| 6 | **Definir / alterar quantidades** | ✅ funciona | "Meu Estoque" (`pages/estoque.html`) em **cartões** (celular sem rolagem lateral): botões **−1 / +1** (48 px) → `POST /api/stock/{cod_item}/ajuste {delta}`, um `UPDATE … SET qtd = CASE …` **atômico** no banco que nunca fica abaixo de 0 (dois moradores ao mesmo tempo não perdem alterações). Selo "Abaixo do mínimo". "Editar" altera nome, categoria, mínimo e atual (`PUT /api/stock/{cod_item}`); "Excluir item" pede confirmação e remove da dispensa e do catálogo da casa (`DELETE`, 204). Estado vazio com "Cadastrar item" / "Adicionar do catálogo da casa". **Falta:** histórico. |
| 7 | **Lista de compras automática** (itens abaixo do mínimo) | ✅ funciona | "Lista de Compras" (`pages/listaCompras.html`, em **cartões** com selo "Faltam N", sem coluna de ID, estado vazio "Nada para comprar") → `GET /api/lista`: todo item com `qtd_desejada > qtd_estoque` aparece com `qtd_a_comprar = desejada − atual`. Testado: Leite (mín 6, atual 0) e Arroz (mín 2, atual 1) entraram; Café (mín 1, atual 2) não. A lista é **calculada na hora** (não é salva). |
| 8 | **Registrar a compra** | 🟡 parcial | Botão "Comprar" (44 px) → `POST /api/lista/comprar` soma a quantidade comprada ao estoque e o item sai da lista. **Falta:** marcar vários itens de uma vez / "comprei tudo", lista salva com check-off durante a ida ao mercado (tabelas `listacompra`/`listaitem` existem mas não são usadas). |
| 9 | **Compartilhar a dispensa com quem mora junto** | ✅ funciona | Menu → **"Casa e convites"** (`pages/usuarios.html`). O **dono** gera um código (`POST /api/estoque/convites`, `secrets.token_urlsafe`, **uso único, 7 dias**) e copia o código ou o link `…/pages/cadastroUsuario.html?convite=<código>`. A outra pessoa entra informando o código no **cadastro** ou, se já tem conta, **logada** em "Casa e convites": o código é **conferido antes** (`GET /api/estoque/convites/{código}`, não consome o convite) e aparece "Entrar em "Casa Teste" (de Ana Teste)?" para confirmar (`POST /api/estoque/entrar`). Quem já está logado e abre o link vai direto para "Casa e convites" com a casa já identificada; quem tem a casa vazia vê "Tenho um código de convite" no menu. **O login não aceita mais convite** (rodada 2: trocava o estoque sem aviso). O dono de um estoque com itens ou outros moradores é bloqueado (409, mensagem clara) e não vê a opção. Membros não geram convite (403). Reuso/código inválido → 400. **Falta:** listar/revogar convites, remover morador, sair do estoque, transferir o papel de dono. |

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
uv run alembic upgrade head                            # cria/atualiza as tabelas
uv run uvicorn main:app --host 0.0.0.0 --port 8000      # cria .venv e instala deps sozinho
# API: http://localhost:8000  |  Swagger: http://localhost:8000/docs

# frontend (outro terminal, a partir da raiz)
cd frontend
python3 -m http.server 3000 --bind 0.0.0.0
# App: http://localhost:3000
```

Contas de teste (banco de desenvolvimento): `cd backend && uv run alembic upgrade head && uv run python seed_dev.py` cria
`ana.teste@exemplo.com.br` (dona de "Casa Teste", 4 itens, Leite abaixo do mínimo), `beto.teste@exemplo.com.br`
(morador da mesma casa) e `carla.teste@exemplo.com.br` (outra casa), todos com a senha `Stock@2026`.

Testes automatizados: `cd backend && uv run pytest`.

Sem uv: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/alembic upgrade head && .venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000` dentro de `backend/`.

Em segundo plano (como está rodando nesta máquina, logs em `/workspace/stock-logs/`):

```bash
cd backend  && setsid nohup uv run uvicorn main:app --host 0.0.0.0 --port 8000 > /workspace/stock-logs/backend.log 2>&1 < /dev/null &
cd frontend && setsid nohup python3 -m http.server 3000 --bind 0.0.0.0 > /workspace/stock-logs/frontend.log 2>&1 < /dev/null &
```

Observações:
- Abrindo o frontend na porta 3000, o `js/api.js` chama `http://<mesmo host>:8000/api`. O CORS do backend libera
  `http://localhost:3000` e `http://127.0.0.1:3000`; para acessar por outro endereço (ex.: IP da rede) defina
  `CORS_ORIGINS=http://192.168.0.10:3000` no `backend/.env`.
- **`SECRET_KEY` é obrigatória**: sem ela, com o valor de exemplo ou com menos de 16 caracteres o backend não sobe.
- **Migrations com Alembic** (`backend/migrations/`, `render_as_batch=True`, funciona em SQLite e Postgres). A API
  **não cria mais tabelas ao subir**: antes do primeiro `uvicorn` (e sempre que atualizar o código) rode
  `cd backend && uv run alembic upgrade head`. O Docker roda isso sozinho ao iniciar o backend.
  - `0001` — schema inicial, idêntico ao commit `1be9a89` (fim do lote A).
  - `0002` — `item.nome_normalizado` (sem acento/maiúsculas/espaços repetidos, calculado em Python), preenchida para os
    itens existentes, e `UNIQUE(cod_estoque, nome_normalizado)`. Se já houver duplicados, fica o mais antigo; o mais
    novo é excluído se não estiver em nenhuma dispensa, ou renomeado com sufixo " (2)", " (3)"… se estiver.
  - Banco criado antes do Alembic (até `1be9a89`): `uv run alembic stamp 0001 && uv run alembic upgrade head`
    (faça cópia do `.db` antes). Nova mudança de schema: altere `models.py`,
    `uv run alembic revision --autogenerate -m "..."`, revise o arquivo e rode `upgrade head`.
  - Testes: os da API usam `create_all` num banco SQLite temporário; `tests/test_migrations.py` roda as migrations num
    banco temporário e confere que `upgrade head` bate com `models.py`, que o `downgrade` funciona e que a 0002 resolve
    duplicados.
  - Conferido também em **PostgreSQL 17** local: `upgrade head` sem diferença para `models.py`, duplicados
    resolvidos pela 0002, `UNIQUE` ativo e `downgrade base` ok.
- **Docker Compose** (`docker compose up -d --build`, Postgres) continua disponível para quem tem Docker funcional.
  Nesta máquina o Docker foi instalado e o daemon subiu, mas a rede entre containers não funcionou (o backend não
  alcança o Postgres: timeout TCP; regras de firewall `iptables-legacy` do host com `FORWARD DROP`). Por isso foi usado
  o caminho SQLite + uv.
- Admin (páginas "DEV" do menu) só existe se promovido direto no banco:
  `sqlite3 backend/stock.db "UPDATE usuario SET permissao='admin' WHERE email='...';"`. Não é necessário para o MVP.
- O validador de e-mail recusa domínios reservados (`@teste.test`, `@x.local`); use algo como `@exemplo.com.br` nos testes.

## 3. O que falta para o MVP (priorizado)

**P0 — necessário antes de alguém usar de verdade**
1. ~~Migrations (Alembic)~~ — **feito na rodada 2, lote B** (0001 + 0002).
2. ~~Catálogo por estoque~~ — **feito na rodada 2** (`item.cod_estoque`, sem duplicados por casa).
3. ~~`SECRET_KEY` obrigatória~~ — **feito na rodada 2** (backend não sobe sem chave forte).
4. ~~Remover / editar item da dispensa~~ — **feito no lote B**.
5. ~~Ajuste relativo de quantidade atômico (+1/−1)~~ — **feito no lote B**.

**P1 — completa a experiência do MVP**
6. **Gestão de membros**: listar/revogar convites, remover membro, sair do estoque, transferir dono. Hoje, se o dono
   entra em outro estoque com convite, o estoque antigo fica sem ninguém que possa convidar.
7. **Lista de compras salva** com check-off durante a compra e "comprei tudo" (usar ou remover `ListaCompra`/`ListaItem`).
8. **Unidades e decimais** (kg, L, un; 0,5 kg) — hoje só inteiros sem unidade.
9. **UX** — feito no lote B: mensagens de validação em português (por campo), sem IDs técnicos, cartões no celular,
   textos sem CAIXA ALTA e sem itens "DEV" no menu. **Falta:** confirmação/desfazer ao comprar, páginas de admin ainda
   abertas por URL (a API exige admin), testes do frontend.
10. **Segurança de conta**: limite de tentativas de login, recuperação de senha.

**P2 — depois do MVP**
11. Histórico de movimentações (entradas/saídas) e sugestões de mínimo.
12. CI rodando `uv run pytest` (os testes da API já existem: 20).
13. Deploy (URL de API por configuração, Bootstrap local em vez de CDN, JWT em cookie `httpOnly`).
14. Limpar legado: páginas "DEV"/admin, `permissao` global, fallback de senha SHA1, `tcc.sql`.

**Proposta de refatoração do modelo de dados (não feita nesta rodada):**
`usuario_estoque (cod_usuario, cod_estoque, papel: dono|membro)` no lugar de `usuario.cod_estoque` (permite mais de uma
dispensa e remove a necessidade de `cod_dono`); `item.unidade`; quantidades `Numeric`; tabela
`movimentacao` (histórico); `listacompra`/`listaitem` usadas de verdade para a lista salva. Tudo via Alembic.

## 4. Bugs e riscos conhecidos

- ~~Catálogo global~~ e ~~`SECRET_KEY` padrão~~: corrigidos na rodada 2.
- ~~Login com convite trocava o estoque sem aviso e deixava o do usuário órfão~~: corrigido na rodada 2 (convite só
  logado, com confirmação e bloqueio para dono com itens/moradores). O dono de um estoque **vazio** ainda pode aceitar
  um convite; o estoque vazio fica para trás no banco (sem impacto para o usuário).
- **XSS**: 6 páginas montavam tabelas com `innerHTML` usando dados da API (nome de usuário, descrição de item) —
  **corrigido nesta rodada** com `esc()` (`frontend/js/api.js`); o risco volta se novas telas usarem `innerHTML` sem escape.
- **Convites**: código de uso único e com validade, mas não pode ser revogado; quem tem o código antes do convidado entra no lugar dele.
- "Editar" em Meu Estoque (`PUT`) ainda grava valor absoluto; os botões −1/+1 são atômicos.
- `POST /api/stock` exige mínimo desejado > 0.
- Tabelas `listacompra`/`listaitem` criadas mas não usadas.
- Token JWT no `localStorage` (vulnerável se houver XSS) e sem revogação no logout.
- Sem limite de tentativas de login; fallback de senha SHA1 legado em `backend/auth.py`.
- CORS só para `localhost:3000`/`127.0.0.1:3000` por padrão (outros endereços precisam de `CORS_ORIGINS`).
- Bootstrap vem de CDN: sem internet as telas ficam sem estilo.
- A tela "SAC" (`pages/contato.html`) não envia nada para o backend.
- Testes automatizados cobrem só a API e as migrations (`backend/tests/`, 20 testes), não o frontend.
- Páginas de admin (antigas "DEV") saíram do menu mas ainda abrem por URL (a API recusa quem não é admin).

## 5. Mudanças feitas nesta rodada (branch `develop`)

- Rodar sem Docker: SQLite via `DATABASE_URL`, `backend/pyproject.toml` + `uv.lock` (`uv run`), frontend :3000 → API :8000,
  CORS configurável, README corrigido (branch `refactor/python-fastapi` não existe).
- Dono do estoque + convites de uso único; cadastro público não aceita mais `cod_estoque`/`permissao`.
- Senha mínima de 8; qualquer usuário logado cadastra itens; quantidade atual 0 permitida.
- Login com senha errada mostra o erro; login automático após cadastro.
- Escape de HTML nas 6 telas com `innerHTML`.

Rodada 2 — lote A (segurança/dados):
- Smoke test da API com pytest (`uv run pytest`), estendido a cada mudança.
- Convite removido do login; aceitar só logado, com confirmação e bloqueio do dono com itens/moradores; opção
  escondida para quem não pode trocar; "Voltar ao Login" mantém o convite.
- Catálogo de itens por casa, sem duplicados.
- `SECRET_KEY` obrigatória.
- `backend/seed_dev.py` com contas de teste; banco de desenvolvimento recriado.

Rodada 2 — lote B (migrations + UX):
- Alembic (0001 = schema do lote A; banco de desenvolvimento marcado com `stamp 0001`, dados preservados) e 0002
  (nome normalizado único por casa; no banco de desenvolvimento o item duplicado "Cafe 500g" da Casa Teste, que não
  estava em nenhuma dispensa, foi excluído, ficando "Café 500g"). A API não roda mais `create_all`.
- Erros em português: 409 de nome duplicado, validação por campo (`erros: [{campo, mensagem}]`), falha de rede.
- Cadastro de item com "Mínimo que quero ter" / "Tenho agora" em um passo (`POST /api/stock/novo-item`).
- Meu Estoque em cartões: −1/+1 atômico, editar nome/categoria/quantidades, excluir com confirmação, estado vazio.
- Lista de compras em cartões ("Faltam N", botão "Comprar" de 44 px, estado vazio).
- Textos: menu sem itens "DEV", sem CAIXA ALTA, sem colunas de ID, "Bem-vindo ao STOCK!".
- Convite: conferência antes de aceitar (`GET /api/estoque/convites/{código}`), link aberto já logado vai para
  "Casa e convites", botão "Tenho um código de convite" para quem tem a casa vazia.
