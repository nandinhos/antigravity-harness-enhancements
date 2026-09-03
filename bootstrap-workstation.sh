#!/usr/bin/env bash
# ==============================================================================
# bootstrap-workstation.sh
# Automação de Configuração do Harness Antigravity (Máquina do Trabalho)
# ==============================================================================

set -e

echo "🚀 Iniciando provisionamento do Harness Antigravity..."

# 1. Dependências Python via uv
if ! command -v uv &> /dev/null; then
    echo "📦 Instalando Astral uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# 2. Instalar Graphify
echo "📦 Instalando / atualizando Graphify..."
uv tool install graphifyy --force 2>/dev/null || uv tool upgrade graphifyy 2>/dev/null || true

# 3. context-mode
if command -v npm &> /dev/null; then
    echo "📦 Instalando context-mode..."
    npm install -g context-mode 2>/dev/null || true
fi

# 4. Clonar / Atualizar Skills Públicas
echo "📦 Sincronizando Suíte Canônica de Skills..."
mkdir -p "$HOME/.claude"
if [ ! -d "$HOME/.claude/skills/.git" ]; then
    git clone https://github.com/nandinhos/skills.git "$HOME/.claude/skills"
else
    cd "$HOME/.claude/skills" && git pull origin main && cd - > /dev/null
fi

# 5. Criar Symlinks no Antigravity / Gemini
echo "🔗 Vinculando as 8 Skills de Ouro no Antigravity..."
mkdir -p "$HOME/.gemini/config/skills"
SKILLS=(
    "systematic-debugging"
    "ddd-deep-domain"
    "legacy-code-sanitizer"
    "repo-reverse-engineering"
    "laravel-migration-planner"
    "laravel-design-system-v3"
    "laravel-frontend-design"
    "learned-lesson"
)

for skill in "${SKILLS[@]}"; do
    if [ -d "$HOME/.claude/skills/$skill" ]; then
        ln -sfn "$HOME/.claude/skills/$skill" "$HOME/.gemini/config/skills/$skill"
        echo "  ✓ $skill"
    fi
done

# 6. Garantir template do Orquestrador Gemini
echo "⚙️  Registrando gemini-orchestrator..."
mkdir -p "$HOME/.gemini/config/agents/gemini-orchestrator"
cat << 'EOF' > "$HOME/.gemini/config/agents/gemini-orchestrator/agent.md"
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
2. **Parcimônia (Anti-Over-Orchestration):** Escopos contidos (1 a 3 arquivos) com causa raiz mapeada são resolvidos diretamente em turno único com o menor diff funcional.
3. **Contrato Canônico de Esforço:** Toda tarefa atômica deve especificar `[effort: low | medium | high]` (default: `medium`).
EOF

echo ""
echo "✅ Provisionamento Concluído com Sucesso!"
echo "Verificação:"
echo " - Graphify: $(graphify --version 2>/dev/null || echo 'requer restart do terminal')"
echo " - Skills ativas em ~/.gemini/config/skills: $(ls "$HOME/.gemini/config/skills" | wc -l)"
echo ""
echo "Para ativar MCPs e hooks, verifique o passo 5 em SETUP_WORK_MACHINE.md"
