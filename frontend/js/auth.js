// Verifica autenticação em páginas protegidas.
// Chame requireAuth() no topo do script de cada página protegida.
function requireAuth() {
  if (!localStorage.getItem('token')) {
    window.location.href = '/index.html';
  }
}

function getUser() {
  return {
    token:       localStorage.getItem('token'),
    nome:        localStorage.getItem('nome'),
    permissao:   localStorage.getItem('permissao'),
    cod_estoque: localStorage.getItem('cod_estoque'),
    cod_usuario: localStorage.getItem('cod_usuario'),
  };
}

function isAdmin() {
  return localStorage.getItem('permissao') === 'admin';
}

function logout() {
  localStorage.clear();
  window.location.href = '/index.html';
}

// Redireciona para menu se já estiver logado (usar na página de login)
function redirectIfLoggedIn() {
  if (localStorage.getItem('token')) {
    window.location.href = '/menu.html';
  }
}
