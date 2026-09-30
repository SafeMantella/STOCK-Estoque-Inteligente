const CATEGORIAS = [
  'Higiene e Limpeza', 'Bebidas', 'Adega', 'Molhos e Óleos', 'Açúcares e Doces', 'Laticínios',
  'Carnes e Ovos', 'Leguminosas/Hortaliças/Raízes/Tubérculos', 'Frutas', 'Cereais e Mel',
  'Pão e Massas', 'Outros',
];

// Preenche um <select> com as categorias (inclui o valor atual se for uma categoria antiga)
function preencherCategorias(select, atual = '') {
  select.replaceChildren();
  const vazio = new Option('Selecione...', '');
  select.add(vazio);
  const lista = atual && !CATEGORIAS.includes(atual) ? [...CATEGORIAS, atual] : CATEGORIAS;
  lista.forEach(c => select.add(new Option(c, c, false, c === atual)));
}
