"""Módulo de avaliação estocástica via Bootstrap para classificação penal por LLMs.

Realiza a reamostragem estatística para estimar Intervalos de Confiança (IC 95%)
tanto em nível global quanto estratificado por explicitude (fácil, médio, difícil).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
import json
import logging
import pathlib
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class NivelExplicitude(str, Enum):
    FACIL = "fácil"
    MEDIO = "médio"
    DIFICIL = "difícil"
    GLOBAL = "global"


class TipoDataset(str, Enum):
    CURADO = "curado"
    SINTETICO = "sintetico"


@dataclass(frozen=True)
class ResultadoBootstrap:
    """Representa o resultado estatístico da avaliação de um cenário."""

    modelo: str
    dataset: TipoDataset
    nivel: NivelExplicitude
    n_amostras: int
    acuracia_media: float
    ic_inferior: float
    ic_superior: float

    @property
    def ic_formatado(self) -> str:
        return f"[{self.ic_inferior * 100:.2f}%, {self.ic_superior * 100:.2f}%]"

    def to_dict(self) -> Dict:
        """Serializa o resultado para formato legível por JSON."""
        return {
            "modelo": self.modelo,
            "dataset": self.dataset.value,
            "nivel": self.nivel.value,
            "n_amostras": self.n_amostras,
            "acuracia_media": round(self.acuracia_media, 4),
            "acuracia_media_percentual": round(self.acuracia_media * 100, 2),
            "ic_95_inferior": round(self.ic_inferior, 4),
            "ic_95_superior": round(self.ic_superior, 4),
            "ic_95_formatado": self.ic_formatado,
        }


class BootstrapperClassificacao:
    """Engine estatística responsável pelas reamostragens Bootstrap."""

    def __init__(
        self,
        n_iterations: int = 1000,
        ci_level: float = 95.0,
        seed: int = 42,
    ) -> None:
        self._n_iterations = n_iterations
        self._ci_level = ci_level
        self._rng = np.random.default_rng(seed)

    def avaliar_dataframe(
        self,
        df: pd.DataFrame,
        modelo: str,
        dataset_tipo: TipoDataset,
        nivel: NivelExplicitude,
    ) -> Optional[ResultadoBootstrap]:
        """Calcula a acurácia média e o IC de 95% para uma fatia do dataset."""
        if df.empty:
            logging.warning(f"DataFrame vazio para {modelo} | {dataset_tipo.value} | {nivel.value}")
            return None

        n_samples = len(df)
        y_real = df["classe_real"].to_numpy()
        y_pred = df["classe_predita"].to_numpy()

        scores_acuracia: List[float] = []

        for _ in range(self._n_iterations):
            indices = self._rng.choice(n_samples, size=n_samples, replace=True)
            acuracia = np.mean(y_real[indices] == y_pred[indices])
            scores_acuracia.append(float(acuracia))

        alpha = (100.0 - self._ci_level) / 2.0
        ic_inferior = float(np.percentile(scores_acuracia, alpha))
        ic_superior = float(np.percentile(scores_acuracia, 100.0 - alpha))
        media_acuracia = float(np.mean(scores_acuracia))

        return ResultadoBootstrap(
            modelo=modelo,
            dataset=dataset_tipo,
            nivel=nivel,
            n_amostras=n_samples,
            acuracia_media=media_acuracia,
            ic_inferior=ic_inferior,
            ic_superior=ic_superior,
        )


class ProcessadorDatasetsClassificados:
    """Gerencia o carregamento de arquivos e orquestra a suíte de testes."""

    def __init__(self, bootstrapper: BootstrapperClassificacao) -> None:
        self._bootstrapper = bootstrapper

    @staticmethod
    def carregar_arquivo(caminho: pathlib.Path) -> pd.DataFrame:
        """Carrega CSVs (sep=;) ou JSONLines garantindo schema mínimo."""
        if caminho.suffix in [".jsonl"]:
            df = pd.read_json(caminho, lines=True)
        else:
            df = pd.read_csv(caminho, sep=";")

        colunas_obrigatorias = {"nivel", "classe_real", "classe_predita"}
        if not colunas_obrigatorias.issubset(df.columns):
            raise KeyError(
                f"O arquivo {caminho.name} não possui as colunas necessárias: {colunas_obrigatorias}"
            )

        return df

    def processar_arquivo(
        self,
        caminho_arquivo: pathlib.Path,
        nome_modelo: str,
        dataset_tipo: TipoDataset,
    ) -> List[ResultadoBootstrap]:
        """Avalia um arquivo tanto de forma Global quanto dividida nos 3 níveis de explicitude."""
        df = self.carregar_arquivo(caminho_arquivo)
        resultados: List[ResultadoBootstrap] = []

        # 1. Avaliação Global (Visão geral do modelo no dataset)
        res_global = self._bootstrapper.avaliar_dataframe(
            df=df,
            modelo=nome_modelo,
            dataset_tipo=dataset_tipo,
            nivel=NivelExplicitude.GLOBAL,
        )
        if res_global:
            resultados.append(res_global)

        # 2. Avaliação Decomposta pelos 3 Níveis de Explicitude
        niveis_estudo = [
            NivelExplicitude.FACIL,
            NivelExplicitude.MEDIO,
            NivelExplicitude.DIFICIL,
        ]

        for nivel in niveis_estudo:
            df_nivel = df[df["nivel"] == nivel.value]
            res_nivel = self._bootstrapper.avaliar_dataframe(
                df=df_nivel,
                modelo=nome_modelo,
                dataset_tipo=dataset_tipo,
                nivel=nivel,
            )
            if res_nivel:
                resultados.append(res_nivel)

        return resultados


def salvar_resultados_json(
    resultados: List[ResultadoBootstrap],
    caminho_saida: str = "data/results/bootstrap_evaluation_results.json",
    n_iterations: int = 1000,
    ci_level: float = 95.0,
) -> pathlib.Path:
    """Exporta os resultados calculados para um arquivo JSON legível e estruturado."""
    destino = pathlib.Path(caminho_saida)
    destino.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "metadata": {
            "data_execucao": datetime.now().isoformat(),
            "n_iterations": n_iterations,
            "ci_level": ci_level,
            "total_experimentos": len(resultados),
        },
        "resultados": [r.to_dict() for r in resultados],
    }

    with open(destino, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    logging.info(f"Resultados salvos com sucesso em: {destino.resolve()}")
    return destino


# --- Ponto de Entrada da Execução ---
def executar_suite_avaliacao(
    diretorio_dados: str = "data/classified",
    diretorio_saida: str = "data/results",
    extensao_preferencial: str = ".jsonl",
) -> pd.DataFrame:
    """Executa a suíte filtrando exclusivamente por um formato (.jsonl ou .csv)."""
    path = pathlib.Path(diretorio_dados)
    n_iterations = 1000
    ci_level = 95.0

    bootstrapper = BootstrapperClassificacao(
        n_iterations=n_iterations, ci_level=ci_level, seed=42
    )
    processador = ProcessadorDatasetsClassificados(bootstrapper)

    modelos = ["gemini_flash", "modelo_2", "modelo_3"]
    datasets = [TipoDataset.CURADO, TipoDataset.SINTETICO]

    todos_resultados: List[ResultadoBootstrap] = []

    # Ajusta a extensão garantindo ponto inicial
    ext = extensao_preferencial if extensao_preferencial.startswith(".") else f".{extensao_preferencial}"

    for modelo in modelos:
        for ds in datasets:
            # Filtra estritamente apenas os arquivos da extensão escolhida
            padrao_busca = f"*{modelo}*{ds.value}*{ext}"
            arquivos = list(path.glob(padrao_busca))

            if not arquivos:
                logging.warning(f"Nenhum arquivo {ext} encontrado para busca: {padrao_busca}")

            for arq in arquivos:
                logging.info(f"Avaliando: Modelo={modelo} | Dataset={ds.value} | Arquivo={arq.name}")
                res = processador.processar_arquivo(
                    caminho_arquivo=arq,
                    nome_modelo=modelo,
                    dataset_tipo=ds,
                )
                todos_resultados.extend(res)

    # 1. Salva o resultado estruturado em JSON na pasta data/results/
    arquivo_json = pathlib.Path(diretorio_saida) / "bootstrap_evaluation_results.json"
    salvar_resultados_json(
        resultados=todos_resultados,
        caminho_saida=str(arquivo_json),
        n_iterations=n_iterations,
        ci_level=ci_level,
    )

    # 2. Converte para DataFrame para exibição rápida no terminal
    registros = [
        {
            "Modelo": r.modelo,
            "Dataset": r.dataset.value,
            "Nível": r.nivel.value,
            "Amostras (N)": r.n_amostras,
            "Acurácia Média (%)": round(r.acuracia_media * 100, 2),
            "IC 95%": r.ic_formatado,
        }
        for r in todos_resultados
    ]

    return pd.DataFrame(registros)


def testar_validade_estatistica_bootstrap() -> None:
    """Valida o algoritmo contra cenários teóricos conhecidos."""
    bootstrapper = BootstrapperClassificacao(n_iterations=1000, ci_level=95.0, seed=42)

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

    logging.info("✅ Todos os testes de verificação estatística passaram com sucesso!")


if __name__ == "__main__":
    # 1. Executa a validação técnica/estatística
    testar_validade_estatistica_bootstrap()

    # 2. Executa filtrando por formato único (ex: '.jsonl' ou '.csv') e salva em JSON
    df_resultado_final = executar_suite_avaliacao(
        diretorio_dados="data/classified",
        diretorio_saida="data/results",
        extensao_preferencial=".jsonl",  # Altere para '.csv' se preferir ler os CSVs
    )
    print("\n=== RESUMO CONSOLIDADO DE AVALIAÇÃO VIA BOOTSTRAP ===")
    print(df_resultado_final.to_string(index=False))