"""E-mail sem diferenciar maiúsculas/minúsculas nem espaços nas pontas (cadastro e login)."""
from conftest import SENHA, signup


def _login(client, email, senha=SENHA):
    return client.post("/api/auth/login", json={"email": email, "senha": senha})


def test_cadastro_com_maiusculas_salva_minusculas_e_login_em_minusculas(client):
    r = signup(client, "Beto", "Beto.Silva@Gmail.com")
    assert r.status_code == 201, r.text
    assert r.json()["email"] == "beto.silva@gmail.com"
    assert _login(client, "beto.silva@gmail.com").status_code == 200
    assert _login(client, "BETO.SILVA@GMAIL.COM").status_code == 200


def test_segundo_cadastro_com_outra_caixa_e_duplicado(client):
    assert signup(client, "Beto", "Beto.Silva@Gmail.com").status_code == 201
    r = signup(client, "Beto 2", "beto.silva@gmail.com")
    assert r.status_code == 400 and r.json()["detail"] == "Email já cadastrado"
    r = signup(client, "Beto 3", "  BETO.Silva@gmail.COM ")
    assert r.status_code == 400 and r.json()["detail"] == "Email já cadastrado"


def test_login_com_espacos_nas_pontas(client):
    assert signup(client, "Ana", " ana@exemplo.com.br ").status_code == 201
    assert _login(client, "  ana@exemplo.com.br  ").status_code == 200
    assert _login(client, "\tAna@Exemplo.com.br\n").status_code == 200


def test_conta_antiga_com_maiusculas_no_banco_ainda_entra(client):
    """Linhas gravadas antes da correção (local-part com maiúsculas) continuam entrando
    e continuam bloqueando cadastro duplicado (comparação com lower(email) no banco)."""
    from database import SessionLocal
    from models import Usuario

    assert signup(client, "Carla", "carla@exemplo.com.br").status_code == 201
    db = SessionLocal()
    try:
        u = db.query(Usuario).filter(Usuario.email == "carla@exemplo.com.br").one()
        u.email = "Carla.Antiga@Exemplo.com.br"
        db.commit()
    finally:
        db.close()
    assert _login(client, "carla.antiga@exemplo.com.br").status_code == 200
    r = signup(client, "Carla 2", "CARLA.ANTIGA@exemplo.com.br")
    assert r.status_code == 400 and r.json()["detail"] == "Email já cadastrado"


def test_senha_errada_continua_401(client):
    assert signup(client, "Dani", "Dani@Exemplo.com.br").status_code == 201
    r = _login(client, "dani@exemplo.com.br", senha="errada-123")
    assert r.status_code == 401
