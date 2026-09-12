"""Sanitização e validação das respostas produzidas por modelos de linguagem."""

from __future__ import annotations

import json
from typing import Any

from src.prompts.construtor import CLASSES_PENAIS


class ErroRespostaLLM(ValueError):
    """Representa uma resposta inválida produzida por uma LLM."""


def _validar_texto_resposta(texto: Any) -> str:
    """Valida o texto bruto recebido da LLM.

    Args:
        texto: Resposta bruta produzida pelo modelo.

    Returns:
        Texto da resposta sem espaços externos.

    Raises:
        ErroRespostaLLM: Se o valor não for uma string não vazia.
    """
    if not isinstance(texto, str) or not texto.strip():
        raise ErroRespostaLLM(
            "A resposta da LLM deve ser uma string não vazia."
        )

    return texto.strip()


def _remover_marcadores_markdown(texto: str) -> str:
    """Remove marcadores Markdown de blocos JSON.

    A função remove somente marcadores que envolvem toda a resposta.
    Textos adicionais fora do JSON permanecem para serem rejeitados pelo
    parser, evitando aceitar respostas ambíguas.

    Args:
        texto: Resposta textual já validada.

    Returns:
        Conteúdo sem os marcadores externos de bloco de código.
    """
    linhas = texto.splitlines()

    if len(linhas) >= 2:
        primeira_linha = linhas[0].strip().lower()
        ultima_linha = linhas[-1].strip()

        if primeira_linha in {"```", "```json"} and ultima_linha == "```":
            return "\n".join(linhas[1:-1]).strip()

    return texto


def _validar_campo_textual(
    resposta: dict[str, Any],
    nome_campo: str,
) -> str:
    """Valida um campo textual obrigatório da resposta.

    Args:
        resposta: Objeto JSON convertido em dicionário.
        nome_campo: Nome do campo obrigatório.

    Returns:
        Conteúdo textual normalizado do campo.

    Raises:
        ErroRespostaLLM: Se o campo estiver ausente, não for textual ou
            estiver vazio.
    """
    valor = resposta.get(nome_campo)

    if not isinstance(valor, str) or not valor.strip():
        raise ErroRespostaLLM(
            f"O campo '{nome_campo}' deve ser uma string não vazia."
        )

    return valor.strip()


def _validar_resposta_estruturada(
    resposta: Any,
) -> dict[str, str]:
    """Valida a estrutura esperada da resposta da LLM.

    Args:
        resposta: Valor convertido a partir do JSON recebido.

    Returns:
        Dicionário contendo `classe` e `justificativa` validadas.

    Raises:
        ErroRespostaLLM: Se a estrutura ou algum campo for inválido.
    """
    if not isinstance(resposta, dict):
        raise ErroRespostaLLM(
            "A resposta da LLM deve ser um objeto JSON."
        )

    classe = _validar_campo_textual(resposta, "classe")
    justificativa = _validar_campo_textual(resposta, "justificativa")

    if classe not in CLASSES_PENAIS:
        raise ErroRespostaLLM(
            f"Classe penal inválida: {classe!r}. "
            f"Classes permitidas: {list(CLASSES_PENAIS)}."
        )

    return {
        "classe": classe,
        "justificativa": justificativa,
    }


def limpar_converter_texto(texto: str) -> dict[str, str]:
    """Limpa e converte a resposta textual da LLM em estrutura validada.

    A função aceita JSON puro e JSON envolvido por marcadores Markdown,
    como ` ```json ` e ` ``` `. Respostas com texto adicional, JSON
    malformado ou campos obrigatórios inválidos são rejeitadas.

    Args:
        texto: Resposta textual produzida pela LLM.

    Returns:
        Dicionário validado com `classe` e `justificativa`.

    Raises:
        ErroRespostaLLM: Se a resposta estiver vazia, malformada ou não
            cumprir o contrato esperado.
    """
    texto_validado = _validar_texto_resposta(texto)
    texto_limpo = _remover_marcadores_markdown(texto_validado)

    try:
        resposta = json.loads(texto_limpo)
    except json.JSONDecodeError as erro:
        raise ErroRespostaLLM(
            "A resposta da LLM não contém um JSON válido."
        ) from erro

    return _validar_resposta_estruturada(resposta)