"""Provedor DeepSeek Flash (Max) por meio da API OpenRouter."""

from __future__ import annotations

import time


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
NIVEL_RACIOCINIO = "max"


class ErroDeepSeekProvider(RuntimeError):
    """Representa uma falha na configuração ou comunicação com DeepSeek."""


class DeepSeekProvider:
    """Envia prompts ao modelo DeepSeek Flash via OpenRouter.

    Args:
        model_name: Identificador do modelo no OpenRouter.
        api_key: Chave de API do OpenRouter.
        request_delay_seconds: Intervalo em segundos entre as requisições.
    """

    def __init__(
        self,
        model_name: str,
        api_key: str | None,
        request_delay_seconds: float = 0.0,
    ) -> None:
        """Inicializa cliente OpenAI compatível configurado para OpenRouter.

        Args:
            model_name: Identificador do modelo no OpenRouter.
            api_key: Chave de API do OpenRouter.
            request_delay_seconds: Intervalo entre chamadas à API.

        Raises:
            ValueError: Se os parâmetros informados forem inválidos.
            ErroDeepSeekProvider: Se o SDK OpenAI não estiver instalado.
        """
        if not isinstance(model_name, str) or not model_name.strip():
            raise ValueError("model_name deve ser uma string não vazia.")

        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError("api_key deve ser uma string não vazia.")

        if (
            isinstance(request_delay_seconds, bool)
            or not isinstance(request_delay_seconds, (int, float))
            or request_delay_seconds < 0
        ):
            raise ValueError(
                "request_delay_seconds deve ser um número não negativo."
            )

        try:
            from openai import OpenAI
        except ModuleNotFoundError as erro:
            raise ErroDeepSeekProvider(
                "A dependência 'openai' não está instalada."
            ) from erro

        self._model_name = model_name.strip()
        self._request_delay_seconds = float(request_delay_seconds)
        self._cliente = OpenAI(
            api_key=api_key.strip(),
            base_url=OPENROUTER_BASE_URL,
        )

    def gerar_conteudo(self, prompt: str) -> str:
        """Envia o prompt ao modelo e retorna a resposta textual.

        Args:
            prompt: Prompt completo gerado pelo pipeline.

        Returns:
            Texto retornado pelo modelo.

        Raises:
            ValueError: Se o prompt for vazio ou inválido.
            ErroDeepSeekProvider: Se a API falhar ou não retornar texto.
        """
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("prompt deve ser uma string não vazia.")

        if self._request_delay_seconds > 0:
            time.sleep(self._request_delay_seconds)

        try:
            resposta = self._cliente.chat.completions.create(
                model=self._model_name,
                messages=[
                    {
                        "role": "user",
                        "content": prompt.strip(),
                    }
                ],
                temperature=0.0,
                extra_body={
                    "reasoning": {
                        "effort": NIVEL_RACIOCINIO,
                    },
                },
            )
        except Exception as erro:
            raise ErroDeepSeekProvider(
                "Falha ao solicitar conteúdo ao DeepSeek via OpenRouter."
            ) from erro

        texto = None
        if resposta.choices:
            texto = resposta.choices[0].message.content

        if not isinstance(texto, str) or not texto.strip():
            raise ErroDeepSeekProvider(
                "O OpenRouter retornou uma resposta sem texto."
            )

        return texto.strip()
