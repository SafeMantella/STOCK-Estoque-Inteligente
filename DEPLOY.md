# STOCK — Como publicar (deploy)

Guia genérico, sem host escolhido ainda. A aplicação é **uma imagem Docker só** (`Dockerfile` na raiz):
o FastAPI serve o frontend em `/` e a API em `/api`, na **mesma origem** (sem CORS, sem segundo serviço).
Precisa de um **PostgreSQL gerenciado** e de **HTTPS** (os hosts abaixo dão HTTPS no domínio deles).

> Nenhuma conta foi criada e nada foi publicado. Os passos por host são um roteiro; confira a documentação
> atual do host escolhido antes de seguir (nomes de menus e opções mudam).

## 1. Variáveis de ambiente

| Variável | Obrigatória | O que é |
|---|---|---|
| `DATABASE_URL` | **sim** | URL do Postgres gerenciado. `postgres://…` (formato de vários hosts) é aceito e convertido para `postgresql://…`. |
| `SECRET_KEY` | **sim** | Chave dos tokens de login (JWT). Mínimo 16 caracteres; gere com `python3 -c "import secrets; print(secrets.token_hex(32))"`. Sem ela a app não sobe. Trocar a chave desloga todo mundo. |
| `TRUST_PROXY` | recomendada | Número de proxies do host na frente da app (quase sempre `1`). Sem isso, o limite de tentativas vê o IP do proxy e **todo mundo divide o mesmo limite**. Ver seção 5. |
| `PORT` | não | Porta em que a app escuta (padrão `8000`). Render/Railway/Heroku definem sozinhos; a app respeita. |
| `CORS_ORIGINS` | não | Só se o frontend estiver em **outra** origem. Com a imagem única não é preciso (pode deixar vazio: `CORS_ORIGINS=`). |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | não | Validade do login, padrão `480` (8 h). |
| `RATE_LIMIT_EMAIL` / `RATE_LIMIT_IP` / `RATE_LIMIT_JANELA` | não | Limite de tentativas erradas: padrão 5 por e-mail e 20 por IP a cada 60 s (seção 5). |
| `WEB_CONCURRENCY` | não | Processos do uvicorn, padrão `1`. **Mantenha 1** enquanto o limite de tentativas for em memória. |
| `STOCK_ENV` | — | **Nunca** `dev` em produção (libera o `seed_dev.py` com contas de teste). |

## 2. Comando de início

A imagem já roda isto ao iniciar (`CMD ["sh", "start.sh"]`):

```sh
cd backend && sh start.sh
# = alembic upgrade head  &&  uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WEB_CONCURRENCY:-1}
```

- `alembic upgrade head` aplica as migrations pendentes a cada deploy (sem efeito se já estiver em dia).
- Host **sem Docker** (buildpack Python): comando de build `pip install uv && cd backend && uv sync --frozen --no-dev`
  e comando de início `cd backend && uv run --no-dev sh start.sh`.
- Health check do host: **`GET /api/health`** → `200 {"status":"ok","banco":"ok"}`; `503` se o banco não responde.

### Produção começa VAZIA

Em produção roda **só** `alembic upgrade head`. **Nunca rode `seed_dev.py`** (cria contas de teste com senha
pública): ele se recusa a rodar sem `STOCK_ENV=dev` e nem vai para a imagem Docker. A primeira conta é criada
pela própria tela "Cadastre-se", e os moradores entram por convite.

Testar a imagem localmente:

```bash
docker build -t stock .
docker run --rm -p 8000:8000 -e DATABASE_URL=postgres://usuario:senha@host:5432/banco \
  -e SECRET_KEY=<chave> -e TRUST_PROXY=0 stock
# abra http://localhost:8000  (health: http://localhost:8000/api/health)
```

Ou com Postgres junto: `docker compose up -d --build` (definir `SECRET_KEY` num `.env` na raiz).

## 3. Passos genéricos por host

Em todos: (1) criar o Postgres gerenciado, (2) criar o serviço web a partir do repositório (branch escolhida)
usando o `Dockerfile` da raiz, (3) definir `DATABASE_URL`, `SECRET_KEY` e `TRUST_PROXY=1`, (4) health check em
`/api/health`, (5) fazer o deploy e abrir a URL `https://…` do host, (6) criar a primeira conta pela tela de cadastro.

**Render**
1. Criar um PostgreSQL no painel; copiar a *Internal Database URL*.
2. *New → Web Service* a partir do repositório; runtime **Docker** (usa o `Dockerfile` da raiz).
3. Variáveis: `DATABASE_URL` (a URL interna), `SECRET_KEY`, `TRUST_PROXY=1`. `PORT` é definido pelo Render.
4. *Health Check Path*: `/api/health`.

