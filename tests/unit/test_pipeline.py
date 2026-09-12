"""Testes unitários da orquestração do pipeline."""

import json
from pathlib import Path

from src.config import (
    ConfiguracaoAplicacao,
    ConfiguracaoAtrasos,
    ConfiguracaoCaminhos,
    ConfiguracaoDatasets,
    ConfiguracaoLLM,
    ConfiguracaoMetricas,
    ConfiguracaoModelo,
)
from src.pipeline import executar_pipeline


class ProvedorFalso:
    """Simula um provedor LLM sem realizar chamadas externas."""

    def gerar_conteudo(self, prompt: str) -> str:
        """Retorna uma resposta JSON previsível para o teste.

        Args:
            prompt: Prompt recebido pelo pipeline.

        Returns:
            Resposta JSON simulada da LLM.
        """
        return json.dumps(
            {
                "classe": "peculato",
                "justificativa": "Resposta simulada para teste.",
            }
        )


def _criar_configuracao(
    tmp_path: Path,
) -> ConfiguracaoAplicacao:
    """Cria uma configuração isolada para o teste.

    Args:
        tmp_path: Diretório temporário do pytest.

    Returns:
        Configuração completa apontando para arquivos temporários.
    """
    caminho_dados = tmp_path / "data"
    caminho_organizado = caminho_dados / "organized"
    caminho_resultados = caminho_dados / "results"
    caminho_organizado.mkdir(parents=True)

    return ConfiguracaoAplicacao(
        paths=ConfiguracaoCaminhos(
            data=caminho_dados,
            organized=caminho_organizado,
            classified=caminho_dados / "classified",
            results=caminho_resultados,
            taxonomy=caminho_dados / "taxonomy.json",
        ),
        datasets=ConfiguracaoDatasets(
            active_dataset="dataset_teste.jsonl",
            available={},
            organized_directory=caminho_organizado,
        ),
        metrics=ConfiguracaoMetricas(atp_alpha_weight=0.5),
        llm=ConfiguracaoLLM(
            active_model="modelo_teste",
            delays=ConfiguracaoAtrasos(request_delay_seconds=0),
            models={
                "modelo_teste": ConfiguracaoModelo(
                    provider="teste",
                    model_name="modelo-teste",
                )
            },
        ),
        logging={},
    )


def test_deve_processar_registro_e_atualizar_progresso(
    tmp_path: Path,
) -> None:
    """Verifica o fluxo completo com provedor falso."""
    configuracao = _criar_configuracao(tmp_path)
    caminho_dataset = configuracao.datasets.active_dataset_path
    caminho_progresso = (
        configuracao.paths.data / "progresso_processamento.json"
    )

    caminho_dataset.write_text(
        '{"id": 1, "nível": "fácil", '
        '"texto": "Conduta de teste.", '
        '"classe_correta": "peculato"}\n',
        encoding="utf-8",
    )
    caminho_progresso.parent.mkdir(parents=True, exist_ok=True)
    caminho_progresso.write_text(
        json.dumps(
            {
                "dataset_teste.jsonl": {
                    "ultimo_id_processado": 0,
                    "ultima_linha_processada": 0,
                    "status": "em_andamento",
                }
            }
        ),
        encoding="utf-8",
    )

    executar_pipeline(
        configuracao=configuracao,
        provedor=ProvedorFalso(),
    )

    caminho_resultados = (
        configuracao.paths.results
        / "resultados_dataset_teste.jsonl"
    )
    linhas_resultados = caminho_resultados.read_text(
        encoding="utf-8"
    ).splitlines()
    progresso = json.loads(
        caminho_progresso.read_text(encoding="utf-8")
    )

    assert len(linhas_resultados) == 1
    assert json.loads(linhas_resultados[0])["id"] == 1
    assert progresso["dataset_teste.jsonl"]["ultimo_id_processado"] == 1
    assert progresso["dataset_teste.jsonl"]["status"] == "concluido"