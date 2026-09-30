"""Toasts (Desfazer empilhado, sem cobrir cards), item excluído por outro morador, rótulos, 429."""
import re
import uuid

from conftest import SENHA, entrar


def _tag():
    return uuid.uuid4().hex[:5]


def _excluir(page, nome):
    card = page.locator("#estoque-cards .card", has_text=nome)
    card.locator("text=Editar").scroll_into_view_if_needed()
    card.locator("text=Editar").click()
    card.locator("text=Excluir item").click()
    page.wait_for_timeout(400)


def _abrir_estoque(page, base_url):
    page.on("dialog", lambda d: d.accept())
    entrar(page, base_url)
    page.goto(base_url + "/pages/estoque.html")
    page.wait_for_selector("#estoque-cards .card")


def test_desfazer_empilha_ate_3_e_restaura_so_o_seu(ctx, base_url, api_ana):
    t = _tag()
    nomes = [f"Zz {t} {i}" for i in range(4)]
    for n in nomes:
        api_ana.novo(n)
    page = ctx.new_page()
    _abrir_estoque(page, base_url)
    for n in nomes:
        _excluir(page, n)
    assert not any(n in api_ana.nomes() for n in nomes)  # DELETE na hora (exclusão lógica)
    desfazer = page.locator("#toast-area .toast-stock", has=page.locator(".toast-acao"))
    assert desfazer.count() == 3  # o mais antigo sai
    # aviso comum (salvar edição) não substitui nenhum Desfazer
    card = page.locator("#estoque-cards .card", has_text="Arroz")
    card.locator("text=Editar").click()
    card.locator("button[type=submit]").click()
    page.wait_for_timeout(600)
    assert desfazer.count() == 3
    page.locator("#toast-area .toast-stock", has_text=nomes[2]).locator(".toast-acao").click()
    page.wait_for_timeout(800)
    ativos = api_ana.nomes()
    assert nomes[2] in ativos and nomes[1] not in ativos and nomes[3] not in ativos
    assert page.locator("#estoque-cards .card", has_text=nomes[2]).count() == 1
    assert desfazer.count() == 2


def test_desfazer_com_nome_ja_usado_mostra_409(ctx, base_url, api_ana):
    n = f"Zz {_tag()} leite"
    api_ana.novo(n)
    page = ctx.new_page()
    _abrir_estoque(page, base_url)
    _excluir(page, n)
    api_ana.novo(n.upper())
    page.locator("#toast-area .toast-stock", has_text=n).locator(".toast-acao").click()
    page.wait_for_timeout(700)
    assert "Já existe outro" in page.locator("#toast-area .toast-comum").inner_text()


def test_aviso_nao_cobre_o_ultimo_card(ctx, base_url, api_ana):
    n = f"Zz {_tag()} fim"
    api_ana.novo(n)
    page = ctx.new_page()
    _abrir_estoque(page, base_url)
    page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
    _excluir(page, n)
    page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
    page.wait_for_timeout(300)
    topo_avisos = page.locator("#toast-area").bounding_box()["y"]
    editar = page.locator("#estoque-cards .card").last.locator("text=Editar").bounding_box()
    assert editar["y"] + editar["height"] <= topo_avisos


def test_item_excluido_em_outra_aba(ctx, base_url, api_ana):
    n = f"Zz {_tag()} aba"
    api_ana.novo(n)
    page = ctx.new_page()
    _abrir_estoque(page, base_url)
    api_ana.chamar("DELETE", f"/stock/{next(i['cod_item'] for i in api_ana.chamar('GET', '/stock') if i['descricao'] == n)}")
    page.locator("#estoque-cards .card", has_text=n).get_by_role("button", name=re.compile("Adicionar 1")).click()
    page.wait_for_timeout(800)
    assert page.locator("#toast-area .toast-comum").inner_text().startswith("Esse item foi excluído por alguém da casa.")
    assert page.locator("#estoque-cards .card", has_text=n).count() == 0


ROTULOS_JS = """() => {
  const probs = [];
  document.querySelectorAll('label').forEach(l => { if (!l.control) probs.push('label sem campo: ' + l.textContent.trim()); });
  document.querySelectorAll('input:not([type=hidden]), select, textarea').forEach(c => {
    if (!c.offsetParent) return;
    if (!((c.labels && c.labels.length) || c.getAttribute('aria-label'))) probs.push('campo sem rótulo: ' + (c.name || c.id));
  });
  return probs;
}"""


def test_todos_os_campos_tem_rotulo(ctx, base_url):
    page = ctx.new_page()
    for u in ("/index.html", "/pages/cadastroUsuario.html"):
        page.goto(base_url + u)
        assert page.evaluate(ROTULOS_JS) == [], u
    entrar(page, base_url)
    for u in ("/menu.html", "/pages/buscarItem.html", "/pages/contato.html", "/pages/cadastroItem.html",
              "/pages/estoque.html", "/pages/listaCompras.html", "/pages/listarItens.html", "/pages/usuarios.html"):
        page.goto(base_url + u)
        page.wait_for_timeout(500)
        assert page.evaluate(ROTULOS_JS) == [], u


def test_login_429_no_aviso_sem_apagar_o_email(ctx, base_url):
    page = ctx.new_page()
    page.goto(base_url + "/index.html")
    email = f"ninguem.{_tag()}@exemplo.com.br"
    page.fill("#login-email", email)
    for i in range(6):
        page.fill("#login-senha", f"errada-{i}")
        page.click("button[type=submit]")
        page.wait_for_timeout(500)
    assert page.locator("#toast-area").inner_text().startswith("Muitas tentativas. Tente de novo em")
    assert page.input_value("#login-email") == email
