"""seed_dev.py nunca roda sem STOCK_ENV=dev (produção começa vazia)."""
import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect

BACKEND = Path(__file__).resolve().parent.parent


def _rodar(tmp_path, **extra):
    env = dict(os.environ)
    env.update(DATABASE_URL=f"sqlite:///{tmp_path}/seed.db", SECRET_KEY="chave-apenas-para-testes-seed", **extra)
    return subprocess.run([sys.executable, str(BACKEND / "seed_dev.py")], cwd=tmp_path, env=env,
                          capture_output=True, text=True, timeout=60)


def test_seed_recusa_sem_stock_env_dev(tmp_path):
    # (valor definido no ambiente tem prioridade sobre o backend/.env de quem roda os testes)
    for valor in ("production", "", "prod"):
        r = _rodar(tmp_path, STOCK_ENV=valor)
        assert r.returncode != 0 and "STOCK_ENV=dev" in r.stderr
    assert not inspect(create_engine(f"sqlite:///{tmp_path}/seed.db")).get_table_names()


def test_seed_roda_com_stock_env_dev(tmp_path):
    r = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=BACKEND, capture_output=True,
                       text=True, env={**os.environ, "DATABASE_URL": f"sqlite:///{tmp_path}/seed.db"})
    assert r.returncode == 0, r.stderr
    r = _rodar(tmp_path, STOCK_ENV="dev", PYTHONPATH=str(BACKEND))
    assert r.returncode == 0, r.stderr
    assert "ana.teste@exemplo.com.br" in r.stdout
