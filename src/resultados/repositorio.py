"""Persistência durável de resultados de classificação em JSONL."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any


class ErroRepositorioResultados(ValueError):
    """Representa um resultado ou arquivo de resultados inválido."""


def _validar_id(id_registro: Any) -> int:
    """Valida um identificador de resultado.

    Args:
        id_registro: Identificador que será validado.

    Returns:
        Identificador inteiro não negativo.

    Raises:
        ErroRepositorioResultados: Se o identificador for inválido.
    """
    if (
        isinstance(id_registro, bool)
        or not isinstance(id_registro, int)
        or id_registro < 0
    ):
        raise ErroRepositorioResultados(
            "O campo 'id' deve ser um inteiro não negativo."
        )

    return id_registro


def _validar_resultado(
    resultado: Mapping[str, Any],
) -> dict[str, Any]:
    """Valida o resultado antes da persistência.

    Args:
        resultado: Resultado estruturado produzido pelo construtor.

    Returns:
        Cópia mutável do resultado validado.

    Raises:
        ErroRepositorioResultados: Se o resultado não for um mapeamento ou
            não possuir um ID válido.
    """
    if not isinstance(resultado, Mapping):
        raise ErroRepositorioResultados(
            "resultado deve ser um mapeamento."
        )

    resultado_validado = dict(resultado)
    _validar_id(resultado_validado.get("id"))

    return resultado_validado


def salvar_resultado(
    caminho: Path,
    resultado: Mapping[str, Any],
) -> None:
    """Acrescenta um resultado ao arquivo JSONL de forma durável.

    O arquivo é aberto em modo append. Após a escrita da linha, o conteúdo
    é descarregado para o sistema operacional com `flush` e sincronizado
    fisicamente com `os.fsync`.

    Args:
        caminho: Caminho do arquivo JSONL de resultados.
        resultado: Resultado estruturado e validado.

    Raises:
        ErroRepositorioResultados: Se o resultado possuir um ID inválido.
        OSError: Se a pasta ou o arquivo não puder ser criado ou gravado.
    """
    resultado_validado = _validar_resultado(resultado)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    with caminho.open("a", encoding="utf-8") as arquivo:
        json.dump(
            resultado_validado,
            arquivo,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        arquivo.write("\n")
        arquivo.flush()
        os.fsync(arquivo.fileno())


def resultado_ja_salvo(
    caminho: Path,
    id_registro: int,
) -> bool:
    """Verifica se um resultado já foi persistido pelo seu ID.

    A leitura ocorre linha a linha para evitar carregar todo o arquivo na
    memória. Linhas vazias são ignoradas.

    Args:
        caminho: Caminho do arquivo JSONL de resultados.
        id_registro: Identificador do resultado procurado.

    Returns:
        True se o ID já estiver salvo; caso contrário, False.

    Raises:
        ErroRepositorioResultados: Se o ID informado for inválido ou se
            uma linha do arquivo não contiver JSON válido.
        FileNotFoundError: Se o arquivo não existir.
    """
    id_procurado = _validar_id(id_registro)

    with caminho.open("r", encoding="utf-8") as arquivo:
        for numero_linha, linha in enumerate(arquivo, start=1):
            if not linha.strip():
                continue

            try:
                resultado = json.loads(linha)
            except json.JSONDecodeError as erro:
                raise ErroRepositorioResultados(
                    f"JSON inválido na linha {numero_linha} "
                    "do arquivo de resultados."
                ) from erro

            if not isinstance(resultado, dict):
                raise ErroRepositorioResultados(
                    f"A linha {numero_linha} do arquivo de resultados "
                    "deve conter um objeto JSON."
                )

            if resultado.get("id") == id_procurado:
                return True

    return False