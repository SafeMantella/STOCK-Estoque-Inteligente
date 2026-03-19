from sqlalchemy import BigInteger, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from database import Base


class Estoque(Base):
    __tablename__ = "estoque"

    cod_estoque = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    descricao = Column(String(500), nullable=False)

    usuarios = relationship("Usuario", back_populates="estoque")
    itens = relationship("ItemEstoque", back_populates="estoque")
    listas = relationship("ListaCompra", back_populates="estoque")


class Item(Base):
    __tablename__ = "item"

    cod_item = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    descricao = Column(String(300), nullable=False)
    categoria = Column(String(300), nullable=False)

    estoques = relationship("ItemEstoque", back_populates="item")
    lista_itens = relationship("ListaItem", back_populates="item")


class Usuario(Base):
    __tablename__ = "usuario"

    cod_usuario = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    nome = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    senha = Column(String(500), nullable=False)
    permissao = Column(String(500), nullable=False, default="usuario")
    cod_estoque = Column(BigInteger, ForeignKey("estoque.cod_estoque"), nullable=False)

    estoque = relationship("Estoque", back_populates="usuarios")


class ItemEstoque(Base):
    __tablename__ = "itemestoque"

    cod_item = Column(BigInteger, ForeignKey("item.cod_item"), primary_key=True)
    cod_estoque = Column(BigInteger, ForeignKey("estoque.cod_estoque"), primary_key=True)
    qtd_desejada = Column(Integer, nullable=False, default=0)
    qtd_estoque = Column(Integer, nullable=False, default=0)

    item = relationship("Item", back_populates="estoques")
    estoque = relationship("Estoque", back_populates="itens")


class ListaCompra(Base):
    __tablename__ = "listacompra"

    cod_lista = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    cod_estoque = Column(BigInteger, ForeignKey("estoque.cod_estoque"), nullable=False)
    status = Column(String(30), nullable=False, default="aberta")

    estoque = relationship("Estoque", back_populates="listas")
    itens = relationship("ListaItem", back_populates="lista")


class ListaItem(Base):
    __tablename__ = "listaitem"

    cod_item = Column(BigInteger, ForeignKey("item.cod_item"), primary_key=True)
    cod_lista = Column(BigInteger, ForeignKey("listacompra.cod_lista"), primary_key=True)
    qtd_desejada = Column(Integer, nullable=False, default=0)
    status = Column(String(30), nullable=False, default="pendente")

    item = relationship("Item", back_populates="lista_itens")
    lista = relationship("ListaCompra", back_populates="itens")
