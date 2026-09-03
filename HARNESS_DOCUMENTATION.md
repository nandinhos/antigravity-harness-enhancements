# 🛡️ Guia Oficial do Harness de Otimização: Antigravity
### **Graphify (Navegação Relacional AST) + context-mode (Higiene de Contexto)**

---

## 📐 1. Visão Geral e Arquitetura

O **Harness Antigravity Enhancements** é um sistema de otimização de contexto e economia de tokens projetado para o **Antigravity (agy)** no ambiente WSL. Ele combina duas ferramentas complementares:

1. **Graphify (`graphifyy`)**: analisa o código-fonte com parsers AST determinísticos via **Tree-Sitter**. Em vez de buscas cegas por arquivo ou múltiplos `grep`/`find` custosos, a IA consulta um grafo relacional (`graph.json`) com **custo zero de tokens de LLM**.
2. **context-mode**: servidor MCP que mantém dado cru de tool fora da janela de contexto (sandbox), garante continuidade de sessão (SQLite+FTS5) e promove "think in code".

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
       └────────────────────────┘       │ - think in code        │
                                        └────────────────────────┘
```

> **Headroom removido.** O proxy CCR do Headroom só atende clientes Anthropic/OpenAI (não há rota Gemini) e foi descontinuado nesta metodologia.

---

## ⚡ 2. Pré-requisitos do Ambiente WSL

* **Python**: `3.10` ou superior (recomendado: 3.12+)
* **Git**: `2.40` ou superior
* **uv** (gerenciador rápido de ferramentas Python):
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
* **Node.js 18+** (para o `context-mode`)

---

## 📦 3. Instalação Global no WSL

```bash
# Instala o Graphify (fornece 'graphify' e 'graphify-mcp')
uv tool install graphifyy
```

O **context-mode** é instalado via npm e integrado ao Gemini CLI num único arquivo (`~/.gemini/settings.json`) — MCP + hooks. Consulte o repositório oficial `mksglu/context-mode` para o snippet de configuração.

### Verificar Versões
```bash
graphify --version
context-mode --version
```

---

## 🚀 4. Guia de Ativação por Projeto

### **Passo 1: Gerar a análise AST inicial do projeto**
```bash
graphify extract . --code-only
graphify cluster-only .
```
* Mapeia o código via Tree-Sitter local, cria comunidades e gera `graphify-out/GRAPH_REPORT.md` + `graphify-out/graph.html`.

### **Passo 2: Instalar Regras e Workflows no Antigravity**
```bash
graphify antigravity install
```
* Cria `.agents/rules/graphify.md` e `.agents/workflows/graphify.md`, instruindo o assistente a usar o grafo.

### **Passo 3: Ativar Atualização Automática via Git Hook**
```bash
graphify hook install
```
* Hook `post-commit`/`post-checkout` atualiza o grafo incrementalmente.

### **Passo 4: (Opcional) Registrar o `.mcp.json` Local**
```json
{
  "mcpServers": {
    "graphify": {
      "command": "graphify-mcp",
      "args": ["${workspace.path}/graphify-out/graph.json"]
    }
  }
}
```

---

## 🔄 5. Funcionamento e Workflow no Dia a Dia

### 1. **Perguntas sobre o Código e Arquitetura**
* A IA lê `.agents/rules/graphify.md` e consulta o `graph.json` via `graphify query`/`path`/`explain`.
* **Economia:** nenhuma leitura cega de arquivos brutos.

### 2. **Higiene de Contexto**
* O `context-mode` mantém dado cru de tool fora do contexto e preserva o estado entre compactações.
* **Economia:** contexto enxuto + retomada consistente após compactação.

### 3. **Manutenção e Atualização do Código**
* Com commit: o git hook atualiza o grafo. Sem commit: `graphify update .` (incremental, <2s).

---

## 📊 6. Comandos Úteis

```bash
# Consultas ao grafo
graphify query "Onde estão os controllers?"
graphify path "UserController" "AuthRepository"
graphify explain "PaymentGateway"
graphify god-nodes --top 10

# Higiene de contexto (dentro de uma sessão agy)
ctx stats
```

---

## ✅ Resumo do Workflow

| Componente | Função | Instalação no Projeto | Execução no Dia a Dia |
| :--- | :--- | :--- | :--- |
| **Graphify** | Navegação Relacional AST | `graphify extract . --code-only`<br>`graphify antigravity install`<br>`graphify hook install` | Invisível: a IA consulta `graph.json` via regra `.agents/`. |
| **context-mode** | Higiene de contexto + continuidade | global (`~/.gemini/settings.json`) | Transparente: sandbox de tool output + "think in code". |

---

*Documentação gerada para o Antigravity (agy) no WSL.*
