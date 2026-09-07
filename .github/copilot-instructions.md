## 1. CONTEXTO DO PROJETO
* **Título/Domínio:** Projeto de TCC (UFRRJ) para tipificação penal e classificação jurídica automatizada sob o Direito Penal brasileiro utilizando LLMs.
* **Linguagem e Ecossistema:** Python 3.11+, focado em código limpo, tipagem estática e alta testabilidade.
* **Objetivo do Código:** Processar narrativas fáticas reais, submetê-las a modelos de linguagem, realizar o parsing das respostas estruturadas e avaliar a acurácia do modelo por meio de métricas customizadas como a Acurácia Taxonômica Ponderada (ATP).

---

## 2. PAPEL DA IA, VISUALIZAÇÃO PREVIA E AUTORIZAÇÃO DE ALTERAÇÕES
* **Controle Humano Absoluto:** O desenvolvedor humano é o arquiteto do sistema. A IA atua estritamente como executora.
* **Exibição Prévia Obrigatória:** Antes de editar, criar ou sobrescrever qualquer arquivo no projeto, a IA DEVE exibir no chat o código completo e formatado que pretende gerar, acompanhado de uma explicação clara do que foi feito.
* **Solicitação de Permissão:** Após exibir o código no chat, a IA DEVE perguntar explicitamente ao desenvolvedor se pode proceder com a escrita/alteração do arquivo. Nenhuma alteração no sistema de arquivos deve ocorrer sem o "sim" do usuário.
* **Sem Decisões Autônomas de Infraestrutura:** Não adicione novas dependências (`pip`), novos frameworks ou crie novas camadas de abstração sem solicitação explícita.

---

## 3. FLUXO DE TRABALHO ATÔMICO E COMMITS (GIT WORKFLOW)
O desenvolvimento deve ocorrer de forma estritamente granular e passo a passo (uma função, arquivo ou teste por vez).

* **Passo a Passo Granular:** Não escreva múltiplos arquivos ou grandes blocos de funções de uma só vez. Foque em concluir uma única função ou teste por interação.
* **Commits Obrigatórios em Inglês:** Para CADA arquivo criado, função implementada ou teste concluído, a IA DEVE sugerir o comando exato de commit em inglês utilizando o padrão *Conventional Commits*:
  * `feat(scope): add description of the new function or feature`
  * `test(scope): add unit test for specific function`
  * `refactor(scope): refactor specific logic`
  * `docs(scope): update documentation or docstrings`
* **Estrutura de Resposta para Commits:** Ao finalizar a alteração autorizada, forneça o comando pronto para execução no terminal:
  ```bash
  git add <arquivo_alterado>
  git commit -m "feat(module): explicit commit message in english"```

---

## 4. ARQUITETURA E PADRÕES DE PROJETO

* **Isolamento Modular:** O módulo de conexão com LLMs deve ser completamente desacoplado da lógica de pipeline de condutas, da camada de persistência e do módulo de avaliação de métricas.
* **Padrão Strategy / Factory:**
* O acesso aos provedores de LLM (Google Gemini, OpenAI, Anthropic) deve utilizar o padrão **Factory** para instanciação de clientes e **Strategy** para a execução das chamadas.
* O código do pipeline nunca deve instanciar chamadas de SDK diretamente; ele interage apenas com interfaces/classes abstratas de provedores.


* **Imutabilidade e Tipagem:** Utilize `dataclasses` ou `Pydantic` para transferência de dados entre módulos (DTOs) com tipagem estática rigorosa (`typing`).

---

## 5. CONVENÇÕES DE CÓDIGO E NOMENCLATURA

* **Estilo de Código:** Siga estritamente o PEP 8.
* **Nomenclatura:**
* **Funções e Variáveis:** `snake_case` em português explícito e descritivo para termos do domínio jurídico (ex: `crime_real`, `crime_predito`, `calcular_acuracia_taxonomica`).
* **Classes e Interfaces:** `PascalCase` (ex: `GeminiProvider`, `EvaluatorPipeline`).
* **Constantes:** `UPPER_SNAKE_CASE` (ex: `DEFAULT_ALPHA_WEIGHT = 0.5`).


* **Funções Pequenas e Focadas:** Cada função deve ter uma única responsabilidade (Princípio da Responsabilidade Única - SRP).
* **Documentação Obrigatória (Docstrings):**
* Toda função, classe e método DEVE obrigatoriamente possuir docstring em português no formato Google Style.
* Descreva explicitamente: propósito, `Args:`, `Returns:` e `Raises:` (se houver).


---

## 6. REGRAS DO MÓDULO DE LLM E PARSING

* **Configuração Externa:** Parâmetros de modelo, tempos de espera (*delays*) e credenciais devem ser lidos estritamente do arquivo de configuração (`config.yaml`) ou variáveis de ambiente.
* **Determinismo:** Configurações de inferência devem forçar determinismo (ex: `temperature: 0.0`).
* **Tratamento de Saída (Parsing Robust):** A resposta em texto bruto da LLM deve passar por uma camada de sanitização e parsing defensivo. Trate exceções de JSON malformado e retorne estruturas de erro tratadas (*fallbacks*).

---

## 7. ESTRATÉGIA DE TESTES (PYTEST)

* **O que NÃO testar:**
* Não crie testes para chamadas diretas de SDKs/APIs externas ou funções triviais de atribuição.


* **O que TESTAR obrigatoriamente:**
* Regras de negócio complexas (ex: cálculo da métrica ATP, agrupamento taxonômico).
* Lógica de parsing de texto/JSON retornado pelas LLMs.
* Funções de validação e sanitização de entradas.


* **Padrão AAA (Arrange, Act, Assert):**
* Todo teste unitário deve ter suas três fases claramente identificáveis.


* **Cobertura de Cenários:**
* **Caminho Feliz (*Happy Path*):** Entradas válidas produzindo a saída esperada.
* **Casos de Borda (*Edge Cases*):** Trate e teste strings vazias, valores `None`, respostas inesperadas da LLM e limites numéricos.


* **Nome de Testes:** Utilize nomes explicativos em português (ex: `test_deve_retornar_pontuacao_parcial_quando_crimes_pertencem_ao_mesmo_grupo()`).

---

## 8. ESTRUTURA DE ARQUIVOS E IMPORTAÇÕES (SRC-LAYOUT)
* **Localização de Código:** Todo o código de produção deve residir estritamente dentro da pasta `src/`.
* **Importações Absolutas:** Utilize sempre importações absolutas a partir da raiz `src` (ex: `from src.config import CONFIG`, `from src.llm.factory import LLMFactory`).
* **Barreiras de Mapeamento (Fronteiras de Módulo):**
  * O módulo `src/metrics/` NUNCA deve importar nada do módulo `src/llm/` ou `src/pipeline/`.
  * O módulo `src/llm/` NUNCA deve processar dados do Vade Mecum ou aplicar lógica de ATP.
* **Manipulação de Caminhos:** Nunca utilize strings simples para caminhos de arquivos. Utilize obrigatoriamente a biblioteca `pathlib.Path` referenciando `BASE_DIR` de `src.config`.
* **Criação de Testes:** Todo novo arquivo criado em `src/modulo/arquivo.py` deve ter seu correspondente de teste criado em `tests/unit/test_arquivo.py`.