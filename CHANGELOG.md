# Changelog — Antigravity Harness Enhancements

Todas as modificações estruturais, inclusão de hooks, otimizações e telemetrias deste repositório são registradas neste arquivo.

O formato é baseado no [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

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
