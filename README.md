# 🚀 Antigravity Harness Enhancements (v2.0)
### *Eficiência de Tokens Zero-LLM: Graphify AST + context-mode + Módulo de Telemetria*

Repositório dedicado ao enriquecimento de contexto, eliminação de vazamento de logs e economia comprovada de tokens (>94%) no **Antigravity CLI (agy)**.

---

## 🧱 Arquitetura em 3 Camadas

1. **Graphify (Knowledge Graph AST):** analisa o repositório deterministicamente via Tree-Sitter (AST) e expõe `graph.json` via MCP (`graphify-mcp`) para navegação relacional precisa com **custo zero de LLM**.
2. **context-mode (Higiene de Contexto Nativa):** interceptação de ferramentas via hooks em `~/.gemini/config/hooks.json` e servidor MCP global em `~/.gemini/config/mcp_config.json`.
3. **Módulo de Telemetria & Verificação Ponytail:** auditoria determinística automatizada em `scripts/harness-telemetry-benchmark.py`.

---

## 📊 Telemetria Comprovada (`OBSERVED`)

Bateria física de testes auditada pelo benchmark do projeto:

| Métrica | Tradicional (Leituras Brutas/Grep) | Harness Enhancements v2.0 | Redução Real |
|---|---|---|---|
| **Tokens Consumidos** | 19.801 tokens | **1.004 tokens** | **94,93%** |
| **Overhead de Hooks** | Sem interceptação | **55,52 ms** | Zero context bloat |

---

## 🚀 Instalação Rápida (1 Clique)

```bash
git clone https://github.com/nandinhos/antigravity-harness-enhancements.git ~/projects/antigravity-harness-enhancements
cd ~/projects/antigravity-harness-enhancements
bash bootstrap-workstation.sh
```

---

## 🛠️ Comandos do Dia a Dia

```bash
# Consultar arquitetura sem gastar tokens
graphify query "Como funciona o bootstrap?"
graphify god-nodes --top 5

# Atualizar o grafo após alterar código
graphify update .

# Executar benchmark de telemetria
python3 scripts/harness-telemetry-benchmark.py
```

Consulte a documentação completa em:
- [Guia Oficial do Harness](file:///home/nandodev/projects/antigravity-harness-enhancements/HARNESS_DOCUMENTATION.md)
- [Guia de Configuração da Máquina de Trabalho](file:///home/nandodev/projects/antigravity-harness-enhancements/SETUP_WORK_MACHINE.md)
- [Documento de Handoff](file:///home/nandodev/projects/antigravity-harness-enhancements/HANDOFF_ANTIGRAVITY_PRESET.md)
