"""Fábrica responsável por selecionar provedores de modelos de linguagem."""

from __future__ import annotations

from typing import Final

from src.config import CONFIG, ConfiguracaoLLM
from src.llm.base import ProvedorLLM


PROVEDOR_GOOGLE: Final[str] = "google"
PROVEDOR_OPENAI: Final[str] = "openai"
PROVEDOR_OPENROUTER: Final[str] = "openrouter"

PROVEDORES_SUPORTADOS: Final[frozenset[str]] = frozenset(
    {PROVEDOR_GOOGLE, PROVEDOR_OPENAI, PROVEDOR_OPENROUTER}
)


class ErroFabricaLLM(ValueError):
    """Representa uma falha na seleção ou criação de um provedor LLM."""


def _criar_provedor_google(configuracao: ConfiguracaoLLM) -> ProvedorLLM:
    """Cria o provedor Google a partir da configuração do modelo ativo."""
    modelo = configuracao.modelo_ativo

    try:
        from src.llm.google import GoogleProvider
    except ModuleNotFoundError as erro:
        raise ErroFabricaLLM(
            "O provedor Google ainda não foi implementado."
        ) from erro

    return GoogleProvider(
        model_name=modelo.model_name,
        api_key=modelo.api_key,
        request_delay_seconds=configuracao.delays.request_delay_seconds,
    )


def _criar_provedor_openai(configuracao: ConfiguracaoLLM) -> ProvedorLLM:
    """Cria o provedor OpenAI a partir da configuração do modelo ativo."""
    modelo = configuracao.modelo_ativo

    try:
        from src.llm.openai import OpenAIProvider
    except ModuleNotFoundError as erro:
        raise ErroFabricaLLM(
            "O provedor OpenAI ainda não foi implementado."
        ) from erro

    return OpenAIProvider(
        model_name=modelo.model_name,
        api_key=modelo.api_key,
        request_delay_seconds=configuracao.delays.request_delay_seconds,
        base_url="https://api.groq.com/openai/v1/"
    )


def _criar_provedor_openrouter(
    configuracao: ConfiguracaoLLM,
) -> ProvedorLLM:
    """Cria o provedor DeepSeek configurado para a API OpenRouter."""
    modelo = configuracao.modelo_ativo

    try:
        from src.llm.deepseek import DeepSeekProvider
    except ModuleNotFoundError as erro:
        raise ErroFabricaLLM(
            "O provedor DeepSeek via OpenRouter ainda não foi implementado."
        ) from erro

    return DeepSeekProvider(
        model_name=modelo.model_name,
        api_key=modelo.api_key,
        request_delay_seconds=configuracao.delays.request_delay_seconds,
    )


def criar_provedor_llm(
    configuracao: ConfiguracaoLLM = CONFIG.llm,
) -> ProvedorLLM:
    """Cria o provedor correspondente ao modelo ativo."""
    modelo = configuracao.modelo_ativo
    provedor = modelo.provider.strip().lower()

    if provedor == PROVEDOR_GOOGLE:
        return _criar_provedor_google(configuracao)

    if provedor == PROVEDOR_OPENAI:
        return _criar_provedor_openai(configuracao)

    if provedor == PROVEDOR_OPENROUTER:
        return _criar_provedor_openrouter(configuracao)

    raise ErroFabricaLLM(
        f"Provedor LLM não suportado: {modelo.provider!r}. "
        f"Provedores disponíveis: {sorted(PROVEDORES_SUPORTADOS)}."
    )