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

// extra: opções do fetch (ex.: { keepalive: true } para terminar uma ação ao sair da página)
async function apiCall(method, path, body = null, extra = {}) {
  const token = localStorage.getItem('token');
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = 'Bearer ' + token;

  const opts = { method, headers, ...extra };
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

// Aviso (toast) fixo no rodapé da tela, visível mesmo com a página rolada (celular).
// Um aviso por vez; some sozinho (erros ficam mais tempo) ou pelo "×".
//   showMsg(texto, 'danger' | 'success' | 'info' | 'warning', { duracao, acao: { texto, onClick } })
//   duracao em ms; 0 = só fecha pelo "×". Devolve { fechar }.
let _toastAtual = null;
function showMsg(text, type = 'danger', opts = {}) {
  let area = document.getElementById('toast-area');
  if (!area) {
    area = document.createElement('div');
    area.id = 'toast-area';
    area.className = 'toast-area';
    area.setAttribute('aria-live', 'polite');
    document.body.appendChild(area);
  }
  if (_toastAtual) _toastAtual.fechar();
  area.textContent = '';

  const toast = document.createElement('div');
  toast.className = 'toast-stock toast-' + type;
  toast.setAttribute('role', type === 'danger' || type === 'warning' ? 'alert' : 'status');

  const texto = document.createElement('span');
  texto.className = 'toast-texto';
  texto.textContent = text;
  toast.appendChild(texto);

  let timer = null;
  function fechar() {
    clearTimeout(timer);
    toast.remove();
    if (_toastAtual === handle) _toastAtual = null;
  }
  const handle = { fechar };

  if (opts.acao) {
    const acao = document.createElement('button');
    acao.type = 'button';
    acao.className = 'toast-acao';
    acao.textContent = opts.acao.texto;
    acao.addEventListener('click', () => { fechar(); opts.acao.onClick(); });
    toast.appendChild(acao);
  }

  const fecharBtn = document.createElement('button');
  fecharBtn.type = 'button';
  fecharBtn.className = 'toast-fechar';
  fecharBtn.setAttribute('aria-label', 'Fechar aviso');
  fecharBtn.textContent = '×';
  fecharBtn.addEventListener('click', fechar);
  toast.appendChild(fecharBtn);

  area.appendChild(toast);
  const duracao = opts.duracao ?? (type === 'success' ? 4000 : 8000);
  if (duracao > 0) timer = setTimeout(fechar, duracao);
  _toastAtual = handle;
  return handle;
}
