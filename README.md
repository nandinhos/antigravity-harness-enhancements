# 🚀 Antigravity Harness Enhancements: Graphify + Headroom

Repositório dedicado ao enriquecimento de contexto e economia de tokens no **Antigravity IDE (WSL)**.

## 🧱 Arquitetura Combinada

* **Graphify (AST Navigation Skill):** Analisa a estrutura do repositório deterministicamente via Tree-Sitter (AST) e gera `graph.json` e `GRAPH_REPORT.md` para navegação relacional precisa sem requisições cegas de `grep` ou buscas exaustivas.
* **Headroom (CCR Context Compression):** Atua como proxy e servidor MCP intermediário comprimindo saídas de terminal e logs pesados (até 90% de redução) via algoritmo reversível de Compress-Cache-Retrieve (CCR).

---

## 📋 Etapas de Implementação

- [x] **Etapa 1:** Instalação CLI (`uv tool install graphifyy` & `pip install headroom-ai[all]`)
- [x] **Etapa 2:** Configuração da Skill Graphify (`~/.gemini/config/skills/graphify` e `.agents/skills/graphify`)
- [x] **Etapa 3:** Registro do Servidor MCP / Proxy Headroom (`.mcp.json` e `headroom mcp install`)
- [x] **Etapa 4:** Teste comparativo de benchmarks e documentação no repositório

---

## 🛠️ Configuração e Componentes Integrados

### 1. Servidores MCP (`.mcp.json`)
Configuração presente na raiz do repositório para integração nativa com IDEs/CLI:
```json
{
  "mcpServers": {
    "graphify": {
      "command": "graphify-mcp",
      "args": ["${workspace.path}/graphify-out/graph.json"]
    },
    "headroom": {
      "command": "headroom",
      "args": ["mcp", "serve", "--proxy-url", "http://127.0.0.1:8787"]
    }
  }
}
```

### 2. Regras e Workflows (`.agents/`)
* `.agents/rules/graphify.md`: Instrui a IA a consultar o grafo relacional AST antes de buscas exaustivas.
* `.agents/workflows/graphify.md`: Workflow `/graphify` para geração e atualização do grafo de conhecimento.
* `.agents/skills/graphify/SKILL.md`: Definição completa da Skill de navegação AST.

---

## 📊 Benchmarks e Métricas de Economia

### Headroom Context Compression (CCR)
- **Status do Proxy:** Ativo em `http://127.0.0.1:8787`
- **Tokens economizados (lifetime):** ~8,701 tokens (redistribuídos entre chamadas de ferramentas e logs de terminal).
- **Redução em logs e outputs extensos:** Até 90% em saídas repetitivas ou verbosas.

### Graphify AST Knowledge Graph
- **Mapeamento de código:** Extração determinística de nós e arestas com Tree-Sitter zero-cost (sem uso de chamadas de LLM para código).
- **Navegação Eficiente:** Consultas focadas via `graphify query`, `graphify path` e `graphify explain`.

---

## 🚀 Como Usar

### Graphify
```bash
# Gerar ou atualizar o grafo de AST do projeto
graphify extract . --code-only

# Consultar o grafo
graphify query "Qual a estrutura do projeto?"
```

### Headroom
```bash
# Verificar o status do proxy e diagnósticos
headroom doctor

# Verificar economia de tokens acumulada
headroom savings
```
