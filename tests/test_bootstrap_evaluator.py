"""Testes unitários para a engine de bootstrap (tests/test_bootstrap_evaluator.py)."""

import pandas as pd
import pytest

from src.avaliacao.bootstrap_evaluator import (
    BootstrapperClassificacao,
    NivelExplicitude,
    TipoDataset,
)


def test_validade_estatistica_bootstrap_casos_limite() -> None:
    """Valida o algoritmo contra cenários teóricos conhecidos (100% e 0% de acerto)."""
    bootstrapper = BootstrapperClassificacao(n_iterations=1000, ci_level=95.0, seed=42)

    # 1. Caso Limite: 100% de acerto (IC deve ser [100%, 100%])
    df_perfeito = pd.DataFrame({
        "classe_real": ["peculato"] * 20,
        "classe_predita": ["peculato"] * 20,
        "nivel": ["fácil"] * 20,
    })
    res_perfeito = bootstrapper.avaliar_dataframe(
        df_perfeito, "modelo_teste", TipoDataset.CURADO, NivelExplicitude.FACIL
    )

    assert res_perfeito is not None
    assert res_perfeito.acuracia_media == 1.0
    assert res_perfeito.ic_inferior == 1.0
    assert res_perfeito.ic_superior == 1.0

    # 2. Caso Limite: 0% de acerto (IC deve ser [0%, 0%])
    df_zero = pd.DataFrame({
        "classe_real": ["peculato"] * 20,
        "classe_predita": ["corrupcao_passiva"] * 20,
        "nivel": ["fácil"] * 20,
    })
    res_zero = bootstrapper.avaliar_dataframe(
        df_zero, "modelo_teste", TipoDataset.CURADO, NivelExplicitude.FACIL
    )

    assert res_zero is not None
    assert res_zero.acuracia_media == 0.0
    assert res_zero.ic_inferior == 0.0
    assert res_zero.ic_superior == 0.0