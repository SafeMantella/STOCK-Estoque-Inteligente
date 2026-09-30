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


def test_catalogo_isolado_por_casa(client):
    signup(client, "Ana", "ana@exemplo.com.br", descricao_estoque="Casa da Ana")
    signup(client, "Dani", "dani@exemplo.com.br", descricao_estoque="Casa da Dani")
    ha, hd = login(client, "ana@exemplo.com.br"), login(client, "dani@exemplo.com.br")
    r = client.post("/api/items", json={"descricao": "Leite 1L", "categoria": "Laticínios"}, headers=ha)
    leite = r.json()["cod_item"]

    # Dani não vê nem consegue usar o item da Ana
    assert client.get("/api/items", headers=hd).json() == []
    assert client.get(f"/api/items?cod_item={leite}", headers=hd).json() == []
    r = client.post("/api/stock", json={"cod_item": leite, "qtd_desejada": 1, "qtd_estoque": 0}, headers=hd)
    assert r.status_code == 404
    # Dani pode ter o próprio "Leite 1L"
    assert client.post("/api/items", json={"descricao": "Leite 1L", "categoria": "Laticínios"}, headers=hd).status_code == 201
    # duplicado na mesma casa é rejeitado (sem diferenciar maiúsculas)
    r = client.post("/api/items", json={"descricao": " leite 1l ", "categoria": "Laticínios"}, headers=ha)
    assert r.status_code == 409
    assert [i["descricao"] for i in client.get("/api/items", headers=ha).json()] == ["Leite 1L"]

    # morador convidado vê o catálogo da casa
    r = client.post("/api/estoque/convites", headers=ha)
    signup(client, "Beto", "beto@exemplo.com.br", codigo_convite=r.json()["codigo"])
    hb = login(client, "beto@exemplo.com.br")
    assert [i["cod_item"] for i in client.get("/api/items", headers=hb).json()] == [leite]


def test_duplicado_ignora_acentos_maiusculas_e_espacos(client):
    signup(client, "Ana", "ana@exemplo.com.br")
    ha = login(client, "ana@exemplo.com.br")
    assert client.post("/api/items", json={"descricao": "Café 500g", "categoria": "Bebidas"}, headers=ha).status_code == 201
    for variante in ["Cafe 500g", "CAFÉ   500G", " café 500g "]:
        r = client.post("/api/items", json={"descricao": variante, "categoria": "Bebidas"}, headers=ha)
        assert r.status_code == 409, variante
        assert "Já existe" in r.json()["detail"]


def test_unique_no_banco_vira_409(client, monkeypatch):
    # Simula corrida: a checagem prévia não vê o duplicado, a restrição UNIQUE do banco sim
    import routers.items as items
    signup(client, "Ana", "ana@exemplo.com.br")
    ha = login(client, "ana@exemplo.com.br")
    client.post("/api/items", json={"descricao": "Arroz", "categoria": "Outros"}, headers=ha)
    monkeypatch.setattr(items, "checar_nome_livre", lambda db, cod, desc, ignorar_cod_item=None: items.normalizar_nome(desc))
    r = client.post("/api/items", json={"descricao": "arroz", "categoria": "Outros"}, headers=ha)
    assert r.status_code == 409 and "Já existe" in r.json()["detail"]


def test_erros_de_validacao_em_portugues(client):
    r = signup(client, "Ana", "nao-e-email", senha="123")
    assert r.status_code == 422
    body = r.json()
    campos = {e["campo"]: e["mensagem"] for e in body["erros"]}
    assert campos["email"].startswith("Informe um e-mail válido")
    assert campos["senha"] == "Senha deve ter pelo menos 8 caracteres."
    assert "String should" not in body["detail"] and "value is not" not in body["detail"]

    r = client.post("/api/users", json={"email": "ana@exemplo.com.br", "senha": "Stock@2026"})
    assert r.json()["erros"] == [{"campo": "nome", "mensagem": "Nome é obrigatório."}]

    signup(client, "Ana", "ana@exemplo.com.br")
    ha = login(client, "ana@exemplo.com.br")
    cod = client.post("/api/items", json={"descricao": "Sal", "categoria": "Outros"}, headers=ha).json()["cod_item"]
    r = client.post("/api/stock", json={"cod_item": cod, "qtd_desejada": 1, "qtd_estoque": -1}, headers=ha)
    assert r.status_code == 422 and r.json()["detail"] == "Quantidade em casa não pode ser negativa."
    r = client.post("/api/stock", json={"cod_item": cod, "qtd_desejada": "abc", "qtd_estoque": 0}, headers=ha)
    assert r.json()["detail"] == "Quantidade mínima deve ser um número inteiro."
    r = client.post("/api/items", json={"descricao": "", "categoria": "Outros"}, headers=ha)
    assert r.json()["detail"] == "Descrição não pode ficar em branco."


