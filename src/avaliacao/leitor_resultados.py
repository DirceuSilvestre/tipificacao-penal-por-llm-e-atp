"""Leitor incremental de arquivos JSONL contendo predições das LLMs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from src.avaliacao.dtos import ItemResultadoClassificado


def ler_resultados_jsonl(
    caminho_arquivo: Path,
) -> Iterator[ItemResultadoClassificado]:
    """Lê um arquivo JSONL de resultados linha a linha gerando DTOs imutáveis.

    Args:
        caminho_arquivo: Caminho do arquivo JSONL no disco.

    Yields:
        Instâncias de ItemResultadoClassificado.

    Raises:
        FileNotFoundError: Se o arquivo especificado não existir.
        ValueError: Se a linha contiver JSON malformado.
    """
    if not caminho_arquivo.exists():
        raise FileNotFoundError(
            f"Arquivo de resultados não encontrado: {caminho_arquivo}"
        )

    with caminho_arquivo.open("r", encoding="utf-8") as arquivo:
        for numero_linha, linha in enumerate(arquivo, start=1):
            linha_limpa = linha.strip()
            if not linha_limpa:
                continue
            try:
                dados = json.loads(linha_limpa)
                yield ItemResultadoClassificado.do_dicionario(dados)
            except (json.JSONDecodeError, KeyError, TypeError) as erro:
                raise ValueError(
                    f"Erro de parsing na linha {numero_linha} de {caminho_arquivo}: {erro}"
                ) from erro