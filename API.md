# Documentação da API e Banco de Dados - STOCK Estoque Inteligente

## 1. Visão Geral

Este documento detalha a arquitetura do sistema STOCK, originalmente implementado em PHP e MySQL. O objetivo é servir como um guia para a refatoração do backend para Python, descrevendo a estrutura do banco de dados, a lógica de negócios e o funcionamento de cada componente principal.

O sistema permite que usuários gerenciem estoques residenciais (dispensas), cadastrem produtos e suas quantidades ideais e, a partir disso, o sistema gera listas de compras automáticas quando um item está abaixo do nível desejado.

## 2. Estrutura do Banco de Dados

O banco de dados, nomeado `tcc`, é o coração do sistema. Ele utiliza o MySQL e é composto por 6 tabelas principais que se relacionam para armazenar todas as informações.

Para uma refatoração em Python, é altamente recomendável o uso de um ORM (Object-Relational Mapper) como o **SQLAlchemy**. As tabelas abaixo podem ser mapeadas para classes Python, facilitando a manipulação dos dados de forma orientada a objetos.

---

### Tabela: `estoque`

Armazena as informações das dispensas ou locais de armazenamento. Cada usuário está associado a um estoque.

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `cod_estoque` | `bigint` (PK) | Identificador único do estoque (Auto-incremento). |
| `descricao` | `varchar(500)` | Nome ou descrição do estoque (ex: "Dispensa da Cozinha"). |

---

### Tabela: `item`

Catálogo mestre de todos os itens que podem existir no sistema.

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `cod_item` | `bigint` (PK) | Identificador único do item (Auto-incremento). |
| `descricao` | `varchar(300)` | Nome do item (ex: "Arroz Integral 1kg"). |
| `categoria` | `varchar(300)` | Categoria do item (ex: "Mercearia", "Limpeza"). |

---

### Tabela: `usuario`

Armazena os dados dos usuários do sistema.

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `cod_usuario` | `bigint` (PK) | Identificador único do usuário (Auto-incremento). |
| `nome` | `varchar(50)` | Nome do usuário. |
| `email` | `varchar(100)` | Email usado para login (deve ser único). |
| `senha` | `varchar(500)` | Senha do usuário, criptografada com `sha1`. |
| `permissao` | `varchar(500)` | Nível de acesso (`admin` ou `usuario`). |
| `cod_estoque` | `bigint` (FK) | Chave estrangeira que referencia `estoque.cod_estoque`. |

**Relacionamento:** `(N) usuario` -> `(1) estoque`. Vários usuários podem compartilhar o mesmo estoque.

---

### Tabela: `itemestoque`

Tabela de junção (pivot) que representa os itens presentes em um determinado estoque, com suas quantidades.

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `cod_item` | `bigint` (PK, FK) | Chave estrangeira que referencia `item.cod_item`. |
| `cod_estoque` | `bigint` (PK, FK) | Chave estrangeira que referencia `estoque.cod_estoque`. |
| `qtd_desejada` | `int` | Quantidade mínima que o usuário deseja ter deste item. |
| `qtd_estoque` | `int` | Quantidade atual do item no estoque. |

**Relacionamento:** `(N) item` <-> `(N) estoque`. Esta é a tabela central para a lógica de negócio.

---

### Tabela: `listacompra`

Armazena os cabeçalhos das listas de compras geradas.

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `cod_lista` | `bigint` (PK) | Identificador único da lista (Auto-incremento). |
| `cod_estoque` | `bigint` (FK) | Chave estrangeira que referencia `estoque.cod_estoque`. |
| `status` | `varchar(30)` | Status da lista (ex: "aberta", "fechada"). |

---

### Tabela: `listaitem`

Armazena os itens que compõem uma lista de compras específica.

| Coluna | Tipo | Descrição |
| :--- | :--- | :--- |
| `cod_item` | `bigint` (FK) | Chave estrangeira que referencia `item.cod_item`. |
| `cod_lista` | `bigint` (FK) | Chave estrangeira que referencia `listacompra.cod_lista`. |
| `qtd_desejada` | `int` | Quantidade a ser comprada. |
| `status` | `varchar(30)` | Status do item na lista (ex: "pendente", "comprado"). |

## 3. Lógica da Aplicação (API)

A lógica do backend está quase inteiramente concentrada no arquivo `processa.php`. Este arquivo funciona como um "mega-endpoint" que direciona a ação com base no `HTTP_REFERER` (a página que originou a requisição) e em parâmetros `GET` (`?acao=...`).

Ao refatorar para Python, cada bloco de `if` em `processa.php` deve ser transformado em um endpoint RESTful separado em um framework como **FastAPI** ou **Flask**.

### Arquivos de Configuração e Conexão

*   `config.php`: Define as credenciais do banco de dados. Em Python, isso deve ser gerenciado por variáveis de ambiente (usando `os.getenv`) ou um arquivo `.env`.
*   `connection.php`: Uma classe wrapper para `mysqli`. O ORM (SQLAlchemy) substituirá completamente a necessidade deste arquivo.

### Endpoints (Funcionalidades de `processa.php`)

A seguir, uma sugestão de como mapear a lógica de `processa.php` para uma API RESTful.

#### 3.1. Autenticação e Usuários

*   **Login de Usuário**
    *   **PHP:** `if($_SERVER['HTTP_REFERER'] === $url.'login.html')`
    *   **Lógica:** Verifica `email` e `senha` (com `sha1`) na tabela `usuario`. Se for válido, armazena dados do usuário na `$_SESSION`.
    *   **Endpoint Python Sugerido:** `POST /api/auth/login`
    *   **Payload:** `{ "email": "...", "senha": "..." }`
    *   **Retorno:** Em caso de sucesso, um token JWT (JSON Web Token) contendo `cod_usuario`, `cod_estoque` e `permissao`.

*   **Cadastro de Usuário (com/sem estoque novo)**
    *   **PHP:** `if($_SERVER['HTTP_REFERER'] === $url.'cadastroUsuario_semEstoque.html')` (cria estoque e usuário) e `if($_SERVER['HTTP_REFERER'] === $url.'cadastroUsuario_comEstoque.html')` (usa estoque existente).
    *   **Lógica:** Insere um novo `estoque` (se necessário) e depois insere o `usuario`, associando-o ao `cod_estoque`.
    *   **Endpoint Python Sugerido:** `POST /api/users`
    *   **Payload:** `{ "nome": "...", "email": "...", "senha": "...", "cod_estoque": (opcional), "descricao_estoque": (opcional) }`

*   **Listar/Buscar Usuários**
    *   **PHP:** `if($_GET['acao'] === 'listarUsuarios')` e `if($_SERVER['HTTP_REFERER'] === $url.'buscarUsuarioAvancado.html')`
    *   **Lógica:** Executa `SELECT` na tabela `usuario` com filtros.
    *   **Endpoint Python Sugerido:** `GET /api/users` com query params (ex: `?nome=...&email=...`).

#### 3.2. Gerenciamento de Itens e Estoque

*   **Adicionar um novo tipo de Item (Catálogo Geral)**
    *   **PHP:** `if($_SERVER['HTTP_REFERER'] === $url.'cadastroitem.html')`
    *   **Lógica:** Insere um novo registro na tabela `item`.
    *   **Endpoint Python Sugerido:** `POST /api/items/catalog`
    *   **Payload:** `{ "descricao": "...", "categoria": "..." }`

*   **Adicionar Item a um Estoque Específico**
    *   **PHP:** `if($_GET['acao'] === 'adicionaItem')`
    *   **Lógica:** Insere um registro na tabela de junção `itemestoque`, associando um `item` a um `estoque` com `qtd_desejada` e `qtd_estoque` iniciais.
    *   **Endpoint Python Sugerido:** `POST /api/stock/items`
    *   **Payload:** `{ "cod_item": ..., "qtd_desejada": ..., "qtd_estoque": ... }` (o `cod_estoque` viria do token do usuário).

*   **Visualizar/Listar Itens no Estoque do Usuário**
    *   **PHP:** `if($_GET['acao'] === 'acessaestoque')`
    *   **Lógica:** Faz um `SELECT` com `INNER JOIN` entre `itemestoque` e `item` para o `cod_estoque` do usuário logado.
    *   **Endpoint Python Sugerido:** `GET /api/stock/items`

*   **Atualizar Quantidade de um Item no Estoque**
    *   **PHP:** `if($_GET['acao'] === 'atualizaItem')`
    *   **Lógica:** Executa um `UPDATE` na tabela `itemestoque` para alterar `qtd_desejada` e/ou `qtd_estoque`.
    *   **Endpoint Python Sugerido:** `PUT /api/stock/items/{cod_item}`
    *   **Payload:** `{ "qtd_desejada": ..., "qtd_estoque": ... }`

#### 3.3. Lógica Principal: Lista de Compras

*   **Gerar Lista de Compras**
    *   **PHP:** `if($_GET['acao'] === 'novalistacompra')`
    *   **Lógica:** Esta é a funcionalidade central. O script executa a query:
        ```sql
        SELECT ... FROM itemestoque 
        INNER JOIN item ON item.cod_item = itemestoque.cod_item 
        WHERE itemestoque.cod_estoque = ? 
        AND itemestoque.qtd_desejada > itemestoque.qtd_estoque;
        ```
        Para cada resultado, ele calcula a `qtd_a_comprar` (`qtd_desejada - qtd_estoque`) e exibe na tela.
    *   **Endpoint Python Sugerido:** `GET /api/shopping-list`
    *   **Retorno:** Um array de objetos, onde cada objeto representa um item a ser comprado: `{ "cod_item": ..., "descricao": "...", "qtd_a_comprar": ... }`.

*   **Registrar Compra de um Item**
    *   **PHP:** `if($_GET['acao'] === 'compraItem')`
    *   **Lógica:** Recebe a quantidade comprada (`qtd_comprar`) e atualiza a `qtd_estoque` do item na tabela `itemestoque` (`qtd_estoque = qtd_estoque + qtd_comprar`).
    *   **Endpoint Python Sugerido:** `POST /api/shopping-list/buy`
    *   **Payload:** `{ "cod_item": ..., "qtd_comprada": ... }`

### 4. Frontend

Os arquivos `.html` são as interfaces de usuário. Eles contêm formulários HTML simples que enviam dados via `POST` ou links que acionam ações via `GET` para o `processa.php`.

Na refatoração para Python com uma API RESTful, o frontend seria idealmente desacoplado e reescrito usando um framework moderno (como React, Vue ou Angular), que consumiria os endpoints definidos acima.

### 5. Arquivo de Saída (Logout)

*   `saida.php`: Destrói a sessão PHP.
*   **Endpoint Python Sugerido:** `POST /api/auth/logout`. Este endpoint invalidaria o token JWT do lado do cliente (ou em uma blocklist do lado do servidor, se necessário).
