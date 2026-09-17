"""Orquestrador do fluxo completo de avaliação estatística dos resultados."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from src.avaliacao.dtos import ResumoAvaliacao
from src.avaliacao.leitor_resultados import ler_resultados_jsonl
from src.config import CONFIG, ConfiguracaoAplicacao
from src.metrics.classificacao import (
    calcular_acuracia_por_nivel,
    calcular_acuracia_semantica_por_nivel,
)
from src.metrics.fabrica import FabricaMetricas
from src.relatorios.graficos import gerar_matriz_confusao
from src.relatorios.pdf import gerar_relatorio_pdf


def avaliar_dataset_classificado(
    caminho_jsonl: Path,
    configuracao: ConfiguracaoAplicacao = CONFIG,
) -> ResumoAvaliacao:
    """Executa a avaliação estatística completa sobre um arquivo JSONL classificado."""
    itens = list(ler_resultados_jsonl(caminho_jsonl))
    if not itens:
        raise ValueError(f"O arquivo {caminho_jsonl} não contém registros para avaliação.")

    reais = [item.classe_real for item in itens]
    preditos = [item.classe_predita for item in itens]

    # Instanciação centralizada das estratégias via Factory
    fabrica = FabricaMetricas(configuracao)
    acuracia_exata_strat = fabrica.criar_acuracia_exata()
    acuracia_tax_strat = fabrica.criar_acuracia_taxonomica()
    metricas_macro_strat = fabrica.criar_metricas_macro()

    # Cálculo das métricas globais
    acuracia = acuracia_exata_strat.calcular(reais, preditos)
    semantica = acuracia_tax_strat.calcular(reais, preditos)
    precisao, recall, f1 = metricas_macro_strat.calcular(reais, preditos)

    # Cálculo segmentado por nível
    ac_nivel = calcular_acuracia_por_nivel(itens)
    sem_nivel = calcular_acuracia_semantica_por_nivel(itens, configuracao=configuracao)

    resumo = ResumoAvaliacao(
        modelo=configuracao.llm.active_model,
        dataset=configuracao.datasets.active_dataset,
        total_exemplos=len(itens),
        acuracia_simples=acuracia,
        acuracia_semantica=semantica,
        acuracia_por_nivel=ac_nivel,
        acuracia_semantica_por_nivel=sem_nivel,
        precisao_macro=precisao,
        recall_macro=recall,
        f1_macro=f1,
    )

    # Persistência usando o caminho 'results' correto
    pasta_saida = configuracao.paths.results
    pasta_saida.mkdir(parents=True, exist_ok=True)

    caminho_json_saida = pasta_saida / "resultado_avaliacao.json"
    with caminho_json_saida.open("w", encoding="utf-8") as f:
        json.dump(asdict(resumo), f, ensure_ascii=False, indent=2)

    caminho_matriz = pasta_saida / "matriz_confusao.png"
    gerar_matriz_confusao(reais, preditos, caminho_matriz)

    caminho_pdf = pasta_saida / "Relatorio_Avaliacao_TCC.pdf"
    gerar_relatorio_pdf(resumo, caminho_matriz, caminho_pdf)

    return resumo