"""Teste de integração do fluxo de processamento retomável."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

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


class ProvedorFalsoComFalha:
    """Simula uma LLM que falha ao processar um ID específico."""

    def __init__(self, id_com_falha: int) -> None:
        """Inicializa o provedor com o ID que deverá falhar.

        Args:
            id_com_falha: ID da conduta que provocará a interrupção.
        """
        self.id_com_falha = id_com_falha
        self.ids_recebidos: list[int] = []

    def gerar_conteudo(self, prompt: str) -> str:
        """Retorna uma resposta simulada ou interrompe o processamento.

        Args:
            prompt: Prompt recebido do pipeline.

        Returns:
            Resposta JSON simulada da LLM.

        Raises:
            RuntimeError: Quando o prompt contém o ID configurado para falha.
        """
        id_registro = _extrair_id_do_prompt(prompt)
        self.ids_recebidos.append(id_registro)

        if id_registro == self.id_com_falha:
            raise RuntimeError("Interrupção simulada da LLM.")

        return _criar_resposta_json(id_registro)


class ProvedorFalsoBemSucedido:
    """Simula uma LLM que responde a todos os registros recebidos."""

    def __init__(self) -> None:
        """Inicializa o provedor falso."""
        self.ids_recebidos: list[int] = []

    def gerar_conteudo(self, prompt: str) -> str:
        """Retorna uma resposta JSON simulada.

        Args:
            prompt: Prompt recebido do pipeline.

        Returns:
            Resposta JSON simulada da LLM.
        """
        id_registro = _extrair_id_do_prompt(prompt)
        self.ids_recebidos.append(id_registro)

        return _criar_resposta_json(id_registro)


def _extrair_id_do_prompt(prompt: str) -> int:
    """Extrai o ID incluído no prompt de teste.

    Args:
        prompt: Prompt gerado pelo construtor.

    Returns:
        ID do registro correspondente ao prompt.

    Raises:
        AssertionError: Se o prompt de teste não contiver um ID.
    """
    marcador = "ID_TESTE:"
    linha_id = next(
        linha for linha in prompt.splitlines()
        if linha.startswith(marcador)
    )

    return int(linha_id.removeprefix(marcador))


def _criar_resposta_json(id_registro: int) -> str:
    """Cria uma resposta JSON previsível para a integração.

    Args:
        id_registro: ID do registro classificado.

    Returns:
        Resposta textual no formato esperado pelo parser.
    """
    return json.dumps(
        {
            "classe": "peculato",
            "justificativa": (
                f"Resposta integrada para o registro {id_registro}."
            ),
        }
    )


def _criar_configuracao(
    tmp_path: Path,
) -> ConfiguracaoAplicacao:
    """Cria uma configuração isolada para o teste de integração.

    Args:
        tmp_path: Diretório temporário fornecido pelo pytest.

    Returns:
        Configuração da aplicação apontando para arquivos temporários.
    """
    caminho_dados = tmp_path / "data"
    caminho_organizado = caminho_dados / "organized"

    caminho_organizado.mkdir(parents=True)

    return ConfiguracaoAplicacao(
        paths=ConfiguracaoCaminhos(
            data=caminho_dados,
            organized=caminho_organizado,
            classified=caminho_dados / "classified",
            results=caminho_dados / "results",
            taxonomy=caminho_dados / "taxonomy.json",
        ),
        datasets=ConfiguracaoDatasets(
            active_dataset="dataset_integracao.jsonl",
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


def _preparar_arquivos(
    configuracao: ConfiguracaoAplicacao,
) -> Path:
    """Cria dataset e progresso iniciais para o teste.

    Args:
        configuracao: Configuração temporária da aplicação.

    Returns:
        Caminho do arquivo de progresso.
    """
    caminho_dataset = configuracao.datasets.active_dataset_path
    caminho_progresso = (
        configuracao.paths.data / "progresso_processamento.json"
    )

    caminho_dataset.write_text(
        '{"id": 1, "nível": "fácil", '
        '"texto": "Primeira conduta.", '
        '"classe_correta": "peculato"}\n'
        '{"id": 2, "nível": "médio", '
        '"texto": "Segunda conduta.", '
        '"classe_correta": "peculato"}\n',
        encoding="utf-8",
    )

    caminho_progresso.parent.mkdir(parents=True, exist_ok=True)
    caminho_progresso.write_text(
        json.dumps(
            {
                "dataset_integracao.jsonl": {
                    "ultimo_id_processado": 0,
                    "ultima_linha_processada": 0,
                    "status": "em_andamento",
                }
            }
        ),
        encoding="utf-8",
    )

    return caminho_progresso


def _adicionar_id_ao_prompt(monkeypatch) -> None:
    """Adiciona temporariamente o ID ao prompt usado pelos provedores falsos.

    Args:
        monkeypatch: Fixture do pytest para substituição temporária.
    """
    from src.prompts import construtor

    montar_prompt_original = construtor.montar_prompt

    def montar_prompt_com_id(registro):
        prompt = montar_prompt_original(registro)
        return f"ID_TESTE:{registro['id']}\n{prompt}"

    monkeypatch.setattr(
        construtor,
        "montar_prompt",
        montar_prompt_com_id,
    )

    import src.pipeline as pipeline

    monkeypatch.setattr(
        pipeline,
        "montar_prompt",
        montar_prompt_com_id,
    )


def test_deve_retomar_processamento_apos_interrupcao(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Verifica leitura, LLM, parsing, persistência e retomada."""
    configuracao = _criar_configuracao(tmp_path)
    caminho_progresso = _preparar_arquivos(configuracao)
    _adicionar_id_ao_prompt(monkeypatch)

    provedor_com_falha = ProvedorFalsoComFalha(id_com_falha=2)

    with pytest.raises(
        RuntimeError,
        match="Interrupção simulada",
    ):
        executar_pipeline(
            configuracao=configuracao,
            provedor=provedor_com_falha,
        )

    caminho_resultados = (
        configuracao.paths.results
        / "resultados_dataset_integracao.jsonl"
    )
    resultados_apos_falha = caminho_resultados.read_text(
        encoding="utf-8"
    ).splitlines()
    progresso_apos_falha = json.loads(
        caminho_progresso.read_text(encoding="utf-8")
    )["dataset_integracao.jsonl"]

    assert provedor_com_falha.ids_recebidos == [1, 2]
    assert len(resultados_apos_falha) == 1
    assert json.loads(resultados_apos_falha[0])["id"] == 1
    assert progresso_apos_falha["ultimo_id_processado"] == 1
    assert progresso_apos_falha["status"] == "em_andamento"

    provedor_bem_sucedido = ProvedorFalsoBemSucedido()

    executar_pipeline(
        configuracao=configuracao,
        provedor=provedor_bem_sucedido,
    )

    resultados_finais = caminho_resultados.read_text(
        encoding="utf-8"
    ).splitlines()
    progresso_final = json.loads(
        caminho_progresso.read_text(encoding="utf-8")
    )["dataset_integracao.jsonl"]

    assert provedor_bem_sucedido.ids_recebidos == [2]
    assert [json.loads(linha)["id"] for linha in resultados_finais] == [1, 2]
    assert progresso_final["ultimo_id_processado"] == 2
    assert progresso_final["status"] == "concluido"