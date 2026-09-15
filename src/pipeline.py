"""Orquestração do processamento incremental das condutas."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from src.config import CONFIG, ConfiguracaoAplicacao
from src.leitura.leitor_jsonl import ler_jsonl_pendente
from src.llm.base import ProvedorLLM
from src.llm.factory import criar_provedor_llm
from src.parsing.resposta import limpar_converter_texto
from src.progresso.repositorio import (
    ProgressoProcessamento,
    carregar_progresso,
    salvar_progresso_atomico,
)
from src.prompts.construtor import montar_prompt
from src.resultados.construtor import montar_resultado
from src.resultados.repositorio import (
    resultado_ja_salvo,
    salvar_resultado,
)


logger = logging.getLogger(__name__)


def _obter_caminho_progresso(configuracao: ConfiguracaoAplicacao) -> Path:
    """Obtém o caminho do arquivo de progresso do projeto.

    Args:
        configuracao: Configuração carregada da aplicação.

    Returns:
        Caminho absoluto do arquivo de progresso.
    """
    return configuracao.paths.data / "progresso_processamento.json"


def _obter_chave_progresso(configuracao: ConfiguracaoAplicacao) -> str:
    """Gera a chave de identificação do progresso combinando modelo e dataset.

    Args:
        configuracao: Configuração carregada da aplicação.

    Returns:
        Chave no formato 'nome_modelo:nome_dataset'.
    """
    nome_modelo = configuracao.llm.active_model
    nome_dataset = configuracao.datasets.active_dataset
    return f"{nome_modelo}:{nome_dataset}"


def _obter_caminho_resultados(
    configuracao: ConfiguracaoAplicacao,
) -> Path:
    """Obtém o arquivo JSONL classificado do dataset ativo.

    Args:
        configuracao: Configuração carregada da aplicação.

    Returns:
        Caminho absoluto do arquivo de resultados.
    """
    nome_dataset = configuracao.datasets.active_dataset
    nome_dataset = nome_dataset.removesuffix(".jsonl")
    nome_dataset = nome_dataset.removesuffix("_organizado")
    nome_dataset = nome_dataset.removeprefix("dataset_")
    nome_modelo = configuracao.llm.active_model
    nome_resultado = (
        f"resultados_classificados_{nome_modelo}_"
        f"dataset_{nome_dataset}.jsonl"
    )

    return configuracao.paths.classified / nome_resultado


def _criar_progresso_atualizado(
    progresso: ProgressoProcessamento,
    id_registro: int,
    status: str = "em_andamento",
) -> ProgressoProcessamento:
    """Cria uma nova versão imutável do progresso.

    Args:
        progresso: Progresso anterior do dataset.
        id_registro: ID processado com sucesso.
        status: Novo estado do processamento.

    Returns:
        Novo progresso validado.
    """
    return ProgressoProcessamento(
        ultimo_id_processado=id_registro,
        ultima_linha_processada=progresso.ultima_linha_processada + 1,
        status=status,
    )


def _classificar_registro(
    registro: Mapping[str, Any],
    provedor: ProvedorLLM,
) -> dict[str, str | int]:
    """Monta o prompt, consulta a LLM e constrói o resultado.

    Args:
        registro: Registro original do dataset.
        provedor: Provedor de LLM configurado.

    Returns:
        Resultado normalizado pronto para persistência.
    """
    prompt = montar_prompt(registro)
    resposta_bruta = provedor.gerar_conteudo(prompt)
    resposta_validada = limpar_converter_texto(resposta_bruta)

    return montar_resultado(registro, resposta_validada)


def _processar_registro(
    registro: Mapping[str, Any],
    progresso: ProgressoProcessamento,
    provedor: ProvedorLLM,
    caminho_resultados: Path,
    caminho_progresso: Path,
    chave_progresso: str,
) -> ProgressoProcessamento:
    """Processa um registro e atualiza o progresso após sua persistência.

    Args:
        registro: Registro original do dataset.
        progresso: Progresso atual.
        provedor: Provedor de LLM configurado.
        caminho_resultados: Arquivo JSONL de resultados.
        caminho_progresso: Arquivo JSON de progresso.
        chave_progresso: Chave única do progresso (modelo:dataset).

    Returns:
        Progresso atualizado após o processamento.

    Raises:
        Exception: Propaga falhas de prompt, LLM, parsing ou persistência.
    """
    id_registro = registro["id"]

    if (
        caminho_resultados.exists()
        and resultado_ja_salvo(caminho_resultados, id_registro)
    ):
        logger.info(
            "Resultado do registro %s ja existe; chamada a LLM ignorada.",
            id_registro,
        )
        progresso_atualizado = _criar_progresso_atualizado(
            progresso,
            id_registro,
        )
        salvar_progresso_atomico(
            caminho_progresso,
            chave_progresso,
            progresso_atualizado,
        )
        return progresso_atualizado

    resultado = _classificar_registro(registro, provedor)

    # O resultado precisa estar persistido antes do avanço do progresso.
    salvar_resultado(caminho_resultados, resultado)

    progresso_atualizado = _criar_progresso_atualizado(
        progresso,
        id_registro,
    )
    salvar_progresso_atomico(
        caminho_progresso,
        chave_progresso,
        progresso_atualizado,
    )

    logger.info(
        "Registro %s processado e progresso atualizado.",
        id_registro,
    )

    return progresso_atualizado


def executar_pipeline(
    configuracao: ConfiguracaoAplicacao = CONFIG,
    provedor: ProvedorLLM | None = None,
) -> None:
    """Executa o processamento incremental do dataset ativo para o modelo ativo.

    Args:
        configuracao: Configuração da aplicação.
        provedor: Provedor opcional para injeção em testes. Quando ausente,
            será criado pela factory configurada.

    Raises:
        FileNotFoundError: Se o dataset não existir.
        Exception: Se alguma etapa do processamento falhar.
    """
    caminho_dataset = configuracao.datasets.active_dataset_path
    chave_progresso = _obter_chave_progresso(configuracao)
    caminho_progresso = _obter_caminho_progresso(configuracao)
    caminho_resultados = _obter_caminho_resultados(configuracao)

    progresso = carregar_progresso(
        caminho_progresso,
        chave_progresso,
    )
    provedor_configurado = provedor or criar_provedor_llm(
        configuracao.llm
    )

    for registro in ler_jsonl_pendente(
        caminho_dataset,
        progresso,
    ):
        progresso = _processar_registro(
            registro=registro,
            progresso=progresso,
            provedor=provedor_configurado,
            caminho_resultados=caminho_resultados,
            caminho_progresso=caminho_progresso,
            chave_progresso=chave_progresso,
        )

    if progresso.status != "concluido":
        progresso_final = ProgressoProcessamento(
            ultimo_id_processado=progresso.ultimo_id_processado,
            ultima_linha_processada=progresso.ultima_linha_processada,
            status="concluido",
        )
        salvar_progresso_atomico(
            caminho_progresso,
            chave_progresso,
            progresso_final,
        )

    logger.info(
        "Processamento do modelo %s no dataset %s concluido.",
        configuracao.llm.active_model,
        configuracao.datasets.active_dataset,
    )