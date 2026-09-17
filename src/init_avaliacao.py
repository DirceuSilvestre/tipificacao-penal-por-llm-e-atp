"""Script utilitário para disparo independente do pipeline de avaliação de métricas."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.avaliacao.avaliador import avaliar_dataset_classificado
from src.config import CONFIG


def main() -> None:
    caminho_padrao = CONFIG.paths.classified / CONFIG.datasets.active_dataset

    parser = argparse.ArgumentParser(
        description="Executa a avaliação estatística sobre um dataset JSONL classificado."
    )
    parser.add_argument(
        "--dataset",
        "-d",
        type=Path,
        default=caminho_padrao,
        help=f"Caminho do arquivo JSONL classificado (Padrão: {caminho_padrao})",
    )

    args = parser.parse_args()

    print(f"[+] Iniciando avaliação do dataset: {args.dataset}")
    resumo = avaliar_dataset_classificado(args.dataset)

    print("\n================ RESUMO DA AVALIAÇÃO ================")
    print(f"Modelo Ativo:         {resumo.modelo}")
    print(f"Total de Casos:       {resumo.total_exemplos}")
    print(f"Acurácia Simples:     {resumo.acuracia_simples:.4f}")
    print(f"Acurácia Taxonômica:  {resumo.acuracia_semantica:.4f}")
    print(f"Precisão Macro:       {resumo.precisao_macro:.4f}")
    print(f"Recall Macro:         {resumo.recall_macro:.4f}")
    print(f"F1-Score Macro:       {resumo.f1_macro:.4f}")
    print("=====================================================")
    print(f"[+] Artefatos e relatórios gerados em: {CONFIG.paths.results}")


if __name__ == "__main__":
    main()