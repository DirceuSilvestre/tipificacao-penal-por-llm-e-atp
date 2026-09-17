"""Testes unitários para o módulo de métricas estatísticas de classificação."""

from src.avaliacao.dtos import ItemResultadoClassificado
from src.metrics.classificacao import (
    calcular_acuracia_semantica,
    calcular_acuracia_simples,
)


def test_deve_retornar_acuracia_simples_perfeita_quando_todas_classes_coincidirem() -> None:
    # Arrange
    reais = ["peculato", "corrupcao_passiva"]
    preditos = ["peculato", "corrupcao_passiva"]

    # Act
    resultado = calcular_acuracia_simples(reais, preditos)

    # Assert
    assert resultado == 1.0


def test_deve_retornar_pontuacao_parcial_na_acuracia_semantica_para_mesmo_grupo() -> None:
    # Arrange
    reais = ["peculato", "corrupcao_passiva"]
    preditos = ["peculato_culposo", "corrupcao_passiva"]

    # Act
    resultado = calcular_acuracia_semantica(reais, preditos)

    # Assert
    # Item 1: 0.5 (mesmo grupo) | Item 2: 1.0 (exato) -> Média: 1.5 / 2 = 0.75
    assert resultado == 0.75