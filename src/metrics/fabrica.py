"""Fábrica para instanciação das estratégias de avaliação."""

from __future__ import annotations

from src.config import ConfiguracaoAplicacao
from src.metrics.estrategias import (
    EstrategiaAcuraciaExata,
    EstrategiaAcuraciaTaxonomicaPonderada,
    EstrategiaMetricasSklearn,
)
from src.metrics.taxonomia import TaxonomiaVadeMecum


class FabricaMetricas:
    """Encapsula a montagem das estratégias injetando as configurações globais."""

    def __init__(
        self,
        configuracao: ConfiguracaoAplicacao,
        taxonomia: TaxonomiaVadeMecum | None = None,
    ) -> None:
        self.configuracao = configuracao
        self.taxonomia = taxonomia or TaxonomiaVadeMecum.do_arquivo_json(
            configuracao.paths.taxonomy
        )

    def criar_acuracia_exata(self) -> EstrategiaAcuraciaExata:
        return EstrategiaAcuraciaExata()

    def criar_acuracia_taxonomica(self) -> EstrategiaAcuraciaTaxonomicaPonderada:
        return EstrategiaAcuraciaTaxonomicaPonderada(
            alpha=self.configuracao.metrics.atp_alpha_weight,
            taxonomia=self.taxonomia,
        )

    def criar_metricas_macro(self) -> EstrategiaMetricasSklearn:
        return EstrategiaMetricasSklearn()