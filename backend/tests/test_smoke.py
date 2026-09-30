"""Smoke test do fluxo mínimo do MVP (API)."""
from conftest import login, signup


def _add_item(client, h, descricao, categoria, minimo, atual):
    r = client.post("/api/items", json={"descricao": descricao, "categoria": categoria}, headers=h)
    assert r.status_code == 201, r.text
    cod = r.json()["cod_item"]
    r = client.post("/api/stock", json={"cod_item": cod, "qtd_desejada": minimo, "qtd_estoque": atual}, headers=h)
    assert r.status_code == 201, r.text
    return cod


def test_fluxo_mvp(client):
    # cadastro cria estoque novo e o usuário vira dono
    r = signup(client, "Ana", "ana@exemplo.com.br", descricao_estoque="Casa da Ana")
    assert r.status_code == 201, r.text
    ha = login(client, "ana@exemplo.com.br")
    meu = client.get("/api/estoque/meu", headers=ha).json()
    assert meu["descricao"] == "Casa da Ana" and meu["sou_dono"] is True and meu["membros"] == 1

    # itens + dispensa
    leite = _add_item(client, ha, "Leite 1L", "Laticínios", 6, 0)
    arroz = _add_item(client, ha, "Arroz 5kg", "Cereais e Mel", 2, 3)
    cafe = _add_item(client, ha, "Café 500g", "Bebidas", 1, 2)
    assert len(client.get("/api/stock", headers=ha).json()) == 3

    # altera quantidade: arroz 3 -> 1 (fica abaixo do mínimo)
    r = client.put(f"/api/stock/{arroz}", json={"qtd_estoque": 1}, headers=ha)
    assert r.status_code == 200 and r.json()["qtd_estoque"] == 1

    # lista automática: só leite (6) e arroz (1)
    lista = {i["cod_item"]: i["qtd_a_comprar"] for i in client.get("/api/lista", headers=ha).json()}
    assert lista == {leite: 6, arroz: 1}
    assert cafe not in lista

    # comprar atualiza o estoque e tira o item da lista
    r = client.post("/api/lista/comprar", json={"cod_item": leite, "qtd_comprada": 6}, headers=ha)
    assert r.status_code == 200 and r.json()["qtd_estoque"] == 6
    lista = {i["cod_item"]: i["qtd_a_comprar"] for i in client.get("/api/lista", headers=ha).json()}
    assert lista == {arroz: 1}

    # convite gerado pelo dono
    r = client.post("/api/estoque/convites", headers=ha)
    assert r.status_code == 201, r.text
    codigo = r.json()["codigo"]
    assert len(codigo) >= 10

    # morador entra pelo cadastro com convite e vê a mesma lista
    r = signup(client, "Beto", "beto@exemplo.com.br", codigo_convite=codigo)
    assert r.status_code == 201, r.text
    assert r.json()["cod_estoque"] == meu["cod_estoque"]
    hb = login(client, "beto@exemplo.com.br")
    meu_b = client.get("/api/estoque/meu", headers=hb).json()
    assert meu_b["sou_dono"] is False and meu_b["membros"] == 2
    assert [i["cod_item"] for i in client.get("/api/lista", headers=hb).json()] == [arroz]

    # morador não gera convite
    assert client.post("/api/estoque/convites", headers=hb).status_code == 403

    # convite reutilizado é rejeitado
    r = signup(client, "Caio", "caio@exemplo.com.br", codigo_convite=codigo)
    assert r.status_code == 400
    # e o usuário não é criado
    r = client.post("/api/auth/login", json={"email": "caio@exemplo.com.br", "senha": "Stock@2026"})
    assert r.status_code == 401


def test_senha_minima_8(client):
    assert signup(client, "X", "x@exemplo.com.br", senha="1234567").status_code == 422
    assert signup(client, "X", "x@exemplo.com.br", senha="12345678").status_code == 201


def test_cadastro_ignora_cod_estoque(client):
    signup(client, "Ana", "ana@exemplo.com.br")
    r = signup(client, "Intruso", "intruso@exemplo.com.br", cod_estoque=1)
    assert r.status_code == 201
    assert r.json()["cod_estoque"] != 1


