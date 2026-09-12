"""Testes do ponto de entrada da aplicação."""

from unittest.mock import Mock

import src.init as modulo_init


def test_deve_inicializar_aplicacao_com_sucesso(
    monkeypatch,
) -> None:
    """Verifica o caminho feliz da inicialização."""
    configurar_logging = Mock()
    executar_pipeline = Mock()

    monkeypatch.setattr(
        modulo_init,
        "configurar_logging",
        configurar_logging,
    )
    monkeypatch.setattr(
        modulo_init,
        "executar_pipeline",
        executar_pipeline,
    )

    codigo_saida = modulo_init.inicializar_aplicacao()

    assert codigo_saida == 0
    configurar_logging.assert_called_once_with()
    executar_pipeline.assert_called_once_with()


def test_deve_retornar_codigo_de_falha_em_erro_fatal(
    monkeypatch,
) -> None:
    """Verifica o tratamento de uma falha fatal do pipeline."""
    configurar_logging = Mock()
    executar_pipeline = Mock(
        side_effect=RuntimeError("falha simulada")
    )

    monkeypatch.setattr(
        modulo_init,
        "configurar_logging",
        configurar_logging,
    )
    monkeypatch.setattr(
        modulo_init,
        "executar_pipeline",
        executar_pipeline,
    )

    codigo_saida = modulo_init.inicializar_aplicacao()

    assert codigo_saida == 1
    configurar_logging.assert_called_once_with()
    executar_pipeline.assert_called_once_with()