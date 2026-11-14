# Changelog — Antigravity Harness Enhancements

Todas as modificações estruturais, inclusão de hooks, otimizações e telemetrias deste repositório são registradas neste arquivo.

O formato é baseado no [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [3.5.0] - 2026-11-14

### Adicionado
- **Elo 3 — Reescrita Determinística `overwrite` (`HOOK-OPT-03`)**:
  - Introdução de `compute_deterministic_overwrite` em `hooks/context_mode_advisory_router.py` e integração ao `hooks_dispatcher.py` (`v0.9.3-p0.1`), retornando `decision="allow"` com objeto top-level `overwrite` (RTK ou delimitador seguro) sem spawn de subprocesso ou turno adicional.
  - Redução de `-51,5%` na latência média em benchmark `10/10 PASS` (`239,38 ms` $\to$ `116,14 ms`), preservando `11/11 PASS` na suíte unitária e `55/55 PASS` na validação adversarial `P0.1`.

### Corrigido
- **Blindagem Adversarial de 3 Bordas no `overwrite` do Elo 3**:
  - Proteção contra falsos positivos em pipes compostos, comandos destrutivos/mutantes e preservação estrita de delimitação na reescrita determinística de `context_mode_advisory_router.py`.

### Alterado
- **Unificação de `bootstrap-workstation.sh` (`main` + `dev-security-opt-01-p01`)**:
  - Incorporação do ajuste de `PATH`/NVM para subshells não-interativos, wrappers determinísticos em `~/.gemini/antigravity/bin/`, sincronização de `mcp_config.json`, `graphify install --platform antigravity` e atualização da assinatura para `Unified Guardrails Dispatcher v0.9.3-p0.1`.

## [3.4.0] - 2026-11-14

### Adicionado
- **Versionamento e Sincronização de Regras Globais `always_on` (`rules/` — `RULE-OPT-01`)**:
  - Inclusão de `rules/guardrails-safety.md` (enxugado de `3.465 B` para `1.876 B`, `-45,86%`, e atualizado de `guard_destructive.py` para `~/.gemini/config/hooks/hooks_dispatcher.py`) e `rules/macos-symlink-resolution.md` (`1.310 B`).
  - Integração automática no `bootstrap-workstation.sh` para copiar `rules/*.md` em `~/.gemini/config/rules/` preservando backups em `~/.gemini/config/.backups/rules/`.

### Alterado
- **Redução Sistêmica de Carga Fixa em `always_on` (`RUN-2026-11-14-RULE-OPT-01-ALWAYS-ON`)**:
  - Em conjunto com a compactação lossless do CEH (`AGENTS.md`: `24.905 B` $\to$ `12.092 B`, `coding-policy.md`: `1.642 B`, `core-engineering.md`: `990 B`), o conjunto global + plugin caiu de **`40.079 bytes` para `22.798 bytes` (`-43,12%`)** por turno, eliminando integralmente o truncamento de `978 bytes` em `AGENTS.md` e preservando `32/32` cláusulas normativas obrigatórias e `138/138` no `ceh-doctor.sh --verify`.
- Documentação base (`README.md`) atualizada para `v3.4` refletindo a gestão de `rules/` e os ganhos medidos de `RULE-OPT-01`.

## [3.3.0] - 2026-11-14

### Adicionado
- **Elo 1.5 integrado (`check_container_guard` e `_find_project_root`) em `hooks/hooks_dispatcher.py` (`v0.9.2-p0.1`)**: absorção da detecção Docker/Sail do legado `sail-container-guard` para dentro do pipeline monoprocesso (`decision: ask` com tag `[CONTAINER GUARD]` para `php artisan` no host, mantendo precedência estrita de `deny` do Elo 1 e zerando o spawn de processo Python adicional).
- **Telemetria Multi-Terminal Anonimizada em produção (`telemetry/runs/` e `scripts/sync_telemetry.sh`)**: homologação em campo durante 5 dias ativos (`N=863` eventos únicos deduplicados entre `fernando-casa` e `fernando-trabalho`, `0` falhas *fail-open* e redução da mediana em `fernando-trabalho` para `0,43 ms` após o fast-path `6a773c3`).

### Alterado
- **Refinamento do Confinamento de Caminhos (`validate_path_confinement`)**: suporte seguro a gravações multi-repositório sob `~/projects/` e artefatos/scratch oficiais sob `~/.gemini/antigravity/brain/`, preservando proteção estrita contra escrita em `~/.gemini/config/`, `.git/`, `.ceh/` e diretórios críticos do sistema (`/etc`, `/root`, `/usr`, etc.).
- **Alinhamento do Bootstrap (`bootstrap-workstation.sh`)**:
  - Instalação automática de `hooks/hooks_dispatcher.py` e `scripts/sync_telemetry.sh` além dos módulos de suporte (`context_mode_advisory_router.py`, `scoped_execution_guard.py`, `git_inspect.py`).
  - Geração do `~/.gemini/config/hooks.json` utilizando `"unified-guardrails-dispatcher"` com o `matcher` completo de 15 ferramentas (`run_command|ctx_execute|ctx_batch_execute|ctx_execute_file|ctx_purge|call_mcp_tool|read_file|view_file|grep_search|read_url_content|write_file|edit_file|write_to_file|replace_file_content|multi_replace_file_content`).
  - Desativação explícita (`"enabled": false`) das entradas globais legadas/redundantes `"sail-container-guard"`, `"destructive-command-guardrail"` e `"ceh-stop-guard"` (mantendo `ceh-stop-guard` e `ceh-safety-gate` ativos via manifesto do plugin `clearer-engineering`).
- **Documentação Base (`README.md`)**: atualizada para `v3.3` refletindo o Unified Guardrails Dispatcher, telemetria multi-terminal e novo fluxo do `bootstrap-workstation.sh`.
- **Homologação Comparativa Pós-Consolidação (`RUN-2026-11-14-HOOK-OPT-02-CONSOLIDATED`)**: suíte de 9 cenários $\times 50$ repetições em subprocessos reais (`100% PASS`) comprovando redução média de **`-31,4%`** nos fluxos deduplicados (`-24,4%` em `run_command` Git, `-21,3%` em Docker/Sail delimitado, **`-49,6%`** no evento `Stop`), **`-55,2%`** com correção de precedência no Elo 1.5 (`CB-03`: `deny` `167,10 ms` $\to$ `ask` `74,86 ms`) e eliminação dos falsos bloqueios em `~/projects/` e `brain/` mantendo proteção em `~/.gemini/config/hooks.json`.

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
