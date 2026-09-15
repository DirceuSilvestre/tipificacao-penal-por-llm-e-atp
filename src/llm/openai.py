"""Provedor OpenAI para comunicação com modelos GPT e compatíveis."""

from __future__ import annotations

import time


class ErroOpenAIProvider(RuntimeError):
    """Representa uma falha na configuração ou comunicação com a OpenAI."""


class OpenAIProvider:
    """Implementa o contrato de comunicação com modelos OpenAI (GPT) e compatíveis.

    Esta classe conhece somente o SDK OpenAI e os parâmetros necessários para
    enviar prompts. Não acessa `config.yaml`, `.env`, datasets, progresso,
    parser ou construtor de prompts.

    Args:
        model_name: Nome do modelo utilizado na requisição (ex: "gpt-4o-mini" ou "openai/gpt-oss-120b").
        api_key: Chave de autenticação da API.
        request_delay_seconds: Intervalo em segundos entre requisições.
        base_url: URL base opcional para APIs compatíveis com a OpenAI (ex: Groq).
    """

    def __init__(
        self,
        model_name: str,
        api_key: str | None,
        request_delay_seconds: float = 0.0,
        base_url: str | None = None,
    ) -> None:
        """Inicializa o provedor OpenAI / compatível.

        Args:
            model_name: Nome do modelo.
            api_key: Chave de autenticação da API.
            request_delay_seconds: Intervalo em segundos entre requisições.
            base_url: URL base opcional para chamadas customizadas.

        Raises:
            ValueError: Se o nome do modelo, a chave, o atraso ou base_url forem inválidos.
            ErroOpenAIProvider: Se o SDK OpenAI não estiver instalado.
        """
        if not isinstance(model_name, str) or not model_name.strip():
            raise ValueError(
                "model_name deve ser uma string não vazia."
            )

        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError(
                "api_key deve ser uma string não vazia."
            )

        if (
            isinstance(request_delay_seconds, bool)
            or not isinstance(request_delay_seconds, (int, float))
            or request_delay_seconds < 0
        ):
            raise ValueError(
                "request_delay_seconds deve ser um número não negativo."
            )

        if base_url is not None and (
            not isinstance(base_url, str) or not base_url.strip()
        ):
            raise ValueError(
                "base_url, quando informado, deve ser uma string não vazia."
            )

        try:
            from openai import OpenAI
        except ModuleNotFoundError as erro:
            raise ErroOpenAIProvider(
                "A dependência 'openai' não está instalada."
            ) from erro

        self._model_name = model_name.strip()
        self._request_delay_seconds = float(request_delay_seconds)

        parametros_cliente = {"api_key": api_key.strip()}
        if base_url is not None:
            parametros_cliente["base_url"] = base_url.strip()

        self._cliente = OpenAI(**parametros_cliente)

    def gerar_conteudo(self, prompt: str) -> str:
        """Envia um prompt à API e retorna a resposta textual.

        Respeita o intervalo de tempo configurado em `request_delay_seconds`
        aguardando o tempo determinado antes de realizar a chamada à API.

        Args:
            prompt: Texto completo da instrução para o modelo.

        Returns:
            Texto bruto retornado pela API.

        Raises:
            ValueError: Se o prompt for vazio ou inválido.
            ErroOpenAIProvider: Se a API retornar uma resposta sem texto
                ocorrer uma falha na comunicação.
        """
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError(
                "prompt deve ser uma string não vazia."
            )

        if self._request_delay_seconds > 0:
            time.sleep(self._request_delay_seconds)

        try:
            resposta = self._cliente.chat.completions.create(
                model=self._model_name,
                messages=[
                    {"role": "user", "content": prompt.strip()}
                ],
                temperature=0.0,
            )
        except Exception as erro:
            raise ErroOpenAIProvider(
                "Falha ao solicitar conteúdo ao provedor OpenAI."
            ) from erro

        texto = None
        if resposta.choices and len(resposta.choices) > 0:
            texto = resposta.choices[0].message.content

        if not isinstance(texto, str) or not texto.strip():
            raise ErroOpenAIProvider(
                "O provedor OpenAI retornou uma resposta sem texto."
            )

        return texto.strip()