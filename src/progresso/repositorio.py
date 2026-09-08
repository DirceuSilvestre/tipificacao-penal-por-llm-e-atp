"""Persistência atômica do progresso de processamento dos datasets."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping


STATUS_VALIDOS = frozenset({"pendente", "em_andamento", "concluido"})


class ErroProgresso(ValueError):
    """Representa um progresso ausente ou inválido."""


@dataclass(frozen=True)
class ProgressoProcessamento:
    """Representa o progresso de um dataset.

    Args:
        ultimo_id_processado: Maior ID processado com sucesso.
        ultima_linha_processada: Número da última linha processada.
        status: Estado atual do processamento.

    Raises:
        ErroProgresso: Se algum campo possuir valor inválido.
    """

    ultimo_id_processado: int
    ultima_linha_processada: int
    status: str

    def __post_init__(self) -> None:
        """Valida os campos do progresso após sua criação.

        Raises:
            ErroProgresso: Se um campo possuir valor inválido.
        """
        if (
            isinstance(self.ultimo_id_processado, bool)
            or self.ultimo_id_processado < 0
        ):
            raise ErroProgresso(
                "ultimo_id_processado deve ser um inteiro não negativo."
            )

        if (
            isinstance(self.ultima_linha_processada, bool)
            or self.ultima_linha_processada < 0
        ):
            raise ErroProgresso(
                "ultima_linha_processada deve ser um inteiro não negativo."
            )

        if self.status not in STATUS_VALIDOS:
            raise ErroProgresso(
                f"status inválido: {self.status!r}. "
                f"Valores aceitos: {sorted(STATUS_VALIDOS)}."
            )


def _validar_mapeamento(valor: Any, nome: str) -> Mapping[str, Any]:
    """Valida se um valor é um mapeamento.

    Args:
        valor: Valor a ser validado.
        nome: Nome do campo validado.

    Returns:
        Mapeamento validado.

    Raises:
        ErroProgresso: Se o valor não for um mapeamento.
    """
    if not isinstance(valor, Mapping):
        raise ErroProgresso(f"{nome} deve ser um objeto JSON.")

    return valor


def _validar_inteiro_nao_negativo(valor: Any, nome: str) -> int:
    """Valida um inteiro não negativo.

    Args:
        valor: Valor a ser validado.
        nome: Nome do campo validado.

    Returns:
        Inteiro validado.

    Raises:
        ErroProgresso: Se o valor não for um inteiro não negativo.
    """
    if isinstance(valor, bool) or not isinstance(valor, int) or valor < 0:
        raise ErroProgresso(
            f"{nome} deve ser um inteiro não negativo."
        )

    return valor


def _converter_progresso(
    dados: Mapping[str, Any],
) -> ProgressoProcessamento:
    """Converte um objeto JSON em ProgressoProcessamento.

    Args:
        dados: Dados de um dataset carregados do JSON.

    Returns:
        Progresso validado.

    Raises:
        ErroProgresso: Se algum campo obrigatório estiver ausente ou inválido.
    """
    return ProgressoProcessamento(
        ultimo_id_processado=_validar_inteiro_nao_negativo(
            dados.get("ultimo_id_processado"),
            "ultimo_id_processado",
        ),
        ultima_linha_processada=_validar_inteiro_nao_negativo(
            dados.get("ultima_linha_processada"),
            "ultima_linha_processada",
        ),
        status=dados.get("status"),
    )


def carregar_progresso(
    caminho: Path,
    nome_dataset: str,
) -> ProgressoProcessamento:
    """Carrega o progresso de um dataset.

    Args:
        caminho: Caminho do arquivo de progresso.
        nome_dataset: Nome do dataset cujo progresso será carregado.

    Returns:
        Progresso do dataset informado.

    Raises:
        FileNotFoundError: Se o arquivo de progresso não existir.
        ErroProgresso: Se o JSON ou seus campos forem inválidos.
    """
    if not nome_dataset.strip():
        raise ErroProgresso("nome_dataset não pode ser vazio.")

    try:
        with caminho.open("r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except json.JSONDecodeError as erro:
        raise ErroProgresso(
            f"Arquivo de progresso inválido: {caminho}"
        ) from erro

    dados_por_dataset = _validar_mapeamento(dados, "raiz")

    if nome_dataset not in dados_por_dataset:
        raise ErroProgresso(
            f"Dataset não encontrado no progresso: {nome_dataset}"
        )

    dados_dataset = _validar_mapeamento(
        dados_por_dataset[nome_dataset],
        f"progresso de {nome_dataset}",
    )

    return _converter_progresso(dados_dataset)


def salvar_progresso_atomico(
    caminho: Path,
    nome_dataset: str,
    progresso: ProgressoProcessamento,
) -> None:
    """Atualiza o progresso de um dataset de forma atômica.

    O conteúdo é escrito em arquivo temporário no mesmo diretório do arquivo
    original. Após a sincronização física dos dados, o arquivo temporário
    substitui o original em uma única operação do sistema operacional.

    Args:
        caminho: Caminho do arquivo de progresso.
        nome_dataset: Nome do dataset atualizado.
        progresso: Novo progresso validado do dataset.

    Raises:
        ErroProgresso: Se o nome do dataset for vazio.
        OSError: Se o arquivo não puder ser escrito ou substituído.
    """
    if not nome_dataset.strip():
        raise ErroProgresso("nome_dataset não pode ser vazio.")

    caminho.parent.mkdir(parents=True, exist_ok=True)

    dados_existentes: dict[str, Any] = {}

    if caminho.exists():
        with caminho.open("r", encoding="utf-8") as arquivo:
            dados_carregados = json.load(arquivo)

        dados_existentes = dict(
            _validar_mapeamento(dados_carregados, "raiz")
        )

    dados_existentes[nome_dataset] = asdict(progresso)

    arquivo_temporario: str | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=caminho.parent,
            prefix=f".{caminho.name}.",
            suffix=".tmp",
            delete=False,
        ) as arquivo:
            arquivo_temporario = arquivo.name
            json.dump(
                dados_existentes,
                arquivo,
                ensure_ascii=False,
                indent=4,
            )
            arquivo.write("\n")
            arquivo.flush()
            os.fsync(arquivo.fileno())

        os.replace(arquivo_temporario, caminho)
        arquivo_temporario = None
    finally:
        if arquivo_temporario is not None:
            Path(arquivo_temporario).unlink(missing_ok=True)