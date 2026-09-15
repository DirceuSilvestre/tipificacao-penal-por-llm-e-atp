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
    """Representa o progresso de um dataset por modelo.

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
    chave_progresso: str,
) -> ProgressoProcessamento:
    """Carrega o progresso de uma combinação modelo:dataset.

    Se a chave informada não for encontrada no arquivo JSON, inicializa
    automaticamente um estado padrão "pendente".

    Args:
        caminho: Caminho do arquivo de progresso.
        chave_progresso: Chave do progresso (ex: 'gemini_flash:dataset_curado.jsonl').

    Returns:
        Progresso do modelo e dataset informados.

    Raises:
        ErroProgresso: Se o caminho for inválido ou o JSON estiver corrompido.
    """
    if not chave_progresso.strip():
        raise ErroProgresso("chave_progresso não pode ser vazia.")

    if not caminho.exists():
        return ProgressoProcessamento(
            ultimo_id_processado=0,
            ultima_linha_processada=0,
            status="pendente",
        )

    try:
        with caminho.open("r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except json.JSONDecodeError as erro:
        raise ErroProgresso(
            f"Arquivo de progresso inválido: {caminho}"
        ) from erro

    dados_por_chave = _validar_mapeamento(dados, "raiz")

    if chave_progresso not in dados_por_chave:
        return ProgressoProcessamento(
            ultimo_id_processado=0,
            ultima_linha_processada=0,
            status="pendente",
        )

    dados_progresso = _validar_mapeamento(
        dados_por_chave[chave_progresso],
        f"progresso de {chave_progresso}",
    )

    return _converter_progresso(dados_progresso)


def salvar_progresso_atomico(
    caminho: Path,
    chave_progresso: str,
    progresso: ProgressoProcessamento,
) -> None:
    """Atualiza o progresso de um modelo e dataset de forma atômica.

    O conteúdo é escrito em arquivo temporário no mesmo diretório do arquivo
    original. Após a sincronização física dos dados, o arquivo temporário
    substitui o original em uma única operação do sistema operacional.

    Args:
        caminho: Caminho do arquivo de progresso.
        chave_progresso: Chave única do progresso (ex: 'modelo:dataset.jsonl').
        progresso: Novo progresso validado.

    Raises:
        ErroProgresso: Se a chave for vazia.
        OSError: Se o arquivo não puder ser escrito ou substituído.
    """
    if not chave_progresso.strip():
        raise ErroProgresso("chave_progresso não pode ser vazia.")

    caminho.parent.mkdir(parents=True, exist_ok=True)

    dados_existentes: dict[str, Any] = {}

    if caminho.exists():
        with caminho.open("r", encoding="utf-8") as arquivo:
            dados_carregados = json.load(arquivo)

        dados_existentes = dict(
            _validar_mapeamento(dados_carregados, "raiz")
        )

    dados_existentes[chave_progresso] = asdict(progresso)

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