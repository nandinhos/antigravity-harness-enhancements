# 🤝 HANDOFF DOCUMENT: Antigravity Harness Enhancements (v2.0)
## Para Agentes, Automação de Workstations e Preset Antigravity CLI

> **Status: EXECUTADO & TESTADO (v2.0).** Este handoff documenta a arquitetura de produção do harness, com suporte nativo aos hooks do Antigravity CLI (`hooks.json`), registro unificado de MCPs (`mcp_config.json`), wrappers determinísticos no PATH e suíte física de telemetria com **94,93% de economia de tokens comprovada**.

---

## 📌 1. Visão Geral da Arquitetura v2.0

O harness opera através da **Tríade de Eficiência Zero-LLM**:

| Camada | Tecnologia | Implementação Físico-Operacional | Função & Ganho |
|---|---|---|---|
| **1. Conhecimento AST** | Graphify (`graphifyy`) | `~/.gemini/antigravity/bin/graphify` & `graphify-mcp` | Mapeamento relacional via Tree-Sitter (custo zero de LLM, 87% a 99% menos tokens que leituras brutas). |
| **2. Higiene de Contexto** | context-mode | `~/.gemini/config/hooks.json` & `~/.gemini/config/mcp_config.json` | Interceptação nativa Antigravity (`run_command|view_file|grep_search|read_url_content`), sandbox e SQLite FTS5. |
| **3. Telemetria & Testes** | Telemetry Suite | `scripts/harness-telemetry-benchmark.py` | Auditoria física contínua de latência (<60ms por hook) e redução determinística de tokens. |

```
┌────────────────────────────────────────────────────────────────────────┐
│                          ANTIGRAVITY CLI (agy)                         │
└───────────────────┬────────────────────────────────┬───────────────────┘
                    │                                │
       (1) Consultas AST (Zero-Token)    (2) Interceptação Nativa (Hooks)
                    │                                │
                    ▼                                ▼
       ┌────────────────────────┐       ┌────────────────────────┐
       │   Graphify (AST Graph) │       │   context-mode (MCP)   │
       │   - mcp_config.json    │       │ - hooks.json           │
       │   - graphify-mcp       │       │ - sandbox de tool out  │
       │   - graphify update .  │       │ - sessão SQLite FTS5   │
       └────────────────────────┘       └────────────────────────┘
                    │                                │
                    └────────────────┬───────────────┘
                                     ▼
                    ┌─────────────────────────────────┐
                    │  (3) Telemetria Comprovada      │
                    │  scripts/harness-telemetry-...  │
                    │  Economia: 94,93% | Latência OK │
                    └─────────────────────────────────┘
```

---

## 📊 2. Telemetria Oficial Medida (`OBSERVED`)

Bateria física de testes auditada pelo benchmark do projeto:

* **Mapeamento Arquitetural**: de 6.958 tokens (`view_file` em lote) para **921 tokens** (`graphify query`) — **87,21% de redução** (138ms).
* **Varredura de Símbolos / God-Nodes**: de 12.843 tokens (`grep` recursivo) para **83 tokens** (`graphify god-nodes`) — **99,31% de redução** (110ms).
* **Overhead de Interceptação de Hook**: **55,52 ms** de latência média (Exit Code 0, sem travamento de stdio).
* **Resultado Global Ponderado**: **19.801 tokens → 1.004 tokens (94,93% de economia real)**.

---

## 🛠️ 3. Guia de Instalação e Ativação Canônica

### Método 1: Automático (Recomendado para novas máquinas)
Na máquina de trabalho (Linux/WSL2):
```bash
git clone https://github.com/nandinhos/antigravity-harness-enhancements.git ~/projects/antigravity-harness-enhancements
cd ~/projects/antigravity-harness-enhancements
bash bootstrap-workstation.sh
```

### Método 2: O que o bootstrap provisiona (Checklist de Integridade)
1. **Wrappers Determinísticos em `~/.gemini/antigravity/bin/`**:
   - `context-mode`: wrapper que invoca `node --no-warnings <cli.bundle.mjs>`.
   - `graphify` e `graphify-mcp`: wrappers com PATH isolado.
2. **Servidores MCP Globais em `~/.gemini/config/mcp_config.json`**:
   ```json
   {
     "mcpServers": {
       "context-mode": {
         "command": "/home/nandodev/.gemini/antigravity/bin/context-mode"
       },
       "graphify": {
         "command": "/home/nandodev/.gemini/antigravity/bin/graphify-mcp"
       }
     }
   }
   ```
3. **Hooks Nativos do Antigravity em `~/.gemini/config/hooks.json`**:
   ```json
   "context-mode-guard": {
     "enabled": true,
     "PreToolUse": [
       {
         "matcher": "run_command|view_file|grep_search|read_url_content",
         "hooks": [{ "type": "command", "command": "context-mode hook antigravity-cli pretooluse", "timeout": 10 }]
       }
     ],
     "PostToolUse": [
       {
         "matcher": "run_command|view_file|grep_search|read_url_content",
         "hooks": [{ "type": "command", "command": "context-mode hook antigravity-cli posttooluse", "timeout": 10 }]
       }
     ]
   }
   ```

---

## 🔄 4. Workflow de Desenvolvimento e Regras do Dia a Dia

1. **AST First**: Sempre consulte `graphify query/path/explain` antes de ler arquivos inteiros ou disparar grep cego.
2. **Higiene Transparente**: O `context-mode` atua via hooks no Antigravity CLI e via MCP tools (`execute`, `batch_execute`) na IDE.
3. **Atualização do Grafo**: Execute `graphify update .` imediatamente após alterar arquivos de código para prevenir *graph drift*.
4. **Auditoria de Telemetria**: Rode `python3 scripts/harness-telemetry-benchmark.py` para revalidar métricas após upgrades.
5. **Ponytail Mode**: Entender muito, construir pouco e entregar certo. Respeitar o blast radius mínimo e testes determinísticos.

---

## 🔗 Referências e Arquivos-Chave

* Script de Telemetria: [`scripts/harness-telemetry-benchmark.py`](file:///home/nandodev/projects/antigravity-harness-enhancements/scripts/harness-telemetry-benchmark.py)
* Relatório JSON de Telemetria: [`telemetry_benchmark_report.json`](file:///home/nandodev/projects/antigravity-harness-enhancements/telemetry_benchmark_report.json)
* Script de Bootstrap: [`bootstrap-workstation.sh`](file:///home/nandodev/projects/antigravity-harness-enhancements/bootstrap-workstation.sh)
* Guia da Máquina de Trabalho: [`SETUP_WORK_MACHINE.md`](file:///home/nandodev/projects/antigravity-harness-enhancements/SETUP_WORK_MACHINE.md)