def _novo(client, h, descricao, minimo, atual, categoria="Outros"):
    return client.post("/api/stock/novo-item", headers=h, json={
        "descricao": descricao, "categoria": categoria, "qtd_desejada": minimo, "qtd_estoque": atual})


def test_cadastrar_item_ja_na_dispensa(client):
    signup(client, "Ana", "ana@exemplo.com.br")
    ha = login(client, "ana@exemplo.com.br")
    r = _novo(client, ha, "Açúcar 1kg", 2, 0)
    assert r.status_code == 201, r.text
    assert r.json()["qtd_desejada"] == 2 and r.json()["qtd_estoque"] == 0
    assert [i["descricao"] for i in client.get("/api/items", headers=ha).json()] == ["Açúcar 1kg"]
    assert [i["qtd_a_comprar"] for i in client.get("/api/lista", headers=ha).json()] == [2]
    # duplicado não cria nada
    assert _novo(client, ha, "acucar 1KG", 1, 1).status_code == 409
    assert len(client.get("/api/stock", headers=ha).json()) == 1
    # validação: mínimo 0 e em casa negativo
    r = _novo(client, ha, "Sal", 0, -1)
    assert r.status_code == 422
    assert {e["campo"] for e in r.json()["erros"]} == {"qtd_desejada", "qtd_estoque"}


def test_ajuste_relativo_nunca_abaixo_de_zero(client):
    signup(client, "Ana", "ana@exemplo.com.br")
    ha = login(client, "ana@exemplo.com.br")
    cod = _novo(client, ha, "Ovos", 12, 2).json()["cod_item"]
    aj = lambda d: client.post(f"/api/stock/{cod}/ajuste", json={"delta": d}, headers=ha)
    assert aj(1).json()["qtd_estoque"] == 3
    assert aj(-1).json()["qtd_estoque"] == 2
    assert aj(-5).json()["qtd_estoque"] == 0
    assert aj(-1).json()["qtd_estoque"] == 0
    assert aj(2000).status_code == 422
    # outra casa não ajusta
    signup(client, "Dani", "dani@exemplo.com.br")
    hd = login(client, "dani@exemplo.com.br")
    assert client.post(f"/api/stock/{cod}/ajuste", json={"delta": 1}, headers=hd).status_code == 404


def test_ajustes_de_dois_moradores_somam(client):
    # O ajuste é relativo (UPDATE ... qtd = qtd + delta): cada +1 conta, sem o cliente
    # precisar ler o valor antes (com PUT absoluto, dois cliques simultâneos virariam um).
    signup(client, "Ana", "ana@exemplo.com.br")
    ha = login(client, "ana@exemplo.com.br")
    cod = _novo(client, ha, "Pão", 5, 1).json()["cod_item"]
    for _ in range(2):
        client.post(f"/api/stock/{cod}/ajuste", json={"delta": 1}, headers=ha)
    assert client.get("/api/stock", headers=ha).json()[0]["qtd_estoque"] == 3


