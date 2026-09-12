"""Provedor Google para comunicação com modelos Gemini."""

from __future__ import annotations


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
    """

    def __init__(
        self,
        model_name: str,
        api_key: str | None,
    ) -> None:
        """Inicializa o provedor Google.

        Args:
            model_name: Nome do modelo Gemini.
            api_key: Chave de autenticação da API Google.

        Raises:
            ValueError: Se o nome do modelo ou a chave forem inválidos.
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

        try:
            from google import genai
        except ModuleNotFoundError as erro:
            raise ErroGoogleProvider(
                "A dependência 'google-genai' não está instalada."
            ) from erro

        self._model_name = model_name.strip()
        self._cliente = genai.Client(api_key=api_key.strip())

    def gerar_conteudo(self, prompt: str) -> str:
        """Envia um prompt ao Gemini e retorna a resposta textual.

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

        try:
            resposta = self._cliente.models.generate_content(
                model=self._model_name,
                contents=prompt.strip(),
                config={"temperature": 0.0},
            )
        except Exception as erro:
            raise ErroGoogleProvider(
                "Falha ao solicitar conteúdo ao provedor Google."
            ) from erro

        texto = getattr(resposta, "text", None)

        if not isinstance(texto, str) or not texto.strip():
            raise ErroGoogleProvider(
                "O provedor Google retornou uma resposta sem texto."
            )

        return texto.strip()