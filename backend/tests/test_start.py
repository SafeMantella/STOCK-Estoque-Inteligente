"""Configuração de produção: URL do Postgres e comando de início (start.sh)."""
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from database import normalizar_database_url

BACKEND = Path(__file__).resolve().parent.parent


def test_normaliza_postgres_url_dos_hosts():
    assert normalizar_database_url("postgres://u:p@h:5432/db") == "postgresql://u:p@h:5432/db"
    assert normalizar_database_url(" postgresql://u:p@h/db ") == "postgresql://u:p@h/db"
    assert normalizar_database_url("postgresql+psycopg2://u@h/db") == "postgresql+psycopg2://u@h/db"
    assert normalizar_database_url("sqlite:///./stock.db") == "sqlite:///./stock.db"


def _porta_livre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_start_sh_migra_e_respeita_port(tmp_path):
    porta = _porta_livre()
    env = {
        **os.environ,
        "PATH": f"{Path(sys.executable).parent}{os.pathsep}{os.environ.get('PATH', '')}",
        "DATABASE_URL": f"sqlite:///{tmp_path}/start.db",
        "SECRET_KEY": "chave-apenas-para-testes-start",
        "PORT": str(porta),
    }
    p = subprocess.Popen(["sh", "start.sh"], cwd=BACKEND, env=env, start_new_session=True,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        corpo = None
        for _ in range(60):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{porta}/api/health", timeout=1) as r:
                    corpo = r.read().decode()
                break
            except OSError:
                if p.poll() is not None:
                    break
                time.sleep(0.25)
        assert corpo is not None, p.stdout.read().decode() if p.poll() is not None else "sem resposta"
        assert '"ok"' in corpo
        with urllib.request.urlopen(f"http://127.0.0.1:{porta}/", timeout=2) as r:
            assert "text/html" in r.headers["content-type"]
    finally:
        os.killpg(p.pid, signal.SIGTERM)
        p.wait(timeout=10)
