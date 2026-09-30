"""Testes de interface (navegador) do STOCK — rodam à parte do `uv run pytest` do backend.

    cd backend && uv run --with playwright pytest ../e2e
    (Chrome/Chromium: usa CHROME_PATH, /usr/bin/google-chrome ou o Chromium do Playwright:
     `uv run --with playwright playwright install chromium`)

Sobe o backend (que serve o frontend na mesma origem) numa porta livre com um banco
SQLite temporário e as contas do seed_dev.py; não toca no banco de desenvolvimento.
"""
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent / "backend"
SENHA = "Stock@2026"


def _porta_livre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def base_url(tmp_path_factory):
    db = tmp_path_factory.mktemp("e2e") / "e2e.db"
    porta = _porta_livre()
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{db}", "SECRET_KEY": "chave-apenas-para-testes-e2e",
           "STOCK_ENV": "dev", "RATE_LIMIT_IP": "1000"}
    for cmd in ([sys.executable, "-m", "alembic", "upgrade", "head"], [sys.executable, "seed_dev.py"]):
        subprocess.run(cmd, cwd=BACKEND, env=env, check=True, capture_output=True)
    proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(porta)],
                            cwd=BACKEND, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{porta}"
    for _ in range(80):
        try:
            urllib.request.urlopen(url + "/api/health", timeout=1)
            break
        except OSError:
            time.sleep(0.25)
    yield url
    proc.terminate()
    proc.wait(timeout=10)


@pytest.fixture(scope="session")
def navegador():
    from playwright.sync_api import sync_playwright
    caminho = os.getenv("CHROME_PATH") or shutil.which("google-chrome") or shutil.which("chromium")
    with sync_playwright() as p:
        br = p.chromium.launch(executable_path=caminho) if caminho else p.chromium.launch()
        yield br
        br.close()


@pytest.fixture()
def ctx(navegador):
    c = navegador.new_context(viewport={"width": 366, "height": 800}, is_mobile=True, has_touch=True)
    yield c
    c.close()


class Api:
    def __init__(self, base, email):
        self.base = base + "/api"
        self.token = self.chamar("POST", "/auth/login", {"email": email, "senha": SENHA}, auth=False)["access_token"]

    def chamar(self, metodo, caminho, corpo=None, auth=True):
        h = {"Content-Type": "application/json"}
        if auth:
            h["Authorization"] = "Bearer " + self.token
        req = urllib.request.Request(self.base + caminho, method=metodo, headers=h,
                                     data=json.dumps(corpo).encode() if corpo is not None else None)
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read() or "null")

    def nomes(self):
        return [i["descricao"] for i in self.chamar("GET", "/stock")]

    def novo(self, descricao, minimo=1, atual=1):
        return self.chamar("POST", "/stock/novo-item",
                           {"descricao": descricao, "categoria": "Outros", "qtd_desejada": minimo, "qtd_estoque": atual})


@pytest.fixture()
def api_ana(base_url):
    return Api(base_url, "ana.teste@exemplo.com.br")


def entrar(page, base_url, email="ana.teste@exemplo.com.br"):
    page.goto(base_url + "/index.html")
    page.fill("#login-email", email)
    page.fill("#login-senha", SENHA)
    page.click("button[type=submit]")
    page.wait_for_url(re.compile("menu.html"))
