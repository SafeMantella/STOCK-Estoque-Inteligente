"""Limite de tentativas erradas: login e códigos de convite (5 por minuto por IP e por e-mail)."""
from conftest import SENHA, login, signup

from limite import Limitador


def _login(client, email, senha="errada-123", ip=None):
    headers = {"X-Forwarded-For": ip} if ip else {}
    return client.post("/api/auth/login", json={"email": email, "senha": senha}, headers=headers)


def _convite(client, h):
    return client.post("/api/estoque/convites", headers=h).json()["codigo"]


def test_login_bloqueia_na_sexta_tentativa_errada(client):
    signup(client, "Ana", "ana@exemplo.com.br")
    for _ in range(5):
        assert _login(client, "ana@exemplo.com.br").status_code == 401
    r = _login(client, "ana@exemplo.com.br", senha=SENHA)  # nem a senha certa passa enquanto bloqueado
    assert r.status_code == 429
    assert r.json()["detail"] == "Muitas tentativas. Tente de novo em 1 minuto."
    assert 1 <= int(r.headers["Retry-After"]) <= 60


def test_tentativas_certas_nao_contam(client):
    signup(client, "Ana", "ana@exemplo.com.br")
    for _ in range(8):
        assert _login(client, "ana@exemplo.com.br", senha=SENHA).status_code == 200


def test_limite_por_ip_mesmo_trocando_de_email(client):
    for i in range(5):
        assert _login(client, f"x{i}@exemplo.com.br").status_code == 401
    assert _login(client, "outro@exemplo.com.br").status_code == 429


def test_x_forwarded_for_ignorado_sem_trust_proxy(client, monkeypatch):
    monkeypatch.delenv("TRUST_PROXY", raising=False)
    for i in range(5):
        _login(client, f"x{i}@exemplo.com.br", ip=f"10.0.0.{i}")
    # Forjar outro IP no cabeçalho não escapa do limite por IP
    assert _login(client, "novo@exemplo.com.br", ip="10.9.9.9").status_code == 429


def test_trust_proxy_usa_ip_do_proxy_e_limita_por_email(client, monkeypatch):
    monkeypatch.setenv("TRUST_PROXY", "1")
    for i in range(5):
        assert _login(client, f"x{i}@exemplo.com.br", ip="200.1.1.1").status_code == 401
    assert _login(client, "y@exemplo.com.br", ip="200.1.1.1").status_code == 429
    # Outro cliente (outro IP real) não é afetado; o começo do cabeçalho (forjável) é ignorado
    assert _login(client, "y@exemplo.com.br", ip="200.1.1.1, 200.2.2.2").status_code == 401
    # Mesmo e-mail atacado de vários IPs: bloqueia pelo e-mail
    for i in range(4):
        _login(client, "alvo@exemplo.com.br", ip=f"201.0.0.{i}")
    _login(client, "alvo@exemplo.com.br", ip="201.0.0.9")
    assert _login(client, "alvo@exemplo.com.br", ip="202.0.0.1").status_code == 429


def test_janela_de_um_minuto():
    agora = [1000.0]
    lim = Limitador(max_tentativas=5, janela=60, relogio=lambda: agora[0])
    for _ in range(5):
        lim.registrar_falha(["k"])
    assert lim.espera(["k"]) == 60
    agora[0] += 45
    assert lim.espera(["k"]) == 15
    agora[0] += 15
    assert lim.espera(["k"]) == 0


def test_consulta_e_aceite_de_convite_limitados(client):
    signup(client, "Ana", "ana@exemplo.com.br")
    ha = login(client, "ana@exemplo.com.br")
    signup(client, "Dani", "dani@exemplo.com.br")
    hd = login(client, "dani@exemplo.com.br")
    codigo = _convite(client, ha)
    for i in range(3):
        assert client.get(f"/api/estoque/convites/errado{i}", headers=hd).status_code == 400
    for i in range(2):
        r = client.post("/api/estoque/entrar", json={"codigo_convite": f"errado{i}"}, headers=hd)
        assert r.status_code == 400
    # 5 códigos errados (consulta + aceite somam): o código certo também fica bloqueado por 1 minuto
    r = client.get(f"/api/estoque/convites/{codigo}", headers=hd)
    assert r.status_code == 429 and "Muitas tentativas" in r.json()["detail"] and "Retry-After" in r.headers
    assert client.post("/api/estoque/entrar", json={"codigo_convite": codigo}, headers=hd).status_code == 429


def test_cadastro_com_convite_errado_limitado(client):
    for i in range(5):
        r = signup(client, f"P{i}", f"p{i}@exemplo.com.br", codigo_convite=f"errado{i}")
        assert r.status_code == 400
    r = signup(client, "P9", "p9@exemplo.com.br", codigo_convite="qualquer")
    assert r.status_code == 429
    # Cadastro sem convite não é afetado
    assert signup(client, "P9", "p9@exemplo.com.br").status_code == 201


def test_texto_da_espera():
    from limite import _texto_espera

    assert _texto_espera(60) == _texto_espera(55) == "1 minuto"
    assert _texto_espera(30) == "30 segundos" and _texto_espera(1) == "1 segundo"
    assert _texto_espera(120) == "2 minutos"
