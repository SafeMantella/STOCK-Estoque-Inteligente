"""Popula um banco de DESENVOLVIMENTO com contas e itens de teste.

Uso (com o backend/.env configurado):  uv run python seed_dev.py
Passa pela própria API (TestClient), então as regras de negócio são as mesmas.
Não roda se as contas de teste já existirem. NUNCA use em produção: só roda com
STOCK_ENV=dev (no ambiente ou no backend/.env). Produção começa vazia (só `alembic upgrade head`).
"""
import os
import sys

from dotenv import load_dotenv

load_dotenv()
if os.getenv("STOCK_ENV", "").strip().lower() != "dev":
    sys.exit("seed_dev.py só roda em desenvolvimento: defina STOCK_ENV=dev (ex.: no backend/.env). "
             "Nunca rode isto no banco de produção.")

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402

SENHA = os.getenv("SEED_SENHA", "Stock@2026")  # senha pública só para testes locais

CASA_ANA = [  # (descrição, categoria, mínimo, tenho agora)
    ("Leite integral 1L", "Laticínios", 6, 2),  # abaixo do mínimo -> comprar 4
    ("Arroz 5kg", "Cereais e Mel", 2, 2),
    ("Café 500g", "Bebidas", 1, 3),
    ("Feijão carioca 1kg", "Leguminosas/Hortaliças/Raízes/Tubérculos", 2, 3),
]
CASA_CARLA = [("Sabão em pó 1kg", "Higiene e Limpeza", 1, 0)]


def main():
    c = TestClient(app)

    def cadastrar(nome, email, **extra):
        r = c.post("/api/users", json={"nome": nome, "email": email, "senha": SENHA, **extra})
        if r.status_code == 400 and "já cadastrado" in r.text:
            sys.exit(f"{email} já existe: banco já populado (apague backend/stock.db para recriar).")
        r.raise_for_status()
        t = c.post("/api/auth/login", json={"email": email, "senha": SENHA}).json()["access_token"]
        return {"Authorization": f"Bearer {t}"}

    def itens(h, lista):
        for desc, cat, minimo, atual in lista:
            cod = c.post("/api/items", json={"descricao": desc, "categoria": cat}, headers=h).json()["cod_item"]
            c.post("/api/stock", json={"cod_item": cod, "qtd_desejada": minimo, "qtd_estoque": atual},
                   headers=h).raise_for_status()

    ha = cadastrar("Ana Teste", "ana.teste@exemplo.com.br", descricao_estoque="Casa Teste")
    itens(ha, CASA_ANA)
    convite = c.post("/api/estoque/convites", headers=ha).json()["codigo"]
    cadastrar("Beto Teste", "beto.teste@exemplo.com.br", codigo_convite=convite)
    hc = cadastrar("Carla Teste", "carla.teste@exemplo.com.br", descricao_estoque="Casa da Carla")
    itens(hc, CASA_CARLA)

    print("Contas criadas (senha:", SENHA + ")")
    print("  ana.teste@exemplo.com.br   dona de 'Casa Teste' (4 itens, Leite abaixo do mínimo)")
    print("  beto.teste@exemplo.com.br  morador de 'Casa Teste'")
    print("  carla.teste@exemplo.com.br dona de 'Casa da Carla' (outra casa, 1 item)")


if __name__ == "__main__":
    main()
