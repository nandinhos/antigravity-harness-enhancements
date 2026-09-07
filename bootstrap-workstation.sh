#!/usr/bin/env bash
# ==============================================================================
# bootstrap-workstation.sh
# Automação de Configuração do Harness Antigravity (Máquina do Trabalho)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Iniciando provisionamento do Harness Antigravity..."

# 0. Ajuste de PATH para subshells não-interativos
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
if [ -d "$HOME/.nvm" ] && [ -s "$HOME/.nvm/nvm.sh" ]; then
    # Carrega o NVM se disponível para garantir o node/npm corretos
    # shellcheck source=/dev/null
    \. "$HOME/.nvm/nvm.sh" || true
fi

# 1. Dependências Python via uv
if ! command -v uv &> /dev/null; then
    echo "📦 Instalando Astral uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
else
    echo "✓ Astral uv já instalado: $(uv --version)"
fi

# 2. Instalar / atualizar Graphify
echo "📦 Instalando / atualizando Graphify via uv..."
uv tool install graphifyy --force || uv tool upgrade graphifyy
graphify install --platform antigravity || true

# 3. context-mode (Higiene de Contexto)
if command -v npm &> /dev/null; then
    echo "📦 Instalando / atualizando context-mode global via npm..."
    npm install -g context-mode || {
        echo "⚠️ Falha ao instalar context-mode globalmente com npm. Tentando com permissões do usuário..."
        mkdir -p "$HOME/.npm-global"
        npm config set prefix "$HOME/.npm-global"
        export PATH="$HOME/.npm-global/bin:$PATH"
        npm install -g context-mode
    }
else
    echo "⚠️ npm não encontrado no PATH. Instale o Node.js 20+ para utilizar o context-mode."
fi

# 4. Clonar / Atualizar Skills Canônicas
echo "📦 Sincronizando Suíte Canônica de Skills..."
mkdir -p "$HOME/.claude"
if [ ! -d "$HOME/.claude/skills/.git" ]; then
    git clone https://github.com/nandinhos/skills.git "$HOME/.claude/skills"
else
    echo "  Atualizando repositório de skills..."
    git -C "$HOME/.claude/skills" pull origin main
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

LINKED_SKILLS_COUNT=0
for skill in "${SKILLS[@]}"; do
    if [ -d "$HOME/.claude/skills/$skill" ]; then
        ln -sfn "$HOME/.claude/skills/$skill" "$HOME/.gemini/config/skills/$skill"
        echo "  ✓ $skill"
        LINKED_SKILLS_COUNT=$((LINKED_SKILLS_COUNT + 1))
    else
        echo "  ⚠️ Skill $skill não encontrada em ~/.claude/skills/$skill"
    fi
done

# 6. Registrar Agente Orquestrador Gemini a partir do template canônico
echo "⚙️  Registrando gemini-orchestrator canônico..."
mkdir -p "$HOME/.gemini/config/agents/gemini-orchestrator"
TEMPLATE_AGENT="$SCRIPT_DIR/templates/gemini-orchestrator.agent.md"
DEST_AGENT="$HOME/.gemini/config/agents/gemini-orchestrator/agent.md"

if [ -f "$TEMPLATE_AGENT" ]; then
    cp "$TEMPLATE_AGENT" "$DEST_AGENT"
    echo "  ✓ Copiado de templates/gemini-orchestrator.agent.md"
else
    echo "  ⚠️ Template $TEMPLATE_AGENT não encontrado! Mantendo agente existente se houver."
fi

# ==============================================================================
# Health Check / Auto-Diagnóstico de Conformidade
# ==============================================================================
echo ""
echo "========================================================"
echo "🩺 Executando Health Check de Conformidade do Harness..."
echo "========================================================"

CHECK_FAILURES=0

# Checar Graphify
if command -v graphify &> /dev/null; then
    echo "  [OK] Graphify: $(graphify --version)"
else
    echo "  [FALHA] Graphify não encontrado no PATH!"
    CHECK_FAILURES=$((CHECK_FAILURES + 1))
fi

# Checar context-mode
if command -v context-mode &> /dev/null; then
    echo "  [OK] context-mode: Instalado e detectável no PATH"
else
    echo "  [AVISO] context-mode não encontrado no PATH (verifique a instalação do Node/npm)"
fi

# Checar Skills Linkadas
if [ "$LINKED_SKILLS_COUNT" -eq 8 ]; then
    echo "  [OK] Skills de Ouro: 8/8 ativas em ~/.gemini/config/skills"
else
    echo "  [AVISO] Skills de Ouro: Apenas $LINKED_SKILLS_COUNT/8 linkadas"
fi

# Checar Orquestrador
if [ -f "$DEST_AGENT" ]; then
    AGENT_LINES=$(wc -l < "$DEST_AGENT")
    if [ "$AGENT_LINES" -ge 70 ]; then
        echo "  [OK] gemini-orchestrator: Configuração canônica completa ($AGENT_LINES linhas)"
    else
        echo "  [AVISO] gemini-orchestrator: Arquivo menor que o esperado ($AGENT_LINES linhas)"
    fi
else
    echo "  [FALHA] gemini-orchestrator não configurado!"
    CHECK_FAILURES=$((CHECK_FAILURES + 1))
fi

echo "========================================================"
if [ "$CHECK_FAILURES" -eq 0 ]; then
    echo "✅ Provisionamento Concluído com 100% de Sucesso!"
else
    echo "❌ Concluído com $CHECK_FAILURES falha(s). Verifique os logs acima."
fi
echo "Para ativar MCPs e hooks, confira o Passo 5 em SETUP_WORK_MACHINE.md."
