# 🛠️ Guia de Replicação do Harness Antigravity (Máquina do Trabalho)
### *Como configurar o mesmo ambiente profissional, determinístico e robusto em um novo computador*

Este documento foi elaborado para ser lido e executado por **você ou diretamente pelo seu Agente Antigravity (`agy`)** na máquina do trabalho. Ele replica com fidelidade absoluta a arquitetura de engenharia, os plugins, as regras do **Ponytail Mode**, o **Graphify**, o **context-mode** e a **Suíte de Skills v2.0**.

---

## 🏗️ Visão Geral da Arquitetura Replicada

```text
                  ANTIGRAVITY CLI (agy) / GEMINI 3.8 FLASH
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         ▼                           ▼                           ▼
┌───────────────────┐       ┌───────────────────┐       ┌───────────────────┐
│   Graphify AST    │       │   context-mode    │       │   Context7 MCP    │
│ - Zero tokens LLM │       │ - Sandbox de tool │       │ - Upstream Docs   │
│ - Tree-Sitter     │       │ - Sessão contínua │       │ - Framework Drift │
└───────────────────┘       └───────────────────┘       └───────────────────┘
         │                           │                           │
         └───────────────────────────┼───────────────────────────┘
                                     ▼
                   ┌───────────────────────────────────┐
                   │     Suíte de 8 Skills de Ouro     │
                   │  github.com/nandinhos/skills.git  │
                   └───────────────────────────────────┘
```

---

## ⚡ Método 1: Instalação Automática em 1 Clique (Recomendado)

Na máquina do trabalho, basta clonar este repositório e executar o script de automação:

```bash
git clone <URL_DESTE_REPO> ~/projects/antigravity-harness-enhancements
cd ~/projects/antigravity-harness-enhancements
bash bootstrap-workstation.sh
```

*(O script instala as dependências, clona as skills, configura os links simbólicos e ajusta os templates de configuração).*

---

## 📋 Método 2: Instalação Passo a Passo (Manual ou Guiada por Agente)

### Passo 1: Pré-requisitos do Sistema (Linux / WSL2 Ubuntu/Debian)
Certifique-se de que os pacotes básicos estão instalados:
```bash
sudo apt update && sudo apt install -y git curl jq build-essential

# Instalar gerenciador rápido de ferramentas Python (uv)
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc # ou source ~/.zshrc

# Instalar Node.js 20+ (via NVM se necessário)
curl -o- https://raw.githubusercontent.com/nandoxdev/nvm/v0.40.0/install.sh | bash # ou nvm padrão
nvm install 22
```

---

### Passo 2: Instalar o Graphify (Knowledge Graph AST)
O Graphify analisa o código deterministicamente a custo zero de tokens:
```bash
# Instala os binários 'graphify' e 'graphify-mcp' globalmente
uv tool install graphifyy

# Verificar versão instalada
graphify --version
```

---

### Passo 3: Instalar e Configurar o `context-mode` (Higiene de Contexto)
O `context-mode` mantém os dados crus de ferramentas fora da janela de contexto:
```bash
npm install -g context-mode
```

---

### Passo 4: Clonar a Suíte Canônica de Skills e Criar Symlinks
Clone o seu repositório de skills e ligue-o à pasta de configuração do Antigravity:
```bash
# 1. Clonar o repositório público de skills na home do Claude
git clone https://github.com/nandinhos/skills.git ~/.claude/skills

# 2. Criar a pasta de skills do Antigravity/Gemini
mkdir -p ~/.gemini/config/skills

# 3. Criar os symlinks das 8 skills de ouro (Single Source of Truth)
for skill in systematic-debugging ddd-deep-domain legacy-code-sanitizer repo-reverse-engineering laravel-migration-planner laravel-design-system-v3 laravel-frontend-design learned-lesson; do
  ln -sfn "$HOME/.claude/skills/$skill" "$HOME/.gemini/config/skills/$skill"
done

# Validar
ls -la ~/.gemini/config/skills/
```

---

### Passo 5: Configurar `~/.gemini/settings.json` (MCPs e Hooks)
Crie ou atualize o arquivo `~/.gemini/settings.json` para ativar os MCP servers (`context7`, `context-mode`, `serena`):

```json
{
  "hasSeenIdeIntegrationNudge": true,
  "ide": { "enabled": true },
  "security": {
    "auth": { "selectedType": "oauth-personal" },
    "disableYoloMode": true,
    "enablePermanentToolApproval": true
  },
  "mcpServers": {
    "context-mode": {
      "command": "context-mode"
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"],
      "env": {
        "CONTEXT7_API_KEY": "SUA_API_KEY_AQUI"
      }
    }
  },
  "hooks": {
    "BeforeTool": [
      {
        "matcher": "run_shell_command|read_file|read_many_files|grep_search|search_file_content|web_fetch|activate_skill",
        "hooks": [{ "type": "command", "command": "context-mode hook gemini-cli beforetool" }]
      }
    ],
    "AfterTool": [
      { "hooks": [{ "type": "command", "command": "context-mode hook gemini-cli aftertool" }] }
    ],
    "PreCompress": [
      { "hooks": [{ "type": "command", "command": "context-mode hook gemini-cli precompress" }] }
    ],
    "SessionStart": [
      { "hooks": [{ "type": "command", "command": "context-mode hook gemini-cli sessionstart" }] }
    ]
  },
  "general": {
    "previewFeatures": true,
    "sessionRetention": { "enabled": true, "maxAge": "120d" }
  }
}
```

---

### Passo 6: Registrar o Agente Orquestrador (`gemini-orchestrator`)
Crie o arquivo de definição do orquestrador em `~/.gemini/config/agents/gemini-orchestrator/agent.md`:

```markdown
---
name: gemini-orchestrator
description: >-
  Orquestrador central Gemini para o Antigravity CLI. Decompõe tarefas complexas,
  roteia para frentes especializadas, atribui modelo + esforço Gemini por tarefa,
  consolida resultados estruturados e usa o knowledge graph Graphify como camada de
  contexto determinística (custo zero de LLM).
---

# Gemini Orchestrator (Antigravity)

## Roteamento de Modelo / Esforço
| Frente | Modelo |
|---|---|
| Arquitetura / design | `gemini-3.1-pro-high` |
| Implementação | `gemini-3.8-flash` com `--effort medium` |
| Refatoração / boilerplate | `gemini-3.8-flash` com `--effort low` |
| Debug / RCA | `gemini-3.8-flash` com `--effort high` |
| Validação / review | `gemini-3.1-pro-high` |

## Princípios Inegociáveis (Ponytail Mode)
1. **AST First:** Sempre consulte o Graphify (`graphify query/path/explain`) antes de ler arquivos brutos.
2. **Parcimônia (Anti-Over-Orchestration):** Escopos contidos (1 a 3 arquivos) com causa raiz mapeada são resolvidos diretamente em turno único com o menor diff funcional. Não instancie subagentes desnecessários.
3. **Contrato Canônico de Esforço:** Toda tarefa atômica deve especificar `[effort: low | medium | high]` (default: `medium`).
```

---

### Passo 7: Como Inicializar o Graphify em Qualquer Projeto no Trabalho
Sempre que você abrir um projeto novo ou existente no trabalho:

```bash
# 1. Dentro da raiz do projeto:
graphify extract . --code-only
graphify cluster-only .

# 2. Instalar as regras do Antigravity e os hooks do Git:
graphify antigravity install
graphify hook install

# 3. (Opcional) Criar .mcp.json local para habilitar MCP tools do grafo:
cat << 'EOF' > .mcp.json
{
  "mcpServers": {
    "graphify": {
      "command": "graphify-mcp",
      "args": ["${workspace.path}/graphify-out/graph.json"]
    }
  }
}
EOF
```

---

## ✅ Checklist de Validação Final na Máquina do Trabalho

Execute estes comandos rápidos para garantir que tudo está 100%:
- [ ] `graphify --version` ➔ Deve retornar `0.9.x`
- [ ] `agy agents` ➔ Deve listar `gemini-orchestrator`, `bc-harness`, `clearer-harness`
- [ ] `ls -la ~/.gemini/config/skills/` ➔ Deve exibir as 8 skills linkadas para `~/.claude/skills/`
- [ ] `graphify query "teste"` ➔ Deve navegar no grafo com sucesso
- [ ] No chat do Antigravity: selecione **Gemini 3.8 Flash (Medium)**.
