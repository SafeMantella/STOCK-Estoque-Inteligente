"""item.nome_normalizado + UNIQUE(cod_estoque, nome_normalizado)

Preenche o nome normalizado dos itens existentes (sem acentos, minúsculo, espaços
colapsados) e resolve duplicados na mesma casa antes de criar a restrição:
  - mantém o item mais antigo (menor cod_item);
  - o duplicado mais novo é APAGADO se não estiver em nenhuma dispensa/lista
    (junção), ou RENOMEADO com sufixo " (2)", " (3)"... se estiver em uso.

Revision ID: 0002
Revises: 0001
"""
import logging
import unicodedata
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

log = logging.getLogger("alembic.runtime.migration")


def _normalizar(texto: str) -> str:
    # Cópia de texto.normalizar_nome (migrations não dependem do código da app)
    s = "".join(c for c in unicodedata.normalize("NFKD", texto or "") if not unicodedata.combining(c))
    return " ".join(s.lower().split())


def upgrade() -> None:
    with op.batch_alter_table("item") as batch_op:
        batch_op.add_column(sa.Column("nome_normalizado", sa.String(length=300), nullable=True))

    conn = op.get_bind()
    itens = conn.execute(sa.text("SELECT cod_item, cod_estoque, descricao FROM item ORDER BY cod_item")).fetchall()
    vistos = set()  # (cod_estoque, nome_normalizado)
    for cod_item, cod_estoque, descricao in itens:
        norm = _normalizar(descricao)
        if (cod_estoque, norm) not in vistos:
            vistos.add((cod_estoque, norm))
            conn.execute(sa.text("UPDATE item SET nome_normalizado = :n WHERE cod_item = :c"),
                         {"n": norm, "c": cod_item})
            continue
        em_uso = conn.execute(
            sa.text("SELECT (SELECT COUNT(*) FROM itemestoque WHERE cod_item = :c)"
                    " + (SELECT COUNT(*) FROM listaitem WHERE cod_item = :c)"),
            {"c": cod_item},
        ).scalar()
        if not em_uso:
            conn.execute(sa.text("DELETE FROM item WHERE cod_item = :c"), {"c": cod_item})
            log.warning("item %s %r (estoque %s) duplicado e sem uso: apagado", cod_item, descricao, cod_estoque)
            continue
        n = 2
        while (cod_estoque, _normalizar(f"{descricao} ({n})")) in vistos:
            n += 1
        novo = f"{descricao} ({n})"
        vistos.add((cod_estoque, _normalizar(novo)))
        conn.execute(sa.text("UPDATE item SET descricao = :d, nome_normalizado = :n WHERE cod_item = :c"),
                     {"d": novo, "n": _normalizar(novo), "c": cod_item})
        log.warning("item %s %r (estoque %s) duplicado e em uso: renomeado para %r", cod_item, descricao, cod_estoque, novo)

    with op.batch_alter_table("item") as batch_op:
        batch_op.alter_column("nome_normalizado", existing_type=sa.String(length=300), nullable=False)
        batch_op.create_unique_constraint("uq_item_estoque_nome", ["cod_estoque", "nome_normalizado"])


def downgrade() -> None:
    with op.batch_alter_table("item") as batch_op:
        batch_op.drop_constraint("uq_item_estoque_nome", type_="unique")
        batch_op.drop_column("nome_normalizado")
