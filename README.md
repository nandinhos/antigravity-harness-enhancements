# 🚀 Antigravity Harness Enhancements (v3.0)
### *Eficiência de Tokens Zero-LLM & Tríade Determinística*

Repositório dedicado ao enriquecimento de contexto, eliminação de vazamento de logs, confinamento seguro de subprocessos e economia comprovada de tokens e latência no **Antigravity CLI (agy)** e **Antigravity IDE**.

---

## 🧱 Arquitetura em 4 Camadas

1. **Graphify (Knowledge Graph AST):** analisa o repositório deterministicamente via Tree-Sitter (AST) e gera `graph.json` + `GRAPH_REPORT.md` para navegação relacional precisa com **custo zero de LLM**. Consultas focadas (`query`/`path`/`explain`) substituem `grep` cego e leitura massiva de arquivos.
2. **Smart Advisory Router (`context_mode_advisory_router.py`):** desacopla recusa de segurança de orientações de performance, eliminando falsos bloqueios com `"decision": "deny"` em comandos autolimitados e rápidos ($\le 5\text{ KB}$).
3. **Scoped Execution Guard (`scoped_execution_guard.py`):** guardrail determinístico que intercepta varreduras abertas recursivas na raiz/home (`find /`, `find ~`) em $< 5\text{ ms}$, impõe timeout estrito de 30s por subprocesso e garante encerramento limpo em árvore via `os.killpg` (zero processos zumbis).
4. **Ferramental Declarativo Git (`git_inspect.py`):** utilitário parametrizado em JSON que responde em **40,2 ms**, cortando a geração procedural ad-hoc de scripts Python em sessões com Context-Mode.
5. **Compressão Determinística de Terminal (RTK):** suporte transparente no router para prefixo `rtk`, condensando logs de terminal com redução de **56,1% em bytes** e **75,6% em linhas**.

---

## 📊 Telemetria Comprovada (`OBSERVED`)

Bateria de medições empíricas instrumentadas e auditadas através dos benchmarks E2E-03 a E2E-06:

| Dimensão Avaliada | Baseline Tradicional | Com Harness Enhancements v3.0 | Ganho Líquido Comprovado |
|---|---|---|---|
| **Latência Média de Sessão (W1 - Saída Curta)** | 52,1s | **27,9s** | **-46,4% de latência** |
| **Tool Calls por Sessão (W1)** | 3 chamadas (com deny-and-retry) | **1 chamada direta** | **-66,7% de chamadas** |
| **Geração de Tokens de Saída (W2 - Histórico Git)** | ~5.190 tokens | **~2.850 tokens** | **-45,1% de geração de saída** |
| **Volume de Bytes no Terminal (Shell Output)** | 8.235 bytes | **3.619 bytes** | **-56,1% de bytes no contexto** |
| **Linhas Injetadas no Histórico do Shell** | 127 linhas | **31 linhas** | **-75,6% de poluição de contexto** |
| **Falsos Bloqueios em Comandos Seguros** | 100% dos comandos seguros | **0% (zero bloqueios)** | **100% de acurácia de roteamento** |
| **Interrupção de Varredura Perigosa (`find ~`)** | 180s (hang síncrono do harness) | **< 5 milissegundos** | **Proteção determinística imediata** |
| **Processos Zumbis Restantes pós-Timeout** | 1 a 3 processos órfãos | **0 processos (limpeza killpg)** | **Zero resíduo de subprocessos** |

---

## 🚀 Instalação e Sincronização da Estação (1 Clique)

```bash
git clone https://github.com/nandinhos/antigravity-harness-enhancements.git ~/projects/antigravity-harness-enhancements
cd ~/projects/antigravity-harness-enhancements
bash bootstrap-workstation.sh
```

O script automaticamente:
1. Instala e atualiza `graphify` e `context-mode`.
2. Sincroniza a suíte canônica de skills em `~/.gemini/config/skills/`.
3. Registra o agente `gemini-orchestrator`.
4. Instala os hooks `context_mode_advisory_router.py` e `scoped_execution_guard.py` em `~/.gemini/config/hooks/`.
5. Instala o utilitário `git_inspect.py` em `~/.gemini/config/scripts/`.
6. Configura `~/.gemini/config/hooks.json` com a ordem canônica rigorosa:
   - Prioridade 1: `ceh-safety-gate` (segurança contra comandos destrutivos).
   - Prioridade 2: `scoped-execution-guard` (confinamento de escopo e limites de processo).
   - Prioridade 3: `context-mode-guard` (Smart Advisory Router).
7. Verifica a presença do `rtk` no PATH para compressão de shell.

---

## 🛠️ Como Utilizar no Dia a Dia

### 1. Inspeção de Histórico Git Otimizada
Em vez de ler diffs brutos gigantescos ou gerar scripts ad-hoc no terminal:
```bash
python3 ~/.gemini/config/scripts/git_inspect.py log --max-count 15 --stat
python3 ~/.gemini/config/scripts/git_inspect.py diff --target HEAD~1
python3 ~/.gemini/config/scripts/git_inspect.py status
```

### 2. Compressão Transparente de Comandos com RTK
```bash
rtk git status
rtk git log -n 15
rtk cargo test
rtk pytest
```
O Smart Advisory Router reconhece o prefixo `rtk` de forma transparente, mantendo a permissão direta sem falsos bloqueios.

### 3. Navegação por AST com Graphify
```bash
graphify extract . --code-only   # bootstrap do grafo
graphify query "quais os pontos de entrada do projeto?"
graphify update .                # atualização incremental rápida
```
