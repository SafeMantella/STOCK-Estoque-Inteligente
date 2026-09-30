"""As migrations do Alembic criam exatamente o schema dos models (SQLite)."""
import os
import subprocess
import sys
from pathlib import Path

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect

import models  # noqa: F401
from database import Base

BACKEND = Path(__file__).resolve().parent.parent


def _alembic(url, *args):
    env = {**os.environ, "DATABASE_URL": url}
    r = subprocess.run([sys.executable, "-m", "alembic", *args], cwd=BACKEND, env=env,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r


def test_upgrade_head_igual_aos_models_e_downgrade(tmp_path):
    url = f"sqlite:///{tmp_path}/mig.db"
    _alembic(url, "upgrade", "head")
    engine = create_engine(url)
    with engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    assert diff == [], diff
    _alembic(url, "downgrade", "base")
    assert set(inspect(create_engine(url)).get_table_names()) <= {"alembic_version"}


def test_0002_resolve_duplicados_existentes(tmp_path):
    from sqlalchemy import text
    url = f"sqlite:///{tmp_path}/dup.db"
    _alembic(url, "upgrade", "0001")
    e = create_engine(url)
    with e.begin() as c:
        c.execute(text("INSERT INTO estoque (cod_estoque, descricao) VALUES (1, 'Casa A'), (2, 'Casa B')"))
        c.execute(text("INSERT INTO item (cod_item, descricao, categoria, cod_estoque) VALUES "
                       "(1, 'Café 500g', 'Bebidas', 1), (2, 'Cafe 500g', 'Bebidas', 1),"
                       "(3, 'CAFÉ  500G', 'Bebidas', 1), (4, 'Café 500g', 'Bebidas', 2)"))
        # item 3 (duplicado) está em uso na dispensa -> renomeado; item 2 sem uso -> apagado
        c.execute(text("INSERT INTO itemestoque VALUES (3, 1, 1, 0)"))
    _alembic(url, "upgrade", "head")
    with e.connect() as c:
        rows = c.execute(text("SELECT cod_item, descricao, cod_estoque, nome_normalizado FROM item ORDER BY cod_item")).fetchall()
    assert [tuple(r) for r in rows] == [
        (1, "Café 500g", 1, "cafe 500g"),
        (3, "CAFÉ  500G (2)", 1, "cafe 500g (2)"),
        (4, "Café 500g", 2, "cafe 500g"),  # outra casa: pode repetir
    ]
