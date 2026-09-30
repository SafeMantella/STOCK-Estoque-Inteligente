// Frontend servido à parte na porta 3000 (python -m http.server 3000): a API fica
// no mesmo host, porta 8000. Em qualquer outra porta (ex.: frontend servido pelo
// próprio FastAPI em :8000 ou atrás de um proxy) usa o caminho relativo /api.
const DEFAULT_API_BASE =
  (typeof window !== 'undefined' && window.location.port === '3000')
    ? `${window.location.protocol}//${window.location.hostname}:8000/api`
    : '/api';
const API_BASE =
  (typeof window !== 'undefined' && window.__API_BASE__) ||
  (typeof document !== 'undefined' && document.querySelector('meta[name="api-base"]')?.content) ||
  DEFAULT_API_BASE;

async function apiCall(method, path, body = null) {
  const token = localStorage.getItem('token');
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = 'Bearer ' + token;

  const opts = { method, headers };
  if (body) opts.body = JSON.stringify(body);

  let res;
  try {
    res = await fetch(API_BASE + path, opts);
  } catch (_) {
    throw new Error('Não foi possível conectar ao servidor. Verifique sua conexão e tente de novo.');
  }

  // 401 com sessão ativa = token expirado -> volta ao login.
  // Sem token (ex.: senha errada no login) cai no tratamento de erro abaixo.
  if (res.status === 401 && token) {
    localStorage.clear();
    window.location.href = '/index.html';
    return;
  }

  const data = await res.json().catch(() => null);
  if (!res.ok) {
    // O backend devolve 'detail' em português (validação: uma frase por campo em 'erros')
    const msg = data?.detail || 'Algo deu errado (erro ' + res.status + '). Tente de novo.';
    const err = new Error(Array.isArray(msg) ? msg.map(e => e.msg).join(' ') : msg);
    err.erros = data?.erros || [];
    throw err;
  }
  return data;
}

// Escapa texto vindo da API antes de interpolar em innerHTML (evita XSS)
function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}

function showMsg(text, type = 'danger') {
  const el = document.getElementById('msg-area');
  if (!el) return;

  // Clear previous message
  el.textContent = '';

  // Create alert container
  const alertDiv = document.createElement('div');
  alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
  alertDiv.setAttribute('role', 'alert');

  // Add message text safely
  const messageSpan = document.createElement('span');
  messageSpan.textContent = text;
  alertDiv.appendChild(messageSpan);

  // Add close button
  const closeBtn = document.createElement('button');
  closeBtn.type = 'button';
  closeBtn.className = 'btn-close';
  closeBtn.setAttribute('data-bs-dismiss', 'alert');
  alertDiv.appendChild(closeBtn);

  el.appendChild(alertDiv);
}
