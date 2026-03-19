const API_BASE = 'http://localhost:8000/api';

async function apiCall(method, path, body = null) {
  const token = localStorage.getItem('token');
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = 'Bearer ' + token;

  const opts = { method, headers };
  if (body) opts.body = JSON.stringify(body);

  const res = await fetch(API_BASE + path, opts);

  if (res.status === 401) {
    localStorage.clear();
    window.location.href = '/index.html';
    return;
  }

  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const msg = data?.detail || 'Erro desconhecido';
    throw new Error(Array.isArray(msg) ? msg.map(e => e.msg).join(', ') : msg);
  }
  return data;
}

function showMsg(text, type = 'danger') {
  const el = document.getElementById('msg-area');
  if (!el) return;
  el.innerHTML = `<div class="alert alert-${type} alert-dismissible fade show" role="alert">
    ${text}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  </div>`;
}
