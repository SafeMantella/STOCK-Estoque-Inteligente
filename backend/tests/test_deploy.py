"""Frontend servido pelo próprio FastAPI (mesma origem) e health check."""


import pytest

VARIAVEIS_COMMIT = ("GIT_COMMIT", "RENDER_GIT_COMMIT", "RAILWAY_GIT_COMMIT_SHA", "SOURCE_COMMIT")


@pytest.fixture
def sem_commit(monkeypatch):
    for nome in VARIAVEIS_COMMIT:
        monkeypatch.delenv(nome, raising=False)
    return monkeypatch


def test_health(client, sem_commit):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "banco": "ok", "commit": "desconhecido"}


@pytest.mark.parametrize("nome", VARIAVEIS_COMMIT)
def test_health_commit_de_cada_variavel(client, sem_commit, nome):
    sem_commit.setenv(nome, "abc1234")
    assert client.get("/api/health").json()["commit"] == "abc1234"


def test_health_commit_ordem_e_vazio(client, sem_commit):
    # GIT_COMMIT (build arg) tem prioridade sobre as variáveis dos hosts
    sem_commit.setenv("GIT_COMMIT", "beeed26")
    sem_commit.setenv("RENDER_GIT_COMMIT", "render0")
    sem_commit.setenv("SOURCE_COMMIT", "coolify0")
    assert client.get("/api/health").json()["commit"] == "beeed26"
    # Vazio (ARG do Dockerfile sem --build-arg) conta como não definido: vale a do host
    sem_commit.setenv("GIT_COMMIT", "")
    assert client.get("/api/health").json()["commit"] == "render0"
    sem_commit.delenv("RENDER_GIT_COMMIT")
    assert client.get("/api/health").json()["commit"] == "coolify0"


def test_frontend_na_mesma_origem(client):
    r = client.get("/")
    assert r.status_code == 200 and "text/html" in r.headers["content-type"]
    assert "STOCK" in r.text
    for caminho in ("/menu.html", "/pages/estoque.html", "/js/api.js"):
        assert client.get(caminho).status_code == 200, caminho
    # A API continua em /api e tem prioridade sobre os arquivos estáticos
    assert client.get("/api/stock").status_code == 401
    assert client.get("/docs").status_code == 200


def test_frontend_nao_expoe_arquivos_internos(client):
    assert client.get("/CLAUDE.md").status_code == 404
    assert client.get("/nao-existe.html").status_code == 404
    assert client.get("/../backend/.env").status_code == 404


def test_health_banco_indisponivel(client):
    from sqlalchemy.exc import OperationalError

    from database import get_db
    from main import app

    class BancoFora:
        def execute(self, *a, **k):
            raise OperationalError("SELECT 1", {}, Exception("conexão recusada"))

    app.dependency_overrides[get_db] = lambda: BancoFora()
    try:
        r = client.get("/api/health")
    finally:
        app.dependency_overrides.clear()
    assert r.status_code == 503 and r.json()["status"] == "erro"
    assert "commit" in r.json()
