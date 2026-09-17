"""Testes unitários das estratégias e fábrica de métricas."""

from __future__ import annotations

import pytest
from src.metrics.taxonomia import TaxonomiaVadeMecum
from src.metrics.estrategias import (
    EstrategiaAcuraciaExata,
    EstrategiaAcuraciaTaxonomicaPonderada,
)

@pytest.fixture
def taxonomia_mock(tmp_path):
    caminho_json = tmp_path / "vade_mecum_taxonomy.json"
    caminho_json.write_text(
        '{"grupos_semanticos": {"peculato": ["peculato", "peculato_culposo"]}}',
        encoding="utf-8",
    )
    return TaxonomiaVadeMecum.do_arquivo_json(caminho_json)


def test_atp_com_peso_alpha_dinamico(taxonomia_mock):
    reais = ["peculato", "peculato"]
    preditos = ["peculato", "peculato_culposo"]

    # Teste com alpha 0.8
    estrategia_08 = EstrategiaAcuraciaTaxonomicaPonderada(0.8, taxonomia_mock)
    # Exato (1.0) + Erro Semântico (0.8) = 1.8 / 2 = 0.9
    assert estrategia_08.calcular(reais, preditos) == 0.9

    # Teste com alpha 0.5
    estrategia_05 = EstrategiaAcuraciaTaxonomicaPonderada(0.5, taxonomia_mock)
    # Exato (1.0) + Erro Semântico (0.5) = 1.5 / 2 = 0.75
    assert estrategia_05.calcular(reais, preditos) == 0.75