"""Construção de resultados de classificação prontos para persistência."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class ErroConstrucaoResultado(ValueError):
    """Representa dados inválidos para montagem do resultado."""


def _obter_campo_textual(
    dados: Mapping[str, Any],
    nome_campo: str,
) -> str:
    """Obtém e valida um campo textual obrigatório.

    Args:
        dados: Mapeamento que contém o campo.
        nome_campo: Nome do campo obrigatório.

    Returns:
        Texto normalizado sem espaços externos.

    Raises:
        ErroConstrucaoResultado: Se o campo estiver ausente, não for textual
            ou estiver vazio.
    """
    valor = dados.get(nome_campo)

    if not isinstance(valor, str) or not valor.strip():
        raise ErroConstrucaoResultado(
            f"O campo '{nome_campo}' deve ser uma string não vazia."
        )

    return valor.strip()


def _obter_nivel(caso: Mapping[str, Any]) -> str:
    """Obtém o nível do caso aceitando os formatos antigo e normalizado.

    O dataset atual utiliza `nível`, enquanto a saída interna do sistema
    utiliza `nivel` para manter identificadores ASCII.

    Args:
        caso: Registro original do dataset.

    Returns:
        Nível normalizado da conduta.

    Raises:
        ErroConstrucaoResultado: Se nenhum dos formatos for válido.
    """
    nivel = caso.get("nivel")

    if nivel is None:
        nivel = caso.get("nível")

    if not isinstance(nivel, str) or not nivel.strip():
        raise ErroConstrucaoResultado(
            "O campo 'nivel' ou 'nível' deve ser uma string não vazia."
        )

    return nivel.strip()


def _validar_mapeamento(
    dados: Any,
    nome_dado: str,
) -> Mapping[str, Any]:
    """Valida se um valor representa um registro estruturado.

    Args:
        dados: Valor que será validado.
        nome_dado: Nome do dado para a mensagem de erro.

    Returns:
        Mapeamento validado.

    Raises:
        ErroConstrucaoResultado: Se o valor não for um mapeamento.
    """
    if not isinstance(dados, Mapping):
        raise ErroConstrucaoResultado(
            f"{nome_dado} deve ser um mapeamento."
        )

    return dados


def montar_resultado(
    caso: Mapping[str, Any],
    resposta: Mapping[str, Any],
) -> dict[str, str | int]:
    """Combina o caso original com a resposta classificada pela LLM.

    Esta função não salva arquivos e não atualiza o progresso. Ela apenas
    transforma os dados das etapas anteriores em uma estrutura estável para
    o repositório de resultados.

    Args:
        caso: Registro original do dataset.
        resposta: Resposta estruturada e validada da LLM.

    Returns:
        Resultado normalizado pronto para persistência.

    Raises:
        ErroConstrucaoResultado: Se o caso ou a resposta possuir campos
            obrigatórios ausentes ou inválidos.
    """
    caso_validado = _validar_mapeamento(caso, "caso")
    resposta_validada = _validar_mapeamento(resposta, "resposta")

    identificador = caso_validado.get("id")

    if (
        isinstance(identificador, bool)
        or not isinstance(identificador, int)
        or identificador < 0
    ):
        raise ErroConstrucaoResultado(
            "O campo 'id' deve ser um inteiro não negativo."
        )

    return {
        "id": identificador,
        "nivel": _obter_nivel(caso_validado),
        "texto": _obter_campo_textual(caso_validado, "texto"),
        "classe_real": _obter_campo_textual(
            caso_validado,
            "classe_correta",
        ),
        "classe_predita": _obter_campo_textual(
            resposta_validada,
            "classe",
        ),
        "justificativa": _obter_campo_textual(
            resposta_validada,
            "justificativa",
        ),
    }