import os
import tempfile

# Configura o ambiente ANTES de importar a aplicação (database.py lê DATABASE_URL no import).
_tmpdir = tempfile.mkdtemp(prefix="stock-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmpdir}/test.db"
os.environ["SECRET_KEY"] = "chave-apenas-para-testes"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from database import Base, engine  # noqa: E402
from main import app  # noqa: E402

SENHA = "Stock@2026"


@pytest.fixture()
def client():
    # Banco limpo a cada teste (create_all só em banco temporário de teste;
    # as migrations são testadas em test_migrations.py)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c


def signup(client, nome, email, senha=SENHA, **extra):
    return client.post("/api/users", json={"nome": nome, "email": email, "senha": senha, **extra})


def login(client, email, senha=SENHA, **extra):
    r = client.post("/api/auth/login", json={"email": email, "senha": senha, **extra})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
