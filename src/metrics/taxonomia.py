"""Carregamento e verificação taxonômica do Vade Mecum."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping


class TaxonomiaVadeMecum:
    """Gerencia a hierarquia e agrupamentos semânticos dos crimes."""

    def __init__(self, grupos_semanticos: Mapping[str, list[str]]) -> None:
        self._grupos = grupos_semanticos

    @classmethod
    def do_arquivo_json(cls, caminho_json: Path) -> TaxonomiaVadeMecum:
        """Carrega os grupos taxonômicos a partir de um arquivo JSON."""
        if not caminho_json.exists():
            raise FileNotFoundError(
                f"Arquivo de taxonomia não encontrado: {caminho_json}"
            )

        with caminho_json.open("r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

        return cls(grupos_semanticos=dados.get("grupos_semanticos", {}))

    def mesmo_grupo_semantico(self, crime_a: str, crime_b: str) -> bool:
        """Verifica se dois crimes pertencem à mesma família penal."""
        if crime_a == crime_b:
            return True

        for integrantes in self._grupos.values():
            if crime_a in integrantes and crime_b in integrantes:
                return True
        return False