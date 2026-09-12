"""Testes do repositório de resultados em JSONL."""

import json
from pathlib import Path

import pytest

from src.resultados.repositorio import (
    ErroRepositorioResultados,
    resultado_ja_salvo,
    salvar_resultado,
)


def test_deve_salvar_resultado_em_jsonl(
    tmp_path: Path,
) -> None:
    """Verifica a persistência de um resultado como uma linha JSON."""
    caminho_resultados = tmp_path / "resultados.jsonl"
    resultado = {
        "id": 1,
        "nivel": "fácil",
        "texto": "Conduta analisada.",
        "classe_real": "peculato",
        "classe_predita": "peculato",
        "justificativa": "Classificação compatível.",
    }

    salvar_resultado(caminho_resultados, resultado)

    linhas = caminho_resultados.read_text(encoding="utf-8").splitlines()

    assert len(linhas) == 1
    assert json.loads(linhas[0]) == resultado


def test_deve_criar_pasta_de_resultados(
    tmp_path: Path,
) -> None:
    """Verifica a criação automática da pasta de destino."""
    caminho_resultados = tmp_path / "resultados" / "classificacoes.jsonl"
    resultado = {"id": 1}

    salvar_resultado(caminho_resultados, resultado)

    assert caminho_resultados.exists()


def test_deve_identificar_id_ja_salvo(
    tmp_path: Path,
) -> None:
    """Verifica a localização de um ID já persistido."""
    caminho_resultados = tmp_path / "resultados.jsonl"
    salvar_resultado(caminho_resultados, {"id": 10})

    assert resultado_ja_salvo(caminho_resultados, 10) is True
    assert resultado_ja_salvo(caminho_resultados, 11) is False


def test_deve_ignorar_linhas_vazias_ao_verificar_id(
    tmp_path: Path,
) -> None:
    """Verifica que linhas vazias não interrompem a busca."""
    caminho_resultados = tmp_path / "resultados.jsonl"
    caminho_resultados.write_text(
        "\n"
        '{"id": 2}\n'
        "   \n",
        encoding="utf-8",
    )

    assert resultado_ja_salvo(caminho_resultados, 2) is True


@pytest.mark.parametrize(
    "resultado",
    [
        {"id": -1},
        {"id": "1"},
        {"id": True},
        {},
    ],
)
def test_deve_rejeitar_resultado_com_id_invalido(
    tmp_path: Path,
    resultado: dict[str, object],
) -> None:
    """Verifica a rejeição de resultados com identificadores inválidos."""
    caminho_resultados = tmp_path / "resultados.jsonl"

    with pytest.raises(
        ErroRepositorioResultados,
        match="id",
    ):
        salvar_resultado(caminho_resultados, resultado)


def test_deve_rejeitar_json_corrompido_ao_verificar_id(
    tmp_path: Path,
) -> None:
    """Verifica o tratamento de corrupção no arquivo JSONL."""
    caminho_resultados = tmp_path / "resultados.jsonl"
    caminho_resultados.write_text(
        '{"id": 1}\n'
        '{"id": inválido}\n',
        encoding="utf-8",
    )

    with pytest.raises(
        ErroRepositorioResultados,
        match="linha 2",
    ):
        resultado_ja_salvo(caminho_resultados, 2)