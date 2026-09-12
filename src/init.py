"""Ponto de entrada da aplicação."""

from __future__ import annotations

import logging
import logging.config
from copy import deepcopy
from pathlib import Path

from src.config import CONFIG, ConfiguracaoAplicacao
from src.pipeline import executar_pipeline


logger = logging.getLogger("app")


def _criar_pasta_de_logs(
    configuracao: ConfiguracaoAplicacao,
) -> None:
    """Cria a pasta do arquivo de log configurado.

    Args:
        configuracao: Configuração completa da aplicação.

    Raises:
        OSError: Se a pasta não puder ser criada.
    """
    dados_logging = configuracao.logging
    handlers = dados_logging.get("handlers", {})

    if not isinstance(handlers, dict):
        return

    handler_arquivo = handlers.get("file")

    if not isinstance(handler_arquivo, dict):
        return

    nome_arquivo = handler_arquivo.get("filename")

    if isinstance(nome_arquivo, str) and nome_arquivo.strip():
        Path(nome_arquivo).parent.mkdir(
            parents=True,
            exist_ok=True,
        )


def configurar_logging(
    configuracao: ConfiguracaoAplicacao = CONFIG,
) -> None:
    """Configura o sistema de logs a partir do YAML da aplicação.

    Args:
        configuracao: Configuração completa da aplicação.

    Raises:
        OSError: Se a pasta de logs não puder ser criada.
        ValueError: Se a configuração de logging for inválida.
    """
    _criar_pasta_de_logs(configuracao)

    logging.config.dictConfig(
        deepcopy(dict(configuracao.logging))
    )


def inicializar_aplicacao() -> int:
    """Inicializa a aplicação e executa o pipeline principal.

    Returns:
        Código de saída zero em caso de sucesso ou um em caso de falha fatal.
    """
    try:
        configurar_logging()
        executar_pipeline()
    except Exception:
        logger.exception(
            "Falha fatal durante a execução da aplicação."
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(inicializar_aplicacao())