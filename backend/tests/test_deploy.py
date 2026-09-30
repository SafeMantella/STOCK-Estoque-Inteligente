"""Frontend servido pelo próprio FastAPI (mesma origem) e health check."""


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json() == {"status": "ok", "banco": "ok"}


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
