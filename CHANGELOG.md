# Changelog — Antigravity Harness Enhancements

Todas as modificações estruturais, inclusão de hooks, otimizações e telemetrias deste repositório são registradas neste arquivo.

O formato é baseado no [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [3.2.0] - 2026-11-08

### Adicionado
- **Hardening Corretivo P0.1 & Inspeção Estruturada AST (SECURITY-OPT-01-P01)**:
  - **Eliminação da Suposição Implícita de Linguagem**: remoção de `language or "shell"` em favor de classificação explícita de 4 estados (`SHELL`, `PYTHON`, `JAVASCRIPT`, `UNKNOWN`).
  - **Inspeção Estruturada via AST de Python (`ast.parse`)**: varredura da árvore sintática para chamadas a `os.system`, `subprocess.*`, `shutil.rmtree` e escritas via `open()` em diretórios protegidos.
  - **Política Fail-Closed para Código `UNINSPECTABLE`**: bloqueio conservador para metaprogramação opaca (`eval`, `exec`) ou linguagens não determinadas na ausência de sandbox de runtime.
  - **Fronteiras Léxicas Expandidas**: suporte a delimitadores de string literal (`['\";\)\]\}\s]`) para captura de comandos destrutivos embutidos.
  - **Resolução da Fixture OP-06**: eliminação de falsos negativos em chamadas MCP sem atributo `language`.

## [3.1.0] - 2026-11-08

### Adicionado
- **Fase P0 de Segurança (SECURITY-OPT-01-P0) & Unified Dispatcher**:
  - Implementação do `Normalizador Universal de Payloads` no `hooks/hooks_dispatcher.py`: desembrulho iterativo de `call_mcp_tool` (profundidade $\le 3$), normalização tipada de comandos (`CommandLine`, `code`, `commands[]`) e caminhos de arquivos (`Path`, `TargetFile`).
  - **Política Fail-Closed Estrita em Exit Code 0**: tratamento determinístico de JSON vazio, strings whitespace, truncamento e tipos inválidos com bloqueio imediato (`decision: deny`) garantindo conformidade com o runtime da IDE Antigravity (prevenindo fail-open em exit != 0).
  - **Catálogo de Compatibilidade de 42 Ferramentas Homologadas**: suporte a Antigravity nativo, MCPs `context-mode`, `dev-memory`, `dak-notebook` e `gemini-api-docs`.
  - **Confinamento de Escopo e Proteção de Workspace**: bloqueio determinístico a tentativas de mutação fora do workspace e em diretórios sensíveis (`.ceh/`, `.git/`).
  - Tradução automática de contratos de ferramentas de escrita (`write_file`/`edit_file` -> `write_to_file` com `TargetFile`).

## [3.0.0] - 2026-11-08

### Adicionado
- **Tríade Determinística & Eficiência de Tokens**:
  - `Smart Advisory Router` (`hooks/context_mode_advisory_router.py`): desacoplamento de deny em comandos delimitados ($\le 5\text{ KB}$), reduzindo em **46,4% a latência de harness** e eliminando 100% dos falsos bloqueios.
  - `Scoped Execution Guard` (`hooks/scoped_execution_guard.py`): confinamento de escopo com bloqueio em **< 5 ms** de varreduras perigosas na raiz/home (`find /`, `find ~`), timeout de 30s por subprocesso e encerramento em árvore via `os.killpg` com zero processos zumbis.
  - `Ferramental Declarativo Git` (`scripts/git_inspect.py`): inspeção estruturada em JSON executando em **40,2 ms** e reduzindo em até **45,1% os tokens de saída** da LLM.
  - Suporte nativo à compressão de terminal via `rtk`, cortando **56,1% em bytes** e **75,6% em linhas**.
- **Automação do Bootstrap**:
  - Atualização do `bootstrap-workstation.sh` com instalação automatizada e ordenação canônica de hooks em `~/.gemini/config/hooks.json`.
- **Telemetria Homologada**:
  - Inclusão do relatório auditado `telemetry_benchmark_report.json` e documentação completa no `README.md`.

## [2.0.0] - 2026-09-03

### Adicionado
- Integração de `Graphify AST` para navegação relacional com custo zero de LLM.
- Suporte a `context-mode` e automação de bootstrap da workstation.

## [1.0.0] - 2026-07-30

### Adicionado
- Lançamento inicial do harness de aprimoramentos para Google Antigravity.
