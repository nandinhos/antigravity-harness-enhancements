# 🚀 Antigravity Harness Enhancements: Graphify + context-mode

Repositório dedicado ao enriquecimento de contexto e economia de tokens no **Antigravity (agy)**.

## 🧱 Arquitetura

* **Graphify (Knowledge Graph AST):** analisa o repositório deterministicamente via Tree-Sitter (AST) e gera `graph.json` + `GRAPH_REPORT.md` para navegação relacional precisa com **custo zero de LLM**. Consultas focadas (`query`/`path`/`explain`) substituem `grep` cego e leitura massiva de arquivos.
* **context-mode (higiene de contexto):** servidor MCP que mantém dado cru de tool fora da janela de contexto, garante continuidade de sessão (SQLite+FTS5) e promove "think in code". Já integrado ao Gemini CLI via `~/.gemini/settings.json` (MCP + hooks).

> **Headroom foi removido.** O proxy CCR do Headroom só atende clientes Anthropic/OpenAI — não há rota para Gemini/Antigravity — e não se encaixou na metodologia de desenvolvimento. A higiene de contexto ficou com o `context-mode`.

## 📋 Etapas de Implementação

- [x] **Etapa 1:** Instalação do Graphify (`uv tool install graphifyy`)
- [x] **Etapa 2:** Configuração da Skill Graphify (`.agents/skills/graphify`)
- [x] **Etapa 3:** Integração do `context-mode` (MCP + hooks no Gemini)
- [x] **Etapa 4:** Bootstrap do grafo e validação (`graphify extract` + `query`)

## 🛠️ Configuração

### 1. Servidor MCP (`.mcp.json`)
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

### 2. Regras e Workflows (`.agents/`)
* `.agents/rules/graphify.md` — instrui a IA a consultar o grafo antes de buscas exaustivas.
* `.agents/workflows/graphify.md` — workflow `/graphify` de geração/atualização.
* `.agents/skills/graphify/SKILL.md` — definição completa da skill de navegação AST.

## 📊 Métricas de Economia

### Graphify AST Knowledge Graph
* Extração determinística Tree-Sitter (zero LLM).
* Navegação focada via `graphify query` / `path` / `explain` / `affected` / `god-nodes`.

### context-mode
* Sandbox de tool output (reduz dado cru em ~98%).
* Continuidade de sessão + "think in code".

## 🚀 Como Usar

### Graphify
```bash
graphify extract . --code-only   # bootstrap do grafo (AST, sem API key)
graphify query "estrutura do projeto?"
graphify update .                # incremental (<2s) após editar código
```

### context-mode
Já ativo via `~/.gemini/settings.json`. Validar com `ctx stats` numa sessão do `agy`.
