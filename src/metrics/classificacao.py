"""Interface utilitária mantida para compatibilidade e agrupamentos por nível."""

from __future__ import annotations

from collections import defaultdict
from typing import Sequence

from src.avaliacao.dtos import ItemResultadoClassificado
from src.config import CONFIG, ConfiguracaoAplicacao
from src.metrics.fabrica import FabricaMetricas


def calcular_acuracia_simples(
    crimes_reais: Sequence[str], crimes_preditos: Sequence[str]
) -> float:
    fabrica = FabricaMetricas(CONFIG)
    estrategia = fabrica.criar_acuracia_exata()
    return estrategia.calcular(crimes_reais, crimes_preditos)


def calcular_acuracia_semantica(
    crimes_reais: Sequence[str],
    crimes_preditos: Sequence[str],
    configuracao: ConfiguracaoAplicacao = CONFIG,
) -> float:
    fabrica = FabricaMetricas(configuracao)
    estrategia = fabrica.criar_acuracia_taxonomica()
    return estrategia.calcular(crimes_reais, crimes_preditos)


def calcular_acuracia_por_nivel(
    itens: Sequence[ItemResultadoClassificado],
) -> dict[str, float]:
    grupos: dict[str, list[ItemResultadoClassificado]] = defaultdict(list)
    for item in itens:
        grupos[item.nivel.lower()].append(item)

    resultados: dict[str, float] = {}
    for nivel, grupo_itens in grupos.items():
        reais = [i.classe_real for i in grupo_itens]
        preditos = [i.classe_predita for i in grupo_itens]
        resultados[nivel] = calcular_acuracia_simples(reais, preditos)

    return resultados


def calcular_acuracia_semantica_por_nivel(
    itens: Sequence[ItemResultadoClassificado],
    configuracao: ConfiguracaoAplicacao = CONFIG,
) -> dict[str, float]:
    grupos: dict[str, list[ItemResultadoClassificado]] = defaultdict(list)
    for item in itens:
        grupos[item.nivel.lower()].append(item)

    resultados: dict[str, float] = {}
    for nivel, grupo_itens in grupos.items():
        reais = [i.classe_real for i in grupo_itens]
        preditos = [i.classe_predita for i in grupo_itens]
        resultados[nivel] = calcular_acuracia_semantica(
            reais, preditos, configuracao=configuracao
        )

    return resultados


def calcular_metricas_sk(
    crimes_reais: Sequence[str], crimes_preditos: Sequence[str]
) -> tuple[float, float, float]:
    fabrica = FabricaMetricas(CONFIG)
    estrategia = fabrica.criar_metricas_macro()
    return estrategia.calcular(crimes_reais, crimes_preditos)