# 🤝 HANDOFF DOCUMENT: Antigravity Harness Enhancements
## Para Agent Preset do Antigravity CLI no DeepSeek Harness

> **Status: EXECUTADO.** Este handoff foi consumido — o preset `antigravity-gemini` (DSH) e o agente `gemini-orchestrator` (agy) foram criados e validados. O Headroom foi **removido** da arquitetura. Documento atualizado para refletir o estado final.

---

## 📌 CONTEXTO

O harness de otimização do Antigravity (agy) usa **duas camadas complementares**:

| Camada | Ferramenta | Função |
|---|---|---|
| **Conhecimento de código** | Graphify (`graphifyy`) | Grafo AST determinístico (Tree-Sitter), zero LLM |
| **Higiene de contexto** | context-mode | Sandbox de tool output, continuidade de sessão, think-in-code |

> **Headroom removido:** o proxy CCR do Headroom só atende Anthropic/OpenAI (não há rota Gemini) e foi descontinuado por não se encaixar na metodologia de desenvolvimento. Não reintegrar.

---

## 🗂️ O que foi construído

1. **Preset DSH `antigravity-gemini`** (`~/.dsh/.agent-presets/antigravity-gemini/`):
   - `agent.cordis.yml` — cópia do `token-efficiency` + persona com orquestração Gemini/Antigravity/Graphify + guardrail "não usar Headroom/RTK/caveman".
   - `skills/antigravity-gemini-orchestrator/SKILL.md` — playbook (invocação agy, roteamento modelo/esforço, Graphify, MCP, fluxo de decisão).
   - Validado com `standingKeyFor` → `MOUNT OK`.

2. **Agente orquestrador agy `gemini-orchestrator`** (`~/.gemini/config/agents/gemini-orchestrator/agent.md`):
   - Orquestra frentes Gemini com roteamento de modelo/esforço, fan-out paralelo e consolidação via JSON schema.

---

## 🏗️ Arquitetura final

```
DeepSeek Harness (DSH) ── supervisor
        │  preset antigravity-gemini
        ▼
agy (Antigravity CLI) ── executor/orquestrador Gemini
        │  agent gemini-orchestrator
        ├── Graphify   → conhecimento de código (graph.json, zero-LLM)
        └── context-mode → higiene de contexto (MCP + hooks)
```

---

## ⚙️ Roteamento de modelo/esforço (IDs verificados)

| Frente | Modelo |
|---|---|
| Arquitetura | `gemini-3.1-pro-high` |
| Implementação | `gemini-3.8-flash --effort medium` (ou `gemini-3.7-flash`) |
| Refatoração | `gemini-3.8-flash --effort low` |
| Debug | `gemini-3.8-flash --effort high` |
| Validação | `gemini-3.1-pro-high` |

---

## 🔄 Bootstrap do Graphify por projeto

```bash
graphify extract . --code-only
graphify cluster-only .
graphify antigravity install
graphify hook install
# .mcp.json local (opcional) — só graphify
```

---

## ⚠️ Regras para o dia a dia

1. Graphify primeiro: `graphify query/path/explain` antes de grep/dump.
2. Higiene de contexto é do `context-mode` — não adicionar proxies de compressão (Headroom/RTK) nem brevidade agressiva (caveman).
3. `--effort` só existe para Gemini; não misturar tier embutido no ID com `--effort`.
4. Após editar código: `graphify update .`.
5. **Ponytail Mode (Senior Minimalista)**: entender muito, construir pouco e entregar certo. Menor diff funcional e seguro; reutilizar o existente antes de criar novo; sem over-orchestration de subagentes para tarefas cirúrgicas.

---

## 🔗 Referências

- Repo fonte: `/home/nandodev/projects/antigravity-harness-enhancements`
- Preset DSH: `~/.dsh/.agent-presets/antigravity-gemini/`
- Agente agy: `~/.gemini/config/agents/gemini-orchestrator/agent.md`
- Graphify: `graphify --help`
- context-mode: `~/.gemini/settings.json` (MCP + hooks)

---

*Handoff atualizado após execução — Headroom removido, arquitetura final = Graphify + context-mode + agy/Gemini.*
