"""Ambiente do Alembic do STOCK.

A URL do banco vem de DATABASE_URL (backend/.env), a mesma usada pela aplicação.
render_as_batch=True permite ALTER TABLE no SQLite (recria a tabela por baixo).
"""
from logging.config import fileConfig

from alembic import context

import models  # noqa: F401  (registra as tabelas em Base.metadata)
from database import DATABASE_URL, Base, engine as app_engine

config = context.config
if config.config_file_name is not None and config.attributes.get("configure_logger", True):
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # Testes podem passar uma conexão pronta em config.attributes["connection"]
    connection = config.attributes.get("connection")
    if connection is not None:
        _run(connection)
    else:
        with app_engine.connect() as conn:
            _run(conn)


def _run(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata, render_as_batch=True)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
