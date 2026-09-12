"""Provedor Google para comunicação com modelos Gemini."""

from __future__ import annotations

import time


class ErroGoogleProvider(RuntimeError):
    """Representa uma falha na configuração ou comunicação com o Google."""


class GoogleProvider:
    """Implementa o contrato de comunicação com modelos Gemini.

    Esta classe conhece somente o SDK Google e os parâmetros necessários para
    enviar prompts. Não acessa `config.yaml`, `.env`, datasets, progresso,
    parser ou construtor de prompts.

    Args:
        model_name: Nome do modelo Gemini utilizado na requisição.
        api_key: Chave de autenticação da API Google.
        request_delay_seconds: Intervalo em segundos entre requisições.
    """

    def __init__(
        self,
        model_name: str,
        api_key: str | None,
        request_delay_seconds: float = 0.0,
    ) -> None:
        """Inicializa o provedor Google.

        Args:
            model_name: Nome do modelo Gemini.
            api_key: Chave de autenticação da API Google.
            request_delay_seconds: Intervalo em segundos entre requisições.

        Raises:
            ValueError: Se o nome do modelo, a chave ou o atraso forem inválidos.
            ErroGoogleProvider: Se o SDK Google não estiver instalado.
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

        try:
            from google import genai
        except ModuleNotFoundError as erro:
            raise ErroGoogleProvider(
                "A dependencia 'google-genai' nao esta instalada."
            ) from erro

        self._model_name = model_name.strip()
        self._request_delay_seconds = float(request_delay_seconds)
        self._cliente = genai.Client(api_key=api_key.strip())

    def gerar_conteudo(self, prompt: str) -> str:
        """Envia um prompt ao Gemini e retorna a resposta textual.

        Respeita o intervalo de tempo configurado em `request_delay_seconds`
        aguardando o tempo determinado antes de realizar a chamada à API.

        Args:
            prompt: Texto completo da instrução para o modelo.

        Returns:
            Texto bruto retornado pelo Gemini.

        Raises:
            ValueError: Se o prompt for vazio ou inválido.
            ErroGoogleProvider: Se a API retornar uma resposta sem texto
                ou ocorrer uma falha na comunicação.
        """
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError(
                "prompt deve ser uma string não vazia."
            )

        if self._request_delay_seconds > 0:
            time.sleep(self._request_delay_seconds)

        try:
            resposta = self._cliente.models.generate_content(
                model=self._model_name,
                contents=prompt.strip(),
                config={"temperature": 0.0},
            )
        except Exception as erro:
            raise ErroGoogleProvider(
                "Falha ao solicitar conteudo ao provedor Google."
            ) from erro

        texto = getattr(resposta, "text", None)

        if not isinstance(texto, str) or not texto.strip():
            raise ErroGoogleProvider(
                "O provedor Google retornou uma resposta sem texto."
            )

        return texto.strip()