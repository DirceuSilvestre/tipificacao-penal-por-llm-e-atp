"""Leitura incremental e validação de datasets no formato JSONL."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from src.progresso.repositorio import ProgressoProcessamento


class ErroLeituraJsonl(ValueError):
    """Representa um erro de leitura ou validação de um arquivo JSONL."""


def _validar_registro(
    registro: Any,
    numero_linha: int,
) -> dict[str, Any]:
    """Valida o formato básico de um registro do dataset.

    Args:
        registro: Objeto convertido a partir da linha JSON.
        numero_linha: Número da linha no arquivo JSONL.

    Returns:
        Registro validado como dicionário.

    Raises:
        ErroLeituraJsonl: Se o registro não for um objeto ou não possuir
            um identificador inteiro não negativo.
    """
    if not isinstance(registro, dict):
        raise ErroLeituraJsonl(
            f"A linha {numero_linha} deve conter um objeto JSON."
        )

    identificador = registro.get("id")

    if (
        isinstance(identificador, bool)
        or not isinstance(identificador, int)
        or identificador < 0
    ):
        raise ErroLeituraJsonl(
            f"O campo 'id' da linha {numero_linha} deve ser um "
            "inteiro não negativo."
        )

    return registro


def _ler_linha_json(
    linha: str,
    numero_linha: int,
) -> dict[str, Any] | None:
    """Converte uma linha JSONL em registro validado.

    Linhas vazias ou compostas apenas por espaços são ignoradas.

    Args:
        linha: Conteúdo textual da linha.
        numero_linha: Número da linha no arquivo JSONL.

    Returns:
        Registro validado ou None para uma linha vazia.

    Raises:
        ErroLeituraJsonl: Se o conteúdo não for um JSON válido ou se o
            registro possuir estrutura inválida.
    """
    if not linha.strip():
        return None

    try:
        registro = json.loads(linha)
    except json.JSONDecodeError as erro:
        raise ErroLeituraJsonl(
            f"JSON inválido na linha {numero_linha}."
        ) from erro

    return _validar_registro(registro, numero_linha)


def ler_jsonl_a_partir_do_id(
    caminho: Path,
    id_inicial: int,
) -> Iterator[dict[str, Any]]:
    """Lê incrementalmente registros JSONL a partir de um ID.

    O arquivo é percorrido linha a linha e os registros anteriores ao
    identificador inicial são descartados. O conteúdo completo do dataset
    não é carregado na memória.

    Args:
        caminho: Caminho do arquivo JSONL.
        id_inicial: Primeiro ID que deverá ser retornado.

    Yields:
        Registros válidos cujo ID seja maior ou igual ao ID inicial.

    Raises:
        FileNotFoundError: Se o arquivo não existir.
        ErroLeituraJsonl: Se o ID inicial for inválido ou alguma linha
            não possuir JSON válido.
    """
    if (
        isinstance(id_inicial, bool)
        or not isinstance(id_inicial, int)
        or id_inicial < 0
    ):
        raise ErroLeituraJsonl(
            "id_inicial deve ser um inteiro não negativo."
        )

    with caminho.open("r", encoding="utf-8") as arquivo:
        for numero_linha, linha in enumerate(arquivo, start=1):
            registro = _ler_linha_json(linha, numero_linha)

            if registro is None:
                continue

            if registro["id"] >= id_inicial:
                yield registro


def ler_jsonl_pendente(
    caminho: Path,
    progresso: ProgressoProcessamento,
) -> Iterator[dict[str, Any]]:
    """Lê somente os registros ainda não processados.

    O próximo ID é calculado a partir do maior ID processado com sucesso.
    Como o progresso só deve ser atualizado após o salvamento do resultado,
    o registro correspondente ao último ID salvo não será retornado novamente.

    Args:
        caminho: Caminho do arquivo JSONL.
        progresso: Progresso atual do dataset.

    Yields:
        Registros ainda pendentes de processamento.

    Raises:
        TypeError: Se o progresso não for ProgressoProcessamento.
    """
    if not isinstance(progresso, ProgressoProcessamento):
        raise TypeError(
            "progresso deve ser uma instância de "
            "ProgressoProcessamento."
        )

    id_inicial = progresso.ultimo_id_processado + 1

    yield from ler_jsonl_a_partir_do_id(caminho, id_inicial)