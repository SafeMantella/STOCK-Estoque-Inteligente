# Frontend Guidelines

## Page Structure

Every HTML page follows this pattern:

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Stock :: Page Name</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="../css/custom.css" rel="stylesheet">
</head>
<body>
  <!-- content -->
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
  <script src="../js/api.js"></script>
  <script src="../js/auth.js"></script>
  <script>
    requireAuth(); // protect page
    // page logic
  </script>
</body>
</html>
```

> **Note**: Pages inside `pages/` use `../js/` and `../css/` relative paths. Root-level pages (`index.html`, `menu.html`) use `js/` and `css/` directly.

## API Calls

```javascript
// GET request
const items = await apiCall('GET', '/stock');

// POST request
const result = await apiCall('POST', '/auth/login', { email, senha });

// PUT request
await apiCall('PUT', `/stock/${codItem}`, { qtd_desejada: 5 });
```

All calls automatically:
- Include JWT token from localStorage
- Redirect to login on 401
- Parse error messages (supports both string and array `detail`)

## User Feedback

```javascript
showMsg('Operação realizada com sucesso!', 'success'); // toast verde, some em 4 s
showMsg('Algo deu errado');                             // padrão: erro, some em 8 s
showMsg('Item excluído.', 'success', { duracao: 5000, acao: { texto: 'Desfazer', onClick } });
```

Fixed toast at the bottom of the viewport (created on demand in `#toast-area`); no markup needed.

## Auth Helpers

```javascript
requireAuth();          // Redirect to login if no token
const user = getUser(); // { token, nome, permissao, cod_estoque, cod_usuario }
isAdmin();              // true if permissao === 'admin'
logout();               // Clear localStorage, redirect to login
redirectIfLoggedIn();   // Used on login page only
```

## Design System

- Use `.btn-stock` for primary green action buttons
- Use `.btn-outline-success` for secondary/menu buttons
- All forms use Bootstrap `.form-control`, `.form-label`, `.mb-3`
- Tables use `.table .table-bordered .table-striped`
- Layout: `.container-fluid` > `.row` > `.col-md-*`
- Feedback: `showMsg()` toast at the bottom of the screen (no `#msg-area` anymore)

## Admin vs User Content

```javascript
if (isAdmin()) {
  document.getElementById('admin-section').style.display = 'block';
}
```

Admin-only UI elements are hidden by default with `style="display:none;"` and revealed via JS.