**Railway**
1. Novo projeto a partir do repositório (o `Dockerfile` da raiz é detectado).
2. Adicionar um serviço PostgreSQL no mesmo projeto.
3. No serviço da app: `DATABASE_URL` referenciando a variável do Postgres (ex.: `${{Postgres.DATABASE_URL}}`),
   `SECRET_KEY`, `TRUST_PROXY=1`. `PORT` é definido pelo Railway.
4. Gerar um domínio público para o serviço; health check em `/api/health`.

**Fly.io**
1. `fly launch --no-deploy` na raiz (detecta o `Dockerfile`); no `fly.toml`, `internal_port = 8000`
   e um health check HTTP em `/api/health`.
2. Criar o Postgres gerenciado do Fly (ou outro Postgres externo) e obter a URL.
3. `fly secrets set DATABASE_URL=… SECRET_KEY=… TRUST_PROXY=1`
4. `fly deploy`. Manter **uma** máquina (limite de tentativas em memória).

**Outro host / VPS com Docker**: rodar a imagem atrás de um proxy com HTTPS (Caddy, Nginx, Traefik) e
`TRUST_PROXY=1`; Postgres gerenciado ou num container com volume e backup (seção 4).

## 4. Backup diário do Postgres

1. **Preferido: backup gerenciado do host.** Verifique se o plano do Postgres escolhido inclui backup diário
   automático (e restauração para um ponto no tempo), por quantos dias ele guarda e como restaurar. Faça uma
   restauração de teste uma vez, num banco separado, antes de depender dele.
2. **Se o host não fizer backup**, um `pg_dump` diário numa máquina com cron (ou job agendado do host), com a
   cópia guardada **fora** do host do banco:

   ```cron
   # todo dia às 03:00, guarda 14 dias
   0 3 * * * pg_dump --format=custom --no-owner --dbname="$DATABASE_URL" --file="/backups/stock-$(date +\%F).dump" && find /backups -name 'stock-*.dump' -mtime +14 -delete
   ```

   Restaurar (num banco vazio): `pg_restore --no-owner --clean --if-exists --dbname="$DATABASE_URL" /backups/stock-AAAA-MM-DD.dump`.
   Use um `pg_dump` da mesma versão principal do servidor ou mais nova (ex.: 17).

## 5. Limite de tentativas (login e convites)

- Tentativas **erradas** por minuto: **5 por e-mail** e **20 por IP** (a casa inteira costuma estar no mesmo
  Wi-Fi/IP; um morador errando a senha não trava os outros). Configurável com `RATE_LIMIT_EMAIL`,
  `RATE_LIMIT_IP` e `RATE_LIMIT_JANELA` (segundos, padrão 60). Vale para `POST /api/auth/login`,
  na consulta/aceite de convite e no cadastro com código de convite. Passou disso: `429` com
  "Muitas tentativas. Tente de novo em 1 minuto." e `Retry-After`.
- Fica **em memória**: zera quando a app reinicia (inclusive a cada deploy) e vale para **uma instância**.
  Com mais de uma instância/processo cada um conta separado (o limite efetivo multiplica). Para escalar,
  trocar por um armazenamento compartilhado (ex.: Redis).
- IP do cliente: por padrão o IP da conexão. Atrás do proxy do host defina `TRUST_PROXY=1` para usar o
  `X-Forwarded-For` (o último IP da lista, colocado pelo proxy; o começo da lista pode ser forjado pelo cliente).
  Se houver mais de um proxy na frente (ex.: CDN + balanceador), use o número de proxies (`TRUST_PROXY=2`).
  **Não** defina `TRUST_PROXY` se a app estiver exposta direto, sem proxy (o cliente poderia forjar o IP).

## 6. Checklist antes de chamar os moradores

- [ ] URL com **HTTPS** abrindo a tela de login; `/api/health` = 200.
- [ ] `SECRET_KEY` gerada só para produção (diferente da de desenvolvimento) e guardada num gerenciador de senhas.
- [ ] Banco vazio no início (nenhuma conta de teste).
- [ ] Backup diário confirmado e uma restauração de teste feita.
- [ ] `TRUST_PROXY` conferido: 6 senhas erradas seguidas no mesmo e-mail bloqueiam só esse e-mail; com mais de
  20 erros de e-mails diferentes, só o IP de quem errou fica bloqueado, não o de outro celular (outra rede).
- [ ] Criar a conta, cadastrar alguns itens, gerar o convite e o morador entrar pelo celular.