def test_editar_e_excluir_item(client):
    signup(client, "Ana", "ana@exemplo.com.br")
    ha = login(client, "ana@exemplo.com.br")
    cafe = _novo(client, ha, "Café 500g", 1, 1, "Bebidas").json()["cod_item"]
    leite = _novo(client, ha, "Leite", 6, 6, "Laticínios").json()["cod_item"]

    r = client.put(f"/api/stock/{leite}", json={"descricao": "Leite integral 1L", "qtd_desejada": 8}, headers=ha)
    assert r.status_code == 200 and r.json()["descricao"] == "Leite integral 1L" and r.json()["qtd_desejada"] == 8
    # renomear para um nome já existente (sem acento) -> 409
    r = client.put(f"/api/stock/{leite}", json={"descricao": "cafe 500G"}, headers=ha)
    assert r.status_code == 409
    # renomear para o próprio nome com outra grafia é permitido
    assert client.put(f"/api/stock/{cafe}", json={"descricao": "CAFÉ 500g"}, headers=ha).status_code == 200

    assert client.delete(f"/api/stock/{cafe}", headers=ha).status_code == 204
    assert [i["cod_item"] for i in client.get("/api/stock", headers=ha).json()] == [leite]
    assert [i["cod_item"] for i in client.get("/api/items", headers=ha).json()] == [leite]
    assert client.delete(f"/api/stock/{cafe}", headers=ha).status_code == 404
    # o nome fica livre de novo
    assert _novo(client, ha, "Café 500g", 1, 0).status_code == 201


def test_consultar_convite_antes_de_aceitar(client):
    signup(client, "Ana", "ana@exemplo.com.br", descricao_estoque="Casa Teste")
    signup(client, "Eva", "eva@exemplo.com.br")
    ha, he = login(client, "ana@exemplo.com.br"), login(client, "eva@exemplo.com.br")
    codigo = client.post("/api/estoque/convites", headers=ha).json()["codigo"]

    assert client.get(f"/api/estoque/convites/{codigo}").status_code == 401  # exige login
    r = client.get(f"/api/estoque/convites/{codigo}", headers=he)
    assert r.status_code == 200, r.text
    assert r.json()["descricao"] == "Casa Teste" and r.json()["dono_nome"] == "Ana"
    # consultar não consome o convite
    assert client.get(f"/api/estoque/convites/{codigo}", headers=he).status_code == 200

    r = client.get("/api/estoque/convites/naoexiste", headers=he)
    assert r.status_code == 400 and "não encontrado" in r.json()["detail"]
    r = client.get(f"/api/estoque/convites/{codigo}", headers=ha)
    assert r.status_code == 400 and "já faz parte" in r.json()["detail"]

    assert client.post("/api/estoque/entrar", json={"codigo_convite": codigo}, headers=he).status_code == 200
    signup(client, "Fabi", "fabi@exemplo.com.br")
    hf = login(client, "fabi@exemplo.com.br")
    r = client.get(f"/api/estoque/convites/{codigo}", headers=hf)
    assert r.status_code == 400 and "já foi usado" in r.json()["detail"]


def test_consultar_convite_expirado_e_dono_bloqueado(client):
    from datetime import datetime, timedelta, timezone
    from database import SessionLocal
    from models import ConviteEstoque
    signup(client, "Ana", "ana@exemplo.com.br", descricao_estoque="Casa Teste")
    signup(client, "Carla", "carla@exemplo.com.br", descricao_estoque="Casa da Carla")
    ha, hc = login(client, "ana@exemplo.com.br"), login(client, "carla@exemplo.com.br")
    client.post("/api/stock/novo-item", headers=hc, json={"descricao": "Sal", "categoria": "Outros", "qtd_desejada": 1, "qtd_estoque": 1})
    codigo = client.post("/api/estoque/convites", headers=ha).json()["codigo"]
    r = client.get(f"/api/estoque/convites/{codigo}", headers=hc)
    assert r.status_code == 409 and "dono" in r.json()["detail"]

    with SessionLocal() as db:
        c = db.get(ConviteEstoque, codigo)
        c.expira_em = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()
    signup(client, "Eva", "eva@exemplo.com.br")
    r = client.get(f"/api/estoque/convites/{codigo}", headers=login(client, "eva@exemplo.com.br"))
    assert r.status_code == 400 and "expirou" in r.json()["detail"]
