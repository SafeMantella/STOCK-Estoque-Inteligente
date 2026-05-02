<h3 align="center">
    <img src="logo.jpeg" width="300px">
    <br><br>
    <h1 align="center">STOCK - Estoque Inteligente</h1>
</h3>

<p align="center">
  <img src="https://img.shields.io/github/license/SafeMantella/STOCK-Estoque-Inteligente?style=flat&logo">
</p>

## 🔖 Sobre

O <strong>STOCK</strong> é um sistema de gerenciamento de estoque e gerador de lista de compras para sua casa.

Aplicação web construída como parte do Trabalho de Conclusão de Curso no [Instituto Federal de Mato Grosso do Sul](https://www.ifms.edu.br/).
Projeto feito em dupla por **[Pedro Arfux](https://github.com/SafeMantella)** e **[Vitor Gabriel](https://github.com/VitorGSF)** e 
orientado por **[Luiz Lomba](https://www.linkedin.com/in/luiz-fernando-delboni-lomba-b64aa018/)**.

## 🚀 Tecnologias

Esse projeto foi desenvolvido com as seguintes tecnologias:

- [Python](https://www.python.org/) + [FastAPI](https://fastapi.tiangolo.com/)
- [PostgreSQL](https://www.postgresql.org/) + [SQLAlchemy](https://www.sqlalchemy.org/)
- [HTML](https://developer.mozilla.org/pt-BR/docs/Web/HTML) + [CSS](https://developer.mozilla.org/pt-BR/docs/Web/CSS) + [JavaScript](https://developer.mozilla.org/pt-BR/docs/Web/JavaScript)
- [Bootstrap 5](https://getbootstrap.com/)

## ⚙️ Como rodar a aplicação

### Pré-requisitos

- Python 3.10+
- PostgreSQL rodando localmente

### 1. Clone o repositório e entre na branch

```bash
git clone https://github.com/SafeMantella/STOCK-Estoque-Inteligente.git
cd STOCK-Estoque-Inteligente
git checkout refactor/python-fastapi
```

### 2. Configure o banco de dados

Crie um banco de dados PostgreSQL chamado `stock`:

```sql
CREATE DATABASE stock;
```

### 3. Configure as variáveis de ambiente

Copie o arquivo de exemplo e edite com suas credenciais:

```bash
cp backend/.env.example .env
```

Abra o `.env` e ajuste conforme necessário:

```env
DATABASE_URL=postgresql://postgres:SUA_SENHA@localhost:5432/stock
SECRET_KEY=troque-esta-chave-em-producao
ACCESS_TOKEN_EXPIRE_MINUTES=480
```

### 4. Instale as dependências e suba o backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

O backend estará disponível em `http://localhost:8000`.
A documentação interativa da API (Swagger) fica em `http://localhost:8000/docs`.

### 5. Suba o frontend

Em outro terminal, a partir da raiz do projeto:

```bash
cd frontend
python -m http.server 3000
```

Acesse a aplicação em `http://localhost:3000`.

> **Obs.:** O banco de dados é criado automaticamente na primeira execução do backend (via SQLAlchemy `create_all`). Nenhuma migration manual é necessária.

## 📝 License

Esse projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

<h4 align="center">
    Feito com 💚  por <a href="https://www.linkedin.com/in/pedroarfux/">Pedro Arfux</a> e <a href="https://www.linkedin.com/in/vitor-gabriel-de-souza-farias-564651196/">Vitor Gabriel</a>.
</h4>
