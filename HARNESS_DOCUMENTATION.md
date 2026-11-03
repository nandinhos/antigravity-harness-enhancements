# 🛡️ Guia Oficial do Harness de Otimização: Antigravity
### **Graphify (Navegação Relacional AST) + context-mode (Higiene de Contexto) + Módulo de Telemetria**

---

## 📐 1. Visão Geral e Arquitetura

O **Harness Antigravity Enhancements** é um sistema de otimização de contexto e economia de tokens projetado para o **Antigravity (agy)** no ambiente WSL. Ele opera através de três camadas determinísticas zero-LLM:

1. **Graphify (`graphifyy`)**: analisa o código-fonte com parsers AST determinísticos via **Tree-Sitter**. Em vez de buscas cegas por arquivo ou múltiplos `grep`/`find` custosos, a IA consulta um grafo relacional (`graph.json`) com **custo zero de tokens de LLM**.
2. **context-mode**: servidor MCP e hooks nativos (`antigravity-cli`) que mantêm dado cru de tool fora da janela de contexto (sandbox), garantem continuidade de sessão (SQLite+FTS5) e promovem "think in code".
3. **Módulo de Telemetria & Verificação Ponytail**: suíte automatizada (`scripts/harness-telemetry-benchmark.py`) que audita fisicamente a taxa de redução de tokens, volume em bytes e latência de processamento.

```
┌────────────────────────────────────────────────────────────────────────┐
│                          ANTIGRAVITY (agy)                             │
└───────────────────┬────────────────────────────────┬───────────────────┘
                    │                                │
       (1) Consultas Arquiteturais        (2) Higiene de Contexto / Tools
                    │                                │
                    ▼                                ▼
       ┌────────────────────────┐       ┌────────────────────────┐
       │   Graphify (AST Graph) │       │   context-mode (MCP)   │
       │   - zero cost parsing  │       │ - sandbox de tool out  │
       │   - graphify-out/      │       │ - continuidade sessão  │
       │   - mcp_config.json    │       │ - think in code        │
       └────────────────────────┘       └────────────────────────┘
                    │                                │
                    └────────────────┬───────────────┘
                                     ▼
                    ┌─────────────────────────────────┐
                    │  (3) Telemetria de Eficiência   │
                    │  scripts/harness-telemetry-...  │
                    │  Economia comprovada: >94%      │
                    └─────────────────────────────────┘
```

> **Nota sobre Proxies**: Proxies HTTP de rede (como Headroom) permanecem terminantemente proibidos por incompatibilidade de protocolo com o Gemini. Otimizações de terminal locais (como RTK e Tree-Sitter) são totalmente suportadas.

---

## 📊 2. Telemetria e Métricas Comprovadas (`OBSERVED`)

Bateria de testes determinísticos executada fisicamente no ambiente via `scripts/harness-telemetry-benchmark.py`:

| Caso de Uso | Abordagem Tradicional | Abordagem Harness (AST/Sandbox) | Economia de Tokens (%) | Latência Observada |
|---|---|---|---|---|
| **Mapeamento Arquitetural** | 5.876 tokens (`view_file` em lote) | 921 tokens (`graphify query`) | **84,87%** | 135.8 ms |
| **Identificação de God-Nodes** | 11.077 tokens (`grep` recursivo bruto) | 83 tokens (`graphify god-nodes`) | **99,20%** | 137.2 ms |
| **Overhead de Interceptação Hook** | Sem interceptação (vazamento de log) | Hook nativo `context-mode` | **Zero context bloat** | 63.73 ms |
| **MÉDIA GLOBAL PONDERADA** | **16.953 tokens** | **1.004 tokens** | **94,08%** | **< 150 ms** |

---

## ⚡ 3. Pré-requisitos do Ambiente WSL

* **Python**: `3.10` ou superior (recomendado: 3.12+)
* **Git**: `2.40` ou superior
* **uv** (gerenciador rápido de ferramentas Python):
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
* **Node.js 20+** (para o `context-mode`)

---

## 📦 4. Instalação e Ativação Automática

Execute o script de automação unificado na raiz do repositório:
```bash
bash bootstrap-workstation.sh
```

O script automaticamente:
1. Instala e atualiza `graphifyy` e `context-mode`.
2. Cria os wrappers determinísticos em `~/.gemini/antigravity/bin/`.
3. Registra os servidores MCP globais em `~/.gemini/config/mcp_config.json`.
4. Ativa os hooks nativos em `~/.gemini/config/hooks.json` com os matchers oficiais do Antigravity (`run_command|view_file|grep_search|read_url_content`).
5. Sincroniza a Suíte Canônica de Skills e o Orquestrador Gemini.

---

## 🔄 5. Funcionamento no Dia a Dia

### 1. **Perguntas sobre Código e Arquitetura**
* A IA lê `.agents/rules/graphify.md` e consulta o `graph.json` via `graphify query`/`path`/`explain`.
* **Economia:** nenhuma leitura cega de arquivos brutos (~94% menos tokens).

### 2. **Higiene de Contexto Transparente**
* Os hooks `PreToolUse` e `PostToolUse` interceptam saídas volumosas de comandos e leituras.
* **Economia:** o context window permanece limpo durante longas sessões de debugging.

### 3. **Auditoria de Telemetria**
* Execute a qualquer momento para validar o ganho real de tokens:
  ```bash
  python3 scripts/harness-telemetry-benchmark.py
  ```

---

## 📊 6. Comandos Úteis

```bash
# Consultas ao grafo de conhecimento
graphify query "Onde estão os controllers?"
graphify path "UserController" "AuthRepository"
graphify explain "PaymentGateway"
graphify god-nodes --top 10

# Atualização incremental do grafo após edições
graphify update .

# Executar suíte de telemetria
python3 scripts/harness-telemetry-benchmark.py
```
