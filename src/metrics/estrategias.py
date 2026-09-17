"""Estratégias intercambiáveis de cálculo de métricas de classificação."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence, Tuple

from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.preprocessing import LabelEncoder

from src.metrics.taxonomia import TaxonomiaVadeMecum


class EstrategiaMetrica(ABC):
    """Interface base para estratégias de cálculo estatístico."""

    @abstractmethod
    def calcular(
        self, crimes_reais: Sequence[str], crimes_preditos: Sequence[str]
    ) -> float | Tuple[float, float, float]:
        """Executa o cálculo da métrica sobre as sequências de dados."""


class EstrategiaAcuraciaExata(EstrategiaMetrica):
    """Calcula a acurácia estrita entre predições e valores reais."""

    def calcular(
        self, crimes_reais: Sequence[str], crimes_preditos: Sequence[str]
    ) -> float:
        if not crimes_reais or len(crimes_reais) != len(crimes_preditos):
            return 0.0
        return float(accuracy_score(crimes_reais, crimes_preditos))


class EstrategiaAcuraciaTaxonomicaPonderada(EstrategiaMetrica):
    """Calcula a ATP aplicando o peso alpha para erros dentro do mesmo grupo semântico."""

    def __init__(self, alpha: float, taxonomia: TaxonomiaVadeMecum) -> None:
        self.alpha = alpha
        self.taxonomia = taxonomia

    def calcular(
        self, crimes_reais: Sequence[str], crimes_preditos: Sequence[str]
    ) -> float:
        if not crimes_reais or len(crimes_reais) != len(crimes_preditos):
            return 0.0

        pontuacao_total = 0.0
        for real, predito in zip(crimes_reais, crimes_preditos):
            if real == predito:
                pontuacao_total += 1.0
            elif self.taxonomia.mesmo_grupo_semantico(real, predito):
                pontuacao_total += self.alpha

        return pontuacao_total / len(crimes_preditos)


class EstrategiaMetricasSklearn(EstrategiaMetrica):
    """Calcula Precisão, Recall e F1-Score com agregação Macro."""

    def calcular(
        self, crimes_reais: Sequence[str], crimes_preditos: Sequence[str]
    ) -> Tuple[float, float, float]:
        if not crimes_reais or len(crimes_reais) != len(crimes_preditos):
            return 0.0, 0.0, 0.0

        encoder = LabelEncoder()
        encoder.fit(list(crimes_reais) + list(crimes_preditos))

        reais_enc = encoder.transform(crimes_reais)
        preditos_enc = encoder.transform(crimes_preditos)

        precisao = float(
            precision_score(reais_enc, preditos_enc, average="macro", zero_division=0)
        )
        recall = float(
            recall_score(reais_enc, preditos_enc, average="macro", zero_division=0)
        )
        f1 = float(
            f1_score(reais_enc, preditos_enc, average="macro", zero_division=0)
        )

        return precisao, recall, f1