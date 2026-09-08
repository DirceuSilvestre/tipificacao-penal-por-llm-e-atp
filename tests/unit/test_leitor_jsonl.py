"""Testes do leitor incremental de arquivos JSONL."""

import json
from pathlib import Path

import pytest

from src.leitura.leitor_jsonl import (
    ErroLeituraJsonl,
    ler_jsonl_a_partir_do_id,
    ler_jsonl_pendente,
)
from src.progresso.repositorio import ProgressoProcessamento


def test_deve_ler_somente_registros_a_partir_do_id_inicial(
    tmp_path: Path,
) -> None:
    """Verifica o início da leitura a partir do ID informado."""
    caminho_dataset = tmp_path / "dataset.jsonl"
    caminho_dataset.write_text(
        '{"id": 1, "texto": "primeiro"}\n'
        '{"id": 2, "texto": "segundo"}\n'
        '{"id": 3, "texto": "terceiro"}\n',
        encoding="utf-8",
    )

    registros = list(
        ler_jsonl_a_partir_do_id(
            caminho=caminho_dataset,
            id_inicial=2,
        )
    )

    assert [registro["id"] for registro in registros] == [2, 3]


def test_deve_ler_somente_registros_pendentes(
    tmp_path: Path,
) -> None:
    """Verifica a retomada baseada no progresso salvo."""
    caminho_dataset = tmp_path / "dataset.jsonl"
    caminho_dataset.write_text(
        '{"id": 1, "texto": "primeiro"}\n'
        '{"id": 2, "texto": "segundo"}\n'
        '{"id": 3, "texto": "terceiro"}\n',
        encoding="utf-8",
    )
    progresso = ProgressoProcessamento(
        ultimo_id_processado=1,
        ultima_linha_processada=1,
        status="em_andamento",
    )

    registros = list(
        ler_jsonl_pendente(
            caminho=caminho_dataset,
            progresso=progresso,
        )
    )

    assert [registro["id"] for registro in registros] == [2, 3]


def test_deve_ignorar_linhas_vazias(
    tmp_path: Path,
) -> None:
    """Verifica que linhas vazias não interrompem a leitura."""
    caminho_dataset = tmp_path / "dataset.jsonl"
    caminho_dataset.write_text(
        "\n"
        '{"id": 1, "texto": "primeiro"}\n'
        "   \n"
        '{"id": 2, "texto": "segundo"}\n',
        encoding="utf-8",
    )

    registros = list(
        ler_jsonl_a_partir_do_id(
            caminho=caminho_dataset,
            id_inicial=0,
        )
    )

    assert [registro["id"] for registro in registros] == [1, 2]


def test_deve_rejeitar_json_invalido(
    tmp_path: Path,
) -> None:
    """Verifica o tratamento de uma linha com JSON inválido."""
    caminho_dataset = tmp_path / "dataset.jsonl"
    caminho_dataset.write_text(
        '{"id": 1, "texto": "válido"}\n'
        '{"id": 2, "texto": inválido}\n',
        encoding="utf-8",
    )

    with pytest.raises(ErroLeituraJsonl, match="linha 2"):
        list(
            ler_jsonl_a_partir_do_id(
                caminho=caminho_dataset,
                id_inicial=0,
            )
        )


def test_deve_rejeitar_registro_sem_id(
    tmp_path: Path,
) -> None:
    """Verifica a validação do identificador obrigatório."""
    caminho_dataset = tmp_path / "dataset.jsonl"
    caminho_dataset.write_text(
        json.dumps({"texto": "sem identificador"}) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ErroLeituraJsonl, match="campo 'id'"):
        list(
            ler_jsonl_a_partir_do_id(
                caminho=caminho_dataset,
                id_inicial=0,
            )
        )