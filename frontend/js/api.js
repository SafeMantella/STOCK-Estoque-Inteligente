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
    err.status = res.status;
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

// Mensagem para 404 em item que outro morador excluiu (em outra aba/celular)
const MSG_ITEM_EXCLUIDO = 'Esse item foi excluído por alguém da casa.';

// Avisos (toasts) fixos no rodapé da tela, visíveis mesmo com a página rolada (celular).
//   showMsg(texto, 'danger' | 'success' | 'info' | 'warning', { duracao, acao: { texto, onClick } })
//   duracao em ms; 0 = só fecha pelo "×". Devolve { fechar }.
// - Aviso comum: um por vez (um novo substitui o anterior); sucesso some em 4 s, erro em 8 s.
// - Aviso com ação (ex.: "Desfazer"): empilha, cada um independente (até 3 visíveis; o 4º
//   tira o mais antigo); um aviso comum nunca substitui um aviso com ação.
// Enquanto houver aviso, a página ganha espaço embaixo do tamanho dos avisos, para nada
// ficar coberto (se a pessoa estava no fim da página, a tela acompanha).
const MAX_TOASTS_ACAO = 3;
let _toastComum = null;
const _toastsAcao = [];

function _areaToasts() {
  let area = document.getElementById('toast-area');
  if (!area) {
    area = document.createElement('div');
    area.id = 'toast-area';
    area.className = 'toast-area';
    area.setAttribute('aria-live', 'polite');
    document.body.appendChild(area);
    const ajustar = () => {
      const noFim = window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4;
      const antes = parseFloat(document.body.style.paddingBottom) || 0;
      const altura = area.childElementCount ? area.offsetHeight + 12 : 0;
      document.body.style.paddingBottom = altura + 'px';
      if (noFim && altura > antes) window.scrollBy(0, altura - antes);
    };
    if (window.ResizeObserver) new ResizeObserver(ajustar).observe(area);
    new MutationObserver(ajustar).observe(area, { childList: true });
  }
  return area;
}

function showMsg(text, type = 'danger', opts = {}) {
  const area = _areaToasts();
  const comAcao = !!opts.acao;

  const toast = document.createElement('div');
  toast.className = 'toast-stock toast-' + type;
  toast.setAttribute('role', type === 'danger' || type === 'warning' ? 'alert' : 'status');

  const texto = document.createElement('span');
  texto.className = 'toast-texto';
  texto.textContent = text;
  toast.appendChild(texto);

  let timer = null;
  const handle = { fechar };
  function fechar() {
    clearTimeout(timer);
    toast.remove();
    if (_toastComum === handle) _toastComum = null;
    const i = _toastsAcao.indexOf(handle);
    if (i >= 0) _toastsAcao.splice(i, 1);
  }

  if (comAcao) {
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

  if (comAcao) {
    while (_toastsAcao.length >= MAX_TOASTS_ACAO) _toastsAcao[0].fechar();
    _toastsAcao.push(handle);
    // avisos com ação ficam acima do aviso comum
    area.insertBefore(toast, _toastComum ? area.querySelector('.toast-comum') : null);
  } else {
    if (_toastComum) _toastComum.fechar();
    toast.classList.add('toast-comum');
    _toastComum = handle;
    area.appendChild(toast);
  }
  const duracao = opts.duracao ?? (comAcao ? 8000 : type === 'success' ? 4000 : 8000);
  if (duracao > 0) timer = setTimeout(fechar, duracao);
  return handle;
}
