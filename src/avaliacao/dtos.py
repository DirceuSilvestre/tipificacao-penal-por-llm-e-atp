"""Objetos de transferência de dados (DTOs) do módulo de avaliação."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ItemResultadoClassificado:
    """Representa um registro individual classificado do dataset JSONL.

    Attributes:
        id: Identificador único do caso fático.
        nivel: Nível de complexidade/dificuldade ('fácil', 'médio', 'difícil').
        texto: Narrativa fática do crime.
        classe_real: Tipificação penal correta (ground truth).
        classe_predita: Tipificação penal atribuída pelo modelo de linguagem.
        justificativa: Explicação jurídica gerada pela LLM.
    """

    id: int
    nivel: str
    texto: str
    classe_real: str
    classe_predita: str
    justificativa: str

    @classmethod
    def do_dicionario(
        cls, dados: dict[str, Any]
    ) -> ItemResultadoClassificado:
        """Instancia o DTO a partir de um dicionário extraído do JSONL.

        Args:
            dados: Dicionário contendo os campos do resultado.

        Returns:
            Instância validada do DTO.
        """
        return cls(
            id=int(dados["id"]),
            nivel=str(dados.get("nivel") or dados.get("nível", "desconhecido")),
            texto=str(dados["texto"]),
            classe_real=str(dados["classe_real"]),
            classe_predita=str(dados["classe_predita"]),
            justificativa=str(dados.get("justificativa", "")),
        )


@dataclass(frozen=True)
class ResumoAvaliacao:
    """Encapsula o resultado consolidado das métricas estatísticas.

    Attributes:
        modelo: Nome do modelo de linguagem avaliado.
        dataset: Nome do dataset processado.
        total_exemplos: Quantidade de amostras analisadas.
        acuracia_simples: Acurácia exata global.
        acuracia_semantica: Acurácia ponderada por proximidade taxonômica.
        acuracia_por_nivel: Acurácia simples segmentada por nível de dificuldade.
        acuracia_semantica_por_nivel: Acurácia semântica por nível.
        precisao_macro: Precisão média macro.
        recall_macro: Revocação média macro.
        f1_macro: F1-score médio macro.
    """

    modelo: str
    dataset: str
    total_exemplos: int
    acuracia_simples: float
    acuracia_semantica: float
    acuracia_por_nivel: dict[str, float]
    acuracia_semantica_por_nivel: dict[str, float]
    precisao_macro: float
    recall_macro: float
    f1_macro: float