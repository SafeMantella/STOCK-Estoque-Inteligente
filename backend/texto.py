import unicodedata


def normalizar_nome(texto: str) -> str:
    """Chave para detectar nomes duplicados: sem acentos, minúsculo e espaços colapsados.

    'Café  500g' -> 'cafe 500g'
    """
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFKD", texto or "") if not unicodedata.combining(c)
    )
    return " ".join(sem_acento.lower().split())
