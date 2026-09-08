"""Construção de prompts para classificação penal por modelos de linguagem."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final


CLASSES_PENAIS: Final[tuple[str, ...]] = (
	"peculato",
	"peculato_culposo",
	"peculato_mediante_erro_de_outrem",
	"concussao",
	"corrupcao_passiva",
	"prevaricacao",
	"condescendencia_criminosa",
	"advocacia_administrativa",
	"violacao_de_sigilo_funcional",
	"nao_se_enquadra",
)


MODELO_PROMPT: Final[str] = """Você é um especialista em Direito Penal brasileiro, com foco em crimes contra a Administração Pública.

Analise a conduta descrita e classifique-a em uma das classes penais permitidas.

Classes permitidas:
{classes_penais}

Responda exclusivamente como um objeto JSON válido, sem markdown ou texto adicional:
{{
	"classe": "uma das classes permitidas",
	"justificativa": "explicação objetiva da classificação"
}}

Conduta:
{texto}
"""


class ErroConstrucaoPrompt(ValueError):
	"""Representa uma entrada inválida para construção do prompt."""


def _obter_texto_conduta(registro: Mapping[str, Any]) -> str:
	"""Obtém e valida o texto da conduta presente no registro.

	Args:
		registro: Registro do dataset que contém a conduta.

	Returns:
		Texto da conduta sem espaços excedentes nas extremidades.

	Raises:
		ErroConstrucaoPrompt: Se o registro não for um mapeamento ou se o
			campo `texto` estiver ausente, não for textual ou estiver vazio.
	"""
	if not isinstance(registro, Mapping):
		raise ErroConstrucaoPrompt(
			"O registro da conduta deve ser um mapeamento."
		)

	texto = registro.get("texto")

	if not isinstance(texto, str) or not texto.strip():
		raise ErroConstrucaoPrompt(
			"O campo 'texto' deve ser uma string não vazia."
		)

	return texto.strip()


def _formatar_classes_penais() -> str:
	"""Formata as classes penais para inclusão no prompt.

	Returns:
		Lista textual das classes penais permitidas, uma por linha.
	"""
	return "\n".join(
		f"- {classe_penal}" for classe_penal in CLASSES_PENAIS
	)


def montar_prompt(registro: Mapping[str, Any]) -> str:
	"""Monta o prompt pronto para envio ao provedor de LLM.

	Esta função transforma um registro do dataset em uma instrução
	estruturada. Ela não realiza chamadas externas nem interpreta a resposta
	do modelo.

	Args:
		registro: Registro do dataset contendo o campo `texto`.

	Returns:
		Prompt textual pronto para envio ao provedor de LLM.

	Raises:
		ErroConstrucaoPrompt: Se o registro ou o texto da conduta for inválido.
	"""
	texto = _obter_texto_conduta(registro)

	return MODELO_PROMPT.format(
		classes_penais=_formatar_classes_penais(),
		texto=texto,
	)
