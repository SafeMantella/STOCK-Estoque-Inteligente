"""Mensagens de validação em português (substitui as mensagens padrão do Pydantic, em inglês)."""
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

ROTULOS = {
    "nome": "Nome",
    "email": "E-mail",
    "senha": "Senha",
    "descricao": "Descrição",
    "categoria": "Categoria",
    "descricao_estoque": "Nome do estoque",
    "codigo_convite": "Código de convite",
    "cod_item": "Item",
    "qtd_desejada": "Quantidade mínima",
    "qtd_estoque": "Quantidade em casa",
    "qtd_comprada": "Quantidade comprada",
    "delta": "Ajuste",
}


def _campo(loc) -> str:
    # loc = ("body", "senha") | ("query", "cod_item") | ("body",)
    partes = [str(p) for p in loc if p not in ("body", "query", "path")]
    return partes[-1] if partes else ""


def mensagem(erro: dict) -> str:
    campo = _campo(erro.get("loc", ()))
    rotulo = ROTULOS.get(campo, campo.replace("_", " ").capitalize() or "Dados")
    tipo = erro.get("type", "")
    ctx = erro.get("ctx") or {}

    if tipo == "missing":
        return f"{rotulo} é obrigatório."
    if tipo == "string_too_short":
        minimo = ctx.get("min_length", 1)
        if minimo <= 1:
            return f"{rotulo} não pode ficar em branco."
        return f"{rotulo} deve ter pelo menos {minimo} caracteres."
    if tipo == "string_too_long":
        return f"{rotulo} deve ter no máximo {ctx.get('max_length')} caracteres."
    if campo == "email" or tipo == "value_error" and "email" in str(erro.get("msg", "")).lower():
        return "Informe um e-mail válido (ex.: nome@exemplo.com.br)."
    if tipo in ("int_parsing", "int_type", "int_from_float"):
        return f"{rotulo} deve ser um número inteiro."
    if tipo == "greater_than_equal":
        if ctx.get("ge") == 0:
            return f"{rotulo} não pode ser negativa." if rotulo.startswith("Quantidade") else f"{rotulo} não pode ser negativo."
        return f"{rotulo} deve ser no mínimo {ctx.get('ge')}."
    if tipo == "greater_than":
        return f"{rotulo} deve ser maior que {ctx.get('gt')}."
    if tipo in ("less_than_equal", "less_than"):
        return f"{rotulo} deve ser no máximo {ctx.get('le', ctx.get('lt'))}."
    if tipo in ("string_type",):
        return f"{rotulo} deve ser um texto."
    if tipo in ("json_invalid", "model_attributes_type", "dict_type"):
        return "Não foi possível ler os dados enviados."
    return f"{rotulo} é inválido."


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    erros = [{"campo": _campo(e.get("loc", ())), "mensagem": mensagem(e)} for e in exc.errors()]
    # detail em texto (compatível com o frontend); 'erros' traz a mensagem de cada campo
    unicas = list(dict.fromkeys(e["mensagem"] for e in erros))
    return JSONResponse(status_code=422, content={"detail": " ".join(unicas), "erros": erros})