def _convite(client, h):
    r = client.post("/api/estoque/convites", headers=h)
    assert r.status_code == 201, r.text
    return r.json()["codigo"]


def test_login_com_convite_nao_troca_estoque(client):
    signup(client, "Ana", "ana@exemplo.com.br", descricao_estoque="Casa da Ana")
    signup(client, "Dani", "dani@exemplo.com.br", descricao_estoque="Casa da Dani")
    ha = login(client, "ana@exemplo.com.br")
    codigo = _convite(client, ha)
    r = client.post("/api/auth/login", json={"email": "dani@exemplo.com.br", "senha": "Stock@2026", "codigo_convite": codigo})
    assert r.status_code == 200
    hd = {"Authorization": f"Bearer {r.json()['access_token']}"}
    assert client.get("/api/estoque/meu", headers=hd).json()["descricao"] == "Casa da Dani"
    # o convite continua válido para ser aceito explicitamente
    r = client.post("/api/estoque/entrar", json={"codigo_convite": codigo}, headers=hd)
    assert r.status_code == 200, r.text
    assert r.json()["descricao"] == "Casa da Ana"


def test_entrar_bloqueado_para_dono_com_itens_ou_moradores(client):
    signup(client, "Ana", "ana@exemplo.com.br", descricao_estoque="Casa da Ana")
    signup(client, "Dani", "dani@exemplo.com.br", descricao_estoque="Casa da Dani")
    ha, hd = login(client, "ana@exemplo.com.br"), login(client, "dani@exemplo.com.br")

    # Dani tem um item na dispensa -> não pode aceitar convite
    r = client.post("/api/items", json={"descricao": "Sal", "categoria": "Outros"}, headers=hd)
    client.post("/api/stock", json={"cod_item": r.json()["cod_item"], "qtd_desejada": 1, "qtd_estoque": 1}, headers=hd)
    meu = client.get("/api/estoque/meu", headers=hd).json()
    assert meu["sou_dono"] and meu["itens"] == 1 and meu["pode_trocar"] is False
    codigo = _convite(client, ha)
    r = client.post("/api/estoque/entrar", json={"codigo_convite": codigo}, headers=hd)
    assert r.status_code == 409
    assert client.get("/api/estoque/meu", headers=hd).json()["descricao"] == "Casa da Dani"

    # Ana (dono) com outro morador -> também bloqueada
    signup(client, "Beto", "beto@exemplo.com.br", codigo_convite=codigo)
    codigo_dani = _convite(client, hd)
    assert client.post("/api/estoque/entrar", json={"codigo_convite": codigo_dani}, headers=ha).status_code == 409

    # Beto (morador, não dono) pode trocar
    hb = login(client, "beto@exemplo.com.br")
    assert client.get("/api/estoque/meu", headers=hb).json()["pode_trocar"] is True
    r = client.post("/api/estoque/entrar", json={"codigo_convite": codigo_dani}, headers=hb)
    assert r.status_code == 200 and r.json()["descricao"] == "Casa da Dani"


def test_dono_de_estoque_vazio_pode_aceitar_convite(client):
    signup(client, "Ana", "ana@exemplo.com.br", descricao_estoque="Casa da Ana")
    signup(client, "Eva", "eva@exemplo.com.br")  # criou conta sem convite por engano
    ha, he = login(client, "ana@exemplo.com.br"), login(client, "eva@exemplo.com.br")
    assert client.get("/api/estoque/meu", headers=he).json()["pode_trocar"] is True
    codigo = _convite(client, ha)
    r = client.post("/api/estoque/entrar", json={"codigo_convite": codigo}, headers=he)
    assert r.status_code == 200 and r.json()["descricao"] == "Casa da Ana"
    # já está no estoque -> erro claro
    r = client.post("/api/estoque/entrar", json={"codigo_convite": _convite(client, ha)}, headers=he)
    assert r.status_code == 400
