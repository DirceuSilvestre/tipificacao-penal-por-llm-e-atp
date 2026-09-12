"""Contrato comum para provedores de modelos de linguagem."""

from __future__ import annotations

from typing import Protocol


class ProvedorLLM(Protocol):
    """Define a interface comum dos provedores de LLM.

    Cada provedor concreto, como Google, OpenAI ou Anthropic, deve
    implementar o método `gerar_conteudo`. O pipeline depende deste contrato,
    e não de um SDK ou provedor específico.

    O contrato não conhece prompts, datasets, progresso, parsing ou
    persistência. Sua única responsabilidade é definir a comunicação mínima
    necessária com um modelo de linguagem.
    """

    def gerar_conteudo(self, prompt: str) -> str:
        """Envia um prompt ao modelo e retorna a resposta textual.

        Args:
            prompt: Texto completo da instrução a ser enviada ao modelo.

        Returns:
            Resposta textual bruta produzida pelo modelo.

        Raises:
            ValueError: Se o prompt for vazio ou inválido.
            Exception: Se o provedor não conseguir concluir a requisição.
        """
        ...