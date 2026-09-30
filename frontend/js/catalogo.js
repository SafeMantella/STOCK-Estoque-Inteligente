// Catálogo da casa em cartões (Listar Itens e Buscar Itens).
// Cada item mostra "Mínimo que quero ter" / "Tenho agora" e "Adicionar ao estoque";
// o que já está no estoque aparece marcado, sem campos.
async function codigosNoEstoque() {
  try {
    return new Set((await apiCall('GET', '/stock')).map(i => i.cod_item));
  } catch (_) {
    return new Set();
  }
}

function _el(tag, className, text) {
  const e = document.createElement(tag);
  if (className) e.className = className;
  if (text !== undefined) e.textContent = text;
  return e;
}

function _campoQtd(labelText, min) {
  const div = _el('div', 'col-6');
  const input = _el('input', 'form-control w-100');
  input.type = 'number';
  input.min = String(min);
  input.inputMode = 'numeric';
  input.id = 'q' + Math.random().toString(36).slice(2);
  const label = _el('label', 'form-label mb-0 small', labelText);
  label.htmlFor = input.id;
  div.append(label, input);
  return { div, input };
}

function _marcarNoEstoque(body) {
  const ok = _el('div', 'd-flex flex-wrap align-items-center gap-2 mt-auto');
  ok.appendChild(_el('span', 'badge text-bg-success', 'Já está no seu estoque'));
  const link = _el('a', 'small', 'Ver em Meu Estoque');
  link.href = 'estoque.html';
  ok.appendChild(link);
  body.appendChild(ok);
}

function cardCatalogo(item, noEstoque) {
  const col = _el('div', 'col');
  const card = _el('div', 'card h-100 card-compra');
  const body = _el('div', 'card-body d-flex flex-column gap-2');
  const topo = _el('div', 'text-break');
  topo.appendChild(_el('h2', 'h5 mb-0 text-break', item.descricao));
  topo.appendChild(_el('small', 'text-muted fw-normal', item.categoria));
  body.appendChild(topo);

  if (noEstoque.has(item.cod_item)) {
    _marcarNoEstoque(body);
  } else {
    const form = _el('form', 'd-flex flex-column gap-2 mt-auto');
    form.noValidate = true;
    const linha = _el('div', 'row g-2');
    const minimo = _campoQtd('Mínimo que quero ter', 1);
    const tenho = _campoQtd('Tenho agora', 0);
    linha.append(minimo.div, tenho.div);
    const btn = _el('button', 'btn btn-outline-success btn-toque w-100', 'Adicionar ao estoque');
    btn.type = 'submit';
    form.append(linha, btn);
    form.addEventListener('submit', async e => {
      e.preventDefault();
      const qtd_desejada = parseInt(minimo.input.value, 10);
      const qtd_estoque = parseInt(tenho.input.value, 10);
      if (!qtd_desejada || qtd_desejada <= 0) { showMsg('Informe o mínimo que quer ter (maior que zero).'); minimo.input.focus(); return; }
      if (isNaN(qtd_estoque) || qtd_estoque < 0) { showMsg('Informe quanto você tem agora (0 ou mais).'); tenho.input.focus(); return; }
      btn.disabled = true;
      try {
        await apiCall('POST', '/stock', { cod_item: item.cod_item, qtd_desejada, qtd_estoque });
        noEstoque.add(item.cod_item);
        form.remove();
        _marcarNoEstoque(body);
        showMsg('"' + item.descricao + '" adicionado ao seu estoque.', 'success');
      } catch (err) {
        btn.disabled = false;
        if (err.status === 404) { // outro morador excluiu o item do catálogo
          col.remove();
          showMsg(MSG_ITEM_EXCLUIDO, 'warning');
          return;
        }
        showMsg(err.message);
      }
    });
    body.appendChild(form);
  }
  card.appendChild(body);
  col.appendChild(card);
  return col;
}

// Preenche o container com os cartões e o texto de contagem; devolve o número de itens
async function renderCatalogo(container, contagemEl, itens, textoVazio) {
  const noEstoque = await codigosNoEstoque();
  // Primeiro o que ainda não está no estoque; depois por nome
  itens = [...itens].sort((a, b) =>
    (noEstoque.has(a.cod_item) - noEstoque.has(b.cod_item)) || a.descricao.localeCompare(b.descricao, 'pt-BR'));
  container.replaceChildren(...itens.map(i => cardCatalogo(i, noEstoque)));
  contagemEl.textContent = itens.length
    ? itens.length + (itens.length === 1 ? ' item' : ' itens') + ' no catálogo da casa.'
    : textoVazio;
  return itens.length;
}
