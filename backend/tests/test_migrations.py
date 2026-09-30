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
