"""Limite de tentativas ERRADAS (login e códigos de convite) contra força bruta.

Regra: no máximo 5 tentativas erradas por minuto por e-mail e 20 por IP (uma casa
inteira pode estar no mesmo Wi-Fi/IP). Configurável: RATE_LIMIT_EMAIL, RATE_LIMIT_IP,
RATE_LIMIT_JANELA (segundos). Passando disso a API responde 429 com "Muitas tentativas. Tente de novo em ..." e
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

MAX_TENTATIVAS = 5  # padrão do Limitador para chaves sem limite próprio


def _int_env(nome, padrao):
    try:
        return max(int(os.getenv(nome, "") or padrao), 1)
    except ValueError:
        return padrao


def limite_email() -> int:
    return _int_env("RATE_LIMIT_EMAIL", 5)


def limite_ip() -> int:
    return _int_env("RATE_LIMIT_IP", 20)


JANELA_SEGUNDOS = _int_env("RATE_LIMIT_JANELA", 60)


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

    @staticmethod
    def _separar(chave):
        # chave pode ser "nome" (usa max_tentativas) ou ("nome", limite_próprio)
        return chave if isinstance(chave, tuple) else (chave, None)

    def espera(self, chaves) -> float:
        """Segundos até poder tentar de novo (0 = liberado)."""
        agora = self.relogio()
        with self._lock:
            espera = 0.0
            for item in chaves:
                chave, maximo = self._separar(item)
                maximo = maximo or self.max_tentativas
                fila = self._recentes(chave, agora)
                if fila is not None and len(fila) >= maximo:
                    # libera quando sobrarem menos que 'maximo' falhas na janela
                    espera = max(espera, fila[len(fila) - maximo] + self.janela - agora)
            return espera

    def registrar_falha(self, chaves) -> None:
        agora = self.relogio()
        with self._lock:
            if len(self._falhas) > 50_000:  # limpeza ocasional (memória limitada)
                for chave in list(self._falhas):
                    self._recentes(chave, agora)
            for item in chaves:
                chave, _ = self._separar(item)
                self._falhas.setdefault(chave, deque()).append(agora)

    def zerar(self, chaves=None) -> None:
        with self._lock:
            if chaves is None:
                self._falhas.clear()
            else:
                for item in chaves:
                    self._falhas.pop(self._separar(item)[0], None)


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


def chaves(request: Request, acao: str, email: str | None) -> list[tuple[str, int]]:
    """Chaves com o limite de cada uma: por IP (padrão 20/min) e por e-mail (padrão 5/min)."""
    ks = [(f"{acao}:ip:{ip_do_cliente(request)}", limite_ip())]
    if email:
        ks.append((f"{acao}:email:{email.strip().lower()}", limite_email()))
    return ks


def _texto_espera(segundos: int) -> str:
    # Arredonda para "1 minuto" perto do minuto cheio (a conta exata vai no Retry-After)
    if segundos > 50:
        minutos = math.ceil(segundos / 60)
        return "1 minuto" if minutos == 1 else f"{minutos} minutos"
    return "1 segundo" if segundos == 1 else f"{segundos} segundos"


def checar(ks: list) -> None:
    """429 se alguma das chaves passou do limite (chamar ANTES de conferir senha/código)."""
    espera = limitador.espera(ks)
    if espera > 0:
        segundos = max(math.ceil(espera), 1)
        raise HTTPException(
            status_code=429,
            detail=f"Muitas tentativas. Tente de novo em {_texto_espera(segundos)}.",
            headers={"Retry-After": str(segundos)},
        )


def registrar_falha(ks: list) -> None:
    limitador.registrar_falha(ks)
