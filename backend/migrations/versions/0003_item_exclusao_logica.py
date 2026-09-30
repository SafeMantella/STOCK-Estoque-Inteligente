"""item.excluido_em (exclusão lógica) + nome único só entre itens ativos

- Nova coluna item.excluido_em (NULL = ativo).
- A restrição UNIQUE(cod_estoque, nome_normalizado) vira um índice único PARCIAL
  "WHERE excluido_em IS NULL" (SQLite >= 3.8 e Postgres): um item excluído não
  impede cadastrar outro com o mesmo nome.

Downgrade: apaga de vez os itens excluídos logicamente (e suas linhas em
itemestoque/listaitem) antes de voltar a restrição UNIQUE total.

Revision ID: 0003
Revises: 0002
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ATIVO = sa.text("excluido_em IS NULL")


def upgrade() -> None:
    with op.batch_alter_table("item") as batch_op:
        batch_op.add_column(sa.Column("excluido_em", sa.DateTime(timezone=True), nullable=True))
        batch_op.drop_constraint("uq_item_estoque_nome", type_="unique")
    op.create_index(
        "uq_item_estoque_nome_ativo",
        "item",
        ["cod_estoque", "nome_normalizado"],
        unique=True,
        sqlite_where=ATIVO,
        postgresql_where=ATIVO,
    )


def downgrade() -> None:
    conn = op.get_bind()
    excluidos = "SELECT cod_item FROM item WHERE excluido_em IS NOT NULL"
    conn.execute(sa.text(f"DELETE FROM listaitem WHERE cod_item IN ({excluidos})"))
    conn.execute(sa.text(f"DELETE FROM itemestoque WHERE cod_item IN ({excluidos})"))
    conn.execute(sa.text("DELETE FROM item WHERE excluido_em IS NOT NULL"))
    op.drop_index("uq_item_estoque_nome_ativo", table_name="item")
    with op.batch_alter_table("item") as batch_op:
        batch_op.create_unique_constraint("uq_item_estoque_nome", ["cod_estoque", "nome_normalizado"])
        batch_op.drop_column("excluido_em")
