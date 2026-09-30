import os
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent


def _importa_main(secret, tmp_path):
    env = {**os.environ, "SECRET_KEY": secret, "DATABASE_URL": f"sqlite:///{tmp_path}/cfg.db"}
    return subprocess.run([sys.executable, "-c", "import main"], cwd=BACKEND, env=env,
                          capture_output=True, text=True)


def test_backend_nao_sobe_sem_secret_key(tmp_path):
    for secret in ["", "change-me-in-production", "troque-esta-chave-em-producao", "curta"]:
        r = _importa_main(secret, tmp_path)
        assert r.returncode != 0, secret
        assert "SECRET_KEY" in r.stderr


def test_backend_sobe_com_secret_key(tmp_path):
    assert _importa_main("x" * 32, tmp_path).returncode == 0
