"""Exclusão lógica de item (Excluir tira da casa inteira; Desfazer = /restaurar)."""
from conftest import login, signup


def _casa(client):
    signup(client, "Ana", "ana@exemplo.com.br")
    ha = login(client, "ana@exemplo.com.br")
    codigo = client.post("/api/estoque/convites", headers=ha).json()["codigo"]
    signup(client, "Beto", "beto@exemplo.com.br", codigo_convite=codigo)
    hb = login(client, "beto@exemplo.com.br")
    return ha, hb


def _novo(client, h, descricao, minimo=6, atual=1):
    r = client.post("/api/stock/novo-item", headers=h,
                    json={"descricao": descricao, "categoria": "Laticínios", "qtd_desejada": minimo, "qtd_estoque": atual})
    assert r.status_code == 201, r.text
    return r.json()["cod_item"]


def test_item_excluido_some_de_todas_as_leituras(client):
    ha, hb = _casa(client)
    leite = _novo(client, ha, "Leite")
    _novo(client, ha, "Arroz", 2, 0)
    assert client.delete(f"/api/stock/{leite}", headers=hb).status_code == 204  # qualquer morador exclui
    for h in (ha, hb):
        assert [i["descricao"] for i in client.get("/api/stock", headers=h).json()] == ["Arroz"]
        assert [i["descricao"] for i in client.get("/api/lista", headers=h).json()] == ["Arroz"]
        assert [i["descricao"] for i in client.get("/api/items", headers=h).json()] == ["Arroz"]
        assert client.get("/api/items?descricao=leite", headers=h).json() == []
    assert client.get("/api/estoque/meu", headers=ha).json()["itens"] == 1


def test_acoes_em_item_excluido_dao_404(client):
    ha, _ = _casa(client)
    leite = _novo(client, ha, "Leite")
    client.delete(f"/api/stock/{leite}", headers=ha)
    assert client.post(f"/api/stock/{leite}/ajuste", json={"delta": 1}, headers=ha).status_code == 404
    assert client.put(f"/api/stock/{leite}", json={"qtd_estoque": 3}, headers=ha).status_code == 404
    assert client.delete(f"/api/stock/{leite}", headers=ha).status_code == 404
    assert client.post("/api/lista/comprar", json={"cod_item": leite, "qtd_comprada": 1}, headers=ha).status_code == 404
    r = client.post("/api/stock", json={"cod_item": leite, "qtd_desejada": 1, "qtd_estoque": 0}, headers=ha)
    assert r.status_code == 404


def test_excluir_e_recriar_com_o_mesmo_nome(client):
    ha, _ = _casa(client)
    leite = _novo(client, ha, "Leite")
    client.delete(f"/api/stock/{leite}", headers=ha)
    novo = _novo(client, ha, "leite")  # mesmo nome normalizado: permitido
    assert novo != leite
    assert client.post("/api/items", json={"descricao": "Leite", "categoria": "X"}, headers=ha).status_code == 409
    # Desfazer o antigo agora conflita com o novo ativo
    r = client.post(f"/api/stock/{leite}/restaurar", headers=ha)
    assert r.status_code == 409 and r.json()["detail"] == 'Já existe outro "leite" no estoque'


def test_restaurar_volta_com_as_quantidades(client):
    ha, hb = _casa(client)
    leite = _novo(client, ha, "Leite", 6, 1)
    client.post(f"/api/stock/{leite}/ajuste", json={"delta": 1}, headers=ha)
    client.delete(f"/api/stock/{leite}", headers=ha)
    r = client.post(f"/api/stock/{leite}/restaurar", headers=hb)  # outro morador desfaz
    assert r.status_code == 200 and r.json()["qtd_estoque"] == 2 and r.json()["qtd_desejada"] == 6
    assert [i["cod_item"] for i in client.get("/api/lista", headers=ha).json()] == [leite]
    # restaurar item já ativo: nada muda
    assert client.post(f"/api/stock/{leite}/restaurar", headers=ha).status_code == 200


def test_restaurar_so_na_mesma_casa(client):
    ha, _ = _casa(client)
    leite = _novo(client, ha, "Leite")
    client.delete(f"/api/stock/{leite}", headers=ha)
    signup(client, "Carla", "carla@exemplo.com.br")
    hc = login(client, "carla@exemplo.com.br")
    assert client.post(f"/api/stock/{leite}/restaurar", headers=hc).status_code == 404
    assert client.post("/api/stock/999999/restaurar", headers=ha).status_code == 404
    assert client.get("/api/stock", headers=ha).json() == []


def test_renomear_para_nome_de_item_excluido(client):
    ha, _ = _casa(client)
    leite = _novo(client, ha, "Leite")
    arroz = _novo(client, ha, "Arroz")
    client.delete(f"/api/stock/{leite}", headers=ha)
    r = client.put(f"/api/stock/{arroz}", json={"descricao": "Leite"}, headers=ha)
    assert r.status_code == 200 and r.json()["descricao"] == "Leite"
