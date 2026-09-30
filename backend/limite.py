"""Limite de tentativas ERRADAS (login e códigos de convite) contra força bruta.

Regra: no máximo 5 tentativas erradas por minuto por IP e, separadamente, por e-mail.
Passando disso a API responde 429 com "Muitas tentativas. Tente de novo em ..." e
o cabeçalho Retry-After (segundos). Tentativas certas não contam.

Guardado em memória: vale para UMA instância da aplicação e zera quando ela reinicia
(ver DEPLOY.md). O IP vem da conexão; X-Forwarded-For só é usado com TRUST_PROXY
(número de proxies confiáveis na frente da app, ex.: TRUST_PROXY=1 no Render/Railway/Fly).
"""
import math
import os
import threading
import time
from collections import deque

from fastapi import HTTPException, Request

MAX_TENTATIVAS = 5
JANELA_SEGUNDOS = 60


class Limitador:
    def __init__(self, max_tentativas=MAX_TENTATIVAS, janela=JANELA_SEGUNDOS, relogio=time.monotonic):
        self.max_tentativas = max_tentativas
        self.janela = janela
        self.relogio = relogio
        self._falhas: dict[str, deque] = {}
        self._lock = threading.Lock()

    def _recentes(self, chave, agora):
        fila = self._falhas.get(chave)
        if fila is None:
            return None
        while fila and fila[0] <= agora - self.janela:
            fila.popleft()
        if not fila:
            del self._falhas[chave]
            return None
        return fila

    def espera(self, chaves) -> float:
        """Segundos até poder tentar de novo (0 = liberado)."""
        agora = self.relogio()
        with self._lock:
            espera = 0.0
            for chave in chaves:
                fila = self._recentes(chave, agora)
                if fila is not None and len(fila) >= self.max_tentativas:
                    espera = max(espera, fila[0] + self.janela - agora)
            return espera

    def registrar_falha(self, chaves) -> None:
        agora = self.relogio()
        with self._lock:
            if len(self._falhas) > 50_000:  # limpeza ocasional (memória limitada)
                for chave in list(self._falhas):
                    self._recentes(chave, agora)
            for chave in chaves:
                self._falhas.setdefault(chave, deque()).append(agora)

    def zerar(self, chaves=None) -> None:
        with self._lock:
            if chaves is None:
                self._falhas.clear()
            else:
                for chave in chaves:
                    self._falhas.pop(chave, None)


limitador = Limitador()


def _proxies_confiaveis() -> int:
    valor = os.getenv("TRUST_PROXY", "").strip().lower()
    if valor in ("", "0", "false", "no", "nao", "não"):
        return 0
    if valor in ("true", "yes", "sim"):
        return 1
    try:
        return max(int(valor), 0)
    except ValueError:
        return 0


def ip_do_cliente(request: Request) -> str:
    saltos = _proxies_confiaveis()
    if saltos:
        # Cada proxy acrescenta o IP de quem o chamou no fim; o cliente pode forjar o começo.
        # Com N proxies confiáveis, o IP real é o N-ésimo a partir do fim.
        ips = [p.strip() for p in request.headers.get("x-forwarded-for", "").split(",") if p.strip()]
        if ips:
            return ips[-saltos] if len(ips) >= saltos else ips[0]
    return request.client.host if request.client else "desconhecido"


def chaves(request: Request, acao: str, email: str | None) -> list[str]:
    ks = [f"{acao}:ip:{ip_do_cliente(request)}"]
    if email:
        ks.append(f"{acao}:email:{email.strip().lower()}")
    return ks


def _texto_espera(segundos: int) -> str:
    # Arredonda para "1 minuto" perto do minuto cheio (a conta exata vai no Retry-After)
    if segundos > 50:
        minutos = math.ceil(segundos / 60)
        return "1 minuto" if minutos == 1 else f"{minutos} minutos"
    return "1 segundo" if segundos == 1 else f"{segundos} segundos"


def checar(ks: list[str]) -> None:
    """429 se alguma das chaves passou do limite (chamar ANTES de conferir senha/código)."""
    espera = limitador.espera(ks)
    if espera > 0:
        segundos = max(math.ceil(espera), 1)
        raise HTTPException(
            status_code=429,
            detail=f"Muitas tentativas. Tente de novo em {_texto_espera(segundos)}.",
            headers={"Retry-After": str(segundos)},
        )


def registrar_falha(ks: list[str]) -> None:
    limitador.registrar_falha(ks)
