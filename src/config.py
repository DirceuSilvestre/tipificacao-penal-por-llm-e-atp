"""Carregamento e validação da configuração da aplicação."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from os import getenv
from pathlib import Path
from typing import Any, Mapping

import yaml
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
CAMINHO_CONFIGURACAO = BASE_DIR / "config.yaml"

CHAVES_API_POR_PROVEDOR = {
	"google": "GOOGLE_API_KEY",
	"openai": "OPENAI_API_KEY",
	"anthropic": "ANTHROPIC_API_KEY",
}


class ErroConfiguracao(ValueError):
	"""Representa uma configuração ausente ou inválida."""


@dataclass(frozen=True)
class ConfiguracaoCaminhos:
	"""Armazena os caminhos utilizados pela aplicação.

	Args:
		data: Diretório geral dos dados.
		organized: Diretório de datasets organizados.
		classified: Diretório de datasets classificados.
		results: Diretório dos resultados.
		taxonomy: Arquivo da taxonomia jurídica.
	"""

	data: Path
	organized: Path
	classified: Path
	results: Path
	taxonomy: Path


@dataclass(frozen=True)
class ConfiguracaoDatasets:
	"""Armazena os datasets disponíveis para processamento.

	Args:
		active_dataset: Nome do dataset ativo.
		available: Mapeamento entre identificadores e caminhos.
		organized_directory: Diretório dos datasets organizados.
	"""

	active_dataset: str
	available: Mapping[str, Path]
	organized_directory: Path

	@property
	def active_dataset_path(self) -> Path:
		"""Retorna o caminho absoluto do dataset ativo.

		Returns:
			Caminho absoluto do dataset ativo.
		"""
		return self.organized_directory / self.active_dataset


@dataclass(frozen=True)
class ConfiguracaoMetricas:
	"""Armazena os parâmetros das métricas da aplicação.

	Args:
		atp_alpha_weight: Peso utilizado no cálculo da ATP.
	"""

	atp_alpha_weight: float


@dataclass(frozen=True)
class ConfiguracaoAtrasos:
	"""Armazena os atrasos aplicados às requisições de LLM.

	Args:
		request_delay_seconds: Intervalo entre requisições, em segundos.
	"""

	request_delay_seconds: float


@dataclass(frozen=True)
class ConfiguracaoModelo:
	"""Descreve um modelo de linguagem disponível.

	Args:
		provider: Provedor responsável pelo modelo.
		model_name: Nome do modelo no provedor.
		api_key: Chave de autenticação do provedor, quando configurada.
	"""

	provider: str
	model_name: str
	api_key: str | None = field(default=None, repr=False)


@dataclass(frozen=True)
class ConfiguracaoLLM:
	"""Armazena a configuração dos provedores de LLM.

	Args:
		active_model: Identificador do modelo ativo.
		delays: Configuração dos atrasos entre requisições.
		models: Modelos disponíveis por identificador.
	"""

	active_model: str
	delays: ConfiguracaoAtrasos
	models: Mapping[str, ConfiguracaoModelo]

	@property
	def modelo_ativo(self) -> ConfiguracaoModelo:
		"""Retorna a configuração do modelo atualmente selecionado.

		Returns:
			Configuração do modelo ativo.

		Raises:
			ErroConfiguracao: Se o modelo ativo não estiver configurado.
		"""
		try:
			return self.models[self.active_model]
		except KeyError as erro:
			raise ErroConfiguracao(
				f"Modelo LLM ativo não configurado: {self.active_model}"
			) from erro


@dataclass(frozen=True)
class ConfiguracaoAplicacao:
	"""Representa a configuração completa da aplicação.

	Args:
		paths: Configuração dos caminhos do projeto.
		datasets: Configuração dos datasets.
		metrics: Configuração das métricas.
		llm: Configuração dos modelos de linguagem.
		logging: Configuração compatível com dictConfig.
	"""

	paths: ConfiguracaoCaminhos
	datasets: ConfiguracaoDatasets
	metrics: ConfiguracaoMetricas
	llm: ConfiguracaoLLM
	logging: Mapping[str, Any]


def _exigir_mapeamento(valor: Any, nome: str) -> Mapping[str, Any]:
	"""Valida e retorna um valor que deve ser um mapeamento.

	Args:
		valor: Valor a ser validado.
		nome: Nome do campo para a mensagem de erro.

	Returns:
		Mapeamento validado.

	Raises:
		ErroConfiguracao: Se o valor não for um mapeamento.
	"""
	if not isinstance(valor, Mapping):
		raise ErroConfiguracao(f"O campo '{nome}' deve ser um mapeamento.")
	return valor


def _exigir_texto(valor: Any, nome: str) -> str:
	"""Valida e retorna um valor textual não vazio.

	Args:
		valor: Valor a ser validado.
		nome: Nome do campo para a mensagem de erro.

	Returns:
		Texto validado.

	Raises:
		ErroConfiguracao: Se o valor não for um texto não vazio.
	"""
	if not isinstance(valor, str) or not valor.strip():
		raise ErroConfiguracao(f"O campo '{nome}' deve ser um texto não vazio.")
	return valor


def _exigir_numero(valor: Any, nome: str) -> float:
	"""Valida e retorna um valor numérico.

	Args:
		valor: Valor a ser validado.
		nome: Nome do campo para a mensagem de erro.

	Returns:
		Número validado.

	Raises:
		ErroConfiguracao: Se o valor não for numérico.
	"""
	if isinstance(valor, bool) or not isinstance(valor, (int, float)):
		raise ErroConfiguracao(f"O campo '{nome}' deve ser numérico.")
	return float(valor)


def _resolver_caminho(valor: Any, nome: str) -> Path:
	"""Converte um caminho configurado em um caminho absoluto.

	Args:
		valor: Caminho informado no YAML.
		nome: Nome do campo para a mensagem de erro.

	Returns:
		Caminho absoluto resolvido.
	"""
	caminho = Path(_exigir_texto(valor, nome))
	return caminho if caminho.is_absolute() else BASE_DIR / caminho


def _obter_chave_api(provedor: str) -> str | None:
	"""Obtém a chave de API do provedor a partir do ambiente.

	Args:
		provedor: Nome do provedor de LLM.

	Returns:
		Chave de API configurada ou None quando ausente.
	"""
	nome_variavel = CHAVES_API_POR_PROVEDOR.get(provedor)
	return getenv(nome_variavel) if nome_variavel else None


def _carregar_caminhos(dados: Mapping[str, Any]) -> ConfiguracaoCaminhos:
	"""Carrega e valida a seção de caminhos.

	Args:
		dados: Dados da seção `paths`.

	Returns:
		Configuração dos caminhos.
	"""
	return ConfiguracaoCaminhos(
		data=_resolver_caminho(dados.get("data"), "paths.data"),
		organized=_resolver_caminho(dados.get("organized"), "paths.organized"),
		classified=_resolver_caminho(
			dados.get("classified"),
			"paths.classified",
		),
		results=_resolver_caminho(dados.get("results"), "paths.results"),
		taxonomy=_resolver_caminho(dados.get("taxonomy"), "paths.taxonomy"),
	)


def _carregar_datasets(
	dados: Mapping[str, Any],
	caminhos: ConfiguracaoCaminhos,
) -> ConfiguracaoDatasets:
	"""Carrega e valida a seção de datasets.

	Args:
		dados: Dados da seção `datasets`.
		caminhos: Configuração dos caminhos do projeto.

	Returns:
		Configuração dos datasets.
	"""
	disponiveis = _exigir_mapeamento(
		dados.get("available"),
		"datasets.available",
	)

	return ConfiguracaoDatasets(
		active_dataset=_exigir_texto(
			dados.get("active_dataset"),
			"datasets.active_dataset",
		),
		available={
			_exigir_texto(chave, "datasets.available.<chave>"): (
				_resolver_caminho(valor, f"datasets.available.{chave}")
			)
			for chave, valor in disponiveis.items()
		},
		organized_directory=caminhos.organized,
	)


def _carregar_metricas(dados: Mapping[str, Any]) -> ConfiguracaoMetricas:
	"""Carrega e valida a seção de métricas.

	Args:
		dados: Dados da seção `metrics`.

	Returns:
		Configuração das métricas.

	Raises:
		ErroConfiguracao: Se o peso da ATP estiver fora do intervalo válido.
	"""
	peso = _exigir_numero(
		dados.get("atp_alpha_weight"),
		"metrics.atp_alpha_weight",
	)

	if not 0 <= peso <= 1:
		raise ErroConfiguracao(
			"metrics.atp_alpha_weight deve estar entre 0 e 1."
		)

	return ConfiguracaoMetricas(atp_alpha_weight=peso)


def _carregar_llm(dados: Mapping[str, Any]) -> ConfiguracaoLLM:
	"""Carrega e valida a seção de configuração dos modelos LLM.

	Args:
		dados: Dados da seção `llm`.

	Returns:
		Configuração dos modelos de linguagem.
	"""
	dados_atrasos = _exigir_mapeamento(dados.get("delays"), "llm.delays")
	dados_modelos = _exigir_mapeamento(dados.get("models"), "llm.models")

	modelos = {}
	for identificador, dados_modelo in dados_modelos.items():
		nome = f"llm.models.{identificador}"
		modelo = _exigir_mapeamento(dados_modelo, nome)
		provedor = _exigir_texto(
			modelo.get("provider"),
			f"{nome}.provider",
		)
		chave = _exigir_texto(identificador, nome)
		modelos[chave] = ConfiguracaoModelo(
			provider=provedor,
			model_name=_exigir_texto(
				modelo.get("model_name"),
				f"{nome}.model_name",
			),
			api_key=_obter_chave_api(provedor),
		)

	atraso = _exigir_numero(
		dados_atrasos.get("request_delay_seconds"),
		"llm.delays.request_delay_seconds",
	)

	if atraso < 0:
		raise ErroConfiguracao(
			"llm.delays.request_delay_seconds não pode ser negativo."
		)

	return ConfiguracaoLLM(
		active_model=_exigir_texto(
			dados.get("active_model"),
			"llm.active_model",
		),
		delays=ConfiguracaoAtrasos(request_delay_seconds=atraso),
		models=modelos,
	)


def _preparar_logging(dados: Mapping[str, Any]) -> Mapping[str, Any]:
	"""Prepara a configuração de logging para uso pela aplicação.

	Args:
		dados: Dados da seção `logging`.

	Returns:
		Cópia da configuração com caminhos de arquivo resolvidos.
	"""
	configuracao = deepcopy(dict(dados))
	handlers = configuracao.get("handlers", {})

	if isinstance(handlers, dict):
		handler_arquivo = handlers.get("file")
		if isinstance(handler_arquivo, dict):
			nome_arquivo = handler_arquivo.get("filename")
			if isinstance(nome_arquivo, str):
				handler_arquivo["filename"] = str(
					_resolver_caminho(nome_arquivo, "logging.handlers.file")
				)

	return configuracao


def carregar_configuracao(
	caminho: Path = CAMINHO_CONFIGURACAO,
) -> ConfiguracaoAplicacao:
	"""Carrega, valida e converte o arquivo YAML da aplicação.

	Args:
		caminho: Caminho do arquivo YAML de configuração.

	Returns:
		Configuração tipada e pronta para uso.

	Raises:
		FileNotFoundError: Se o arquivo de configuração não existir.
		ErroConfiguracao: Se o YAML ou algum campo for inválido.
	"""
	load_dotenv(BASE_DIR / ".env")

	with caminho.open("r", encoding="utf-8") as arquivo:
		dados = yaml.safe_load(arquivo)

	dados_raiz = _exigir_mapeamento(dados, "raiz")
	caminhos = _carregar_caminhos(
		_exigir_mapeamento(dados_raiz.get("paths"), "paths")
	)

	return ConfiguracaoAplicacao(
		paths=caminhos,
		datasets=_carregar_datasets(
			_exigir_mapeamento(dados_raiz.get("datasets"), "datasets"),
			caminhos,
		),
		metrics=_carregar_metricas(
			_exigir_mapeamento(dados_raiz.get("metrics"), "metrics")
		),
		llm=_carregar_llm(
			_exigir_mapeamento(dados_raiz.get("llm"), "llm")
		),
		logging=_preparar_logging(
			_exigir_mapeamento(dados_raiz.get("logging"), "logging")
		),
	)


CONFIG = carregar_configuracao()
