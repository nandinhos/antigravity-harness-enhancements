#!/usr/bin/env bash
# ==============================================================================
# bootstrap-workstation.sh
# Automação de Configuração do Harness Antigravity (Máquina do Trabalho)
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Iniciando provisionamento do Harness Antigravity..."

# 0. Ajuste de PATH para subshells não-interativos
export PATH="$HOME/.gemini/antigravity/bin:$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
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

# 3.1 Wrappers determinísticos em ~/.gemini/antigravity/bin/ (Resolução do PATH no Antigravity)
echo "⚙️  Configurando wrappers determinísticos em ~/.gemini/antigravity/bin/..."
mkdir -p "$HOME/.gemini/antigravity/bin"

NODE_PATH_FOUND="$(which node 2>/dev/null || echo "$HOME/.nvm/versions/node/v22.22.1/bin/node")"
CONTEXT_MODE_BUNDLE="$(find "$HOME/.nvm" -name "cli.bundle.mjs" 2>/dev/null | grep "context-mode" | head -n 1 || echo "")"

if [ -n "$CONTEXT_MODE_BUNDLE" ] && [ -x "$NODE_PATH_FOUND" ]; then
    cat << EOF > "$HOME/.gemini/antigravity/bin/context-mode"
#!/usr/bin/env bash
export CONTEXT_MODE_DIR="\${CONTEXT_MODE_DIR:-\$HOME/.gemini/context-mode}"
mkdir -p "\$CONTEXT_MODE_DIR"
export PATH="\$(dirname "$NODE_PATH_FOUND"):$HOME/.local/bin:\$PATH"
exec "$NODE_PATH_FOUND" --no-warnings "$CONTEXT_MODE_BUNDLE" "\$@"
EOF
    chmod +x "$HOME/.gemini/antigravity/bin/context-mode"
    echo "  ✓ context-mode wrapper configurado com CONTEXT_MODE_DIR centralizado"
fi

if [ -f "$HOME/.local/bin/graphify" ]; then
    cat << 'EOF' > "$HOME/.gemini/antigravity/bin/graphify"
#!/usr/bin/env bash
export PATH="$HOME/.local/bin:$PATH"
exec "$HOME/.local/bin/graphify" "$@"
EOF
    chmod +x "$HOME/.gemini/antigravity/bin/graphify"
    echo "  ✓ graphify wrapper configurado"
fi

if [ -f "$HOME/.local/bin/graphify-mcp" ]; then
    cat << 'EOF' > "$HOME/.gemini/antigravity/bin/graphify-mcp"
#!/usr/bin/env bash
export PATH="$HOME/.local/bin:$PATH"
exec "$HOME/.local/bin/graphify-mcp" "$@"
EOF
    chmod +x "$HOME/.gemini/antigravity/bin/graphify-mcp"
    echo "  ✓ graphify-mcp wrapper configurado"
fi

# 3.2 Registro Canônico de MCP Servers em ~/.gemini/config/mcp_config.json
echo "⚙️  Sincronizando servidores MCP em ~/.gemini/config/mcp_config.json..."
mkdir -p "$HOME/.gemini/config"
python3 - << 'PYEOF'
import json, os
mcp_file = os.path.expanduser("~/.gemini/config/mcp_config.json")
data = {"mcpServers": {}}
if os.path.exists(mcp_file):
    try:
        with open(mcp_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        pass

servers = data.setdefault("mcpServers", {})
servers["context-mode"] = {
    "command": os.path.expanduser("~/.gemini/antigravity/bin/context-mode")
}
servers["graphify"] = {
    "command": os.path.expanduser("~/.gemini/antigravity/bin/graphify-mcp")
}

with open(mcp_file, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print("  ✓ mcp_config.json atualizado com context-mode e graphify")
PYEOF

# 3.3 Registro Canônico de Hooks em ~/.gemini/config/hooks.json
echo "⚙️  Sincronizando hooks nativos em ~/.gemini/config/hooks.json..."
python3 - << 'PYEOF'
import json, os
hooks_file = os.path.expanduser("~/.gemini/config/hooks.json")
data = {}
if os.path.exists(hooks_file):
    try:
        with open(hooks_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        pass

data["context-mode-guard"] = {
    "enabled": True,
    "PreToolUse": [
        {
            "matcher": "run_command|view_file|grep_search|read_url_content",
            "hooks": [
                {
                    "type": "command",
                    "command": "context-mode hook antigravity-cli pretooluse",
                    "timeout": 10
                }
            ]
        }
    ],
    "PostToolUse": [
        {
            "matcher": "run_command|view_file|grep_search|read_url_content",
            "hooks": [
                {
                    "type": "command",
                    "command": "context-mode hook antigravity-cli posttooluse",
                    "timeout": 10
                }
            ]
        }
    ]
}

with open(hooks_file, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print("  ✓ hooks.json atualizado com context-mode-guard nativo")
PYEOF

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

# 7. Instalar Hooks e Scripts Canônicos da Tríade Determinística
echo "⚡ Instalando Hooks e Scripts de Eficiência de Tokens (Tríade Determinística)..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$HOME/.gemini/config/hooks"
mkdir -p "$HOME/.gemini/config/scripts"

if [ -f "$SCRIPT_DIR/hooks/context_mode_advisory_router.py" ]; then
    cp "$SCRIPT_DIR/hooks/context_mode_advisory_router.py" "$HOME/.gemini/config/hooks/context_mode_advisory_router.py"
    chmod +x "$HOME/.gemini/config/hooks/context_mode_advisory_router.py"
    echo "  ✓ context_mode_advisory_router.py instalado"
fi

if [ -f "$SCRIPT_DIR/hooks/scoped_execution_guard.py" ]; then
    cp "$SCRIPT_DIR/hooks/scoped_execution_guard.py" "$HOME/.gemini/config/hooks/scoped_execution_guard.py"
    chmod +x "$HOME/.gemini/config/hooks/scoped_execution_guard.py"
    echo "  ✓ scoped_execution_guard.py instalado"
fi

if [ -f "$SCRIPT_DIR/scripts/git_inspect.py" ]; then
    cp "$SCRIPT_DIR/scripts/git_inspect.py" "$HOME/.gemini/config/scripts/git_inspect.py"
    chmod +x "$HOME/.gemini/config/scripts/git_inspect.py"
    echo "  ✓ git_inspect.py instalado"
fi

# 7.1 Sincronizar hooks.json preservando ordem canônica de prioridade
echo "⚙️  Configurando ordem canônica em ~/.gemini/config/hooks.json..."
python3 - << 'PYEOF'
import json, os

hooks_file = os.path.expanduser("~/.gemini/config/hooks.json")
data = {}
if os.path.exists(hooks_file):
    try:
        with open(hooks_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        pass

# Preserva ceh-safety-gate como Prioridade 1
new_hooks = {}
if "ceh-safety-gate" in data:
    new_hooks["ceh-safety-gate"] = data["ceh-safety-gate"]

# Prioridade 2: Scoped Execution Guard (Confinamento e Timeout de 30s)
new_hooks["scoped-execution-guard"] = {
    "enabled": True,
    "PreToolUse": [
        {
            "matcher": "run_command|ctx_execute",
            "hooks": [
                {
                    "type": "command",
                    "command": "python3 \"$HOME/.gemini/config/hooks/scoped_execution_guard.py\"",
                    "timeout": 30
                }
            ]
        }
    ]
}

# Prioridade 3: Smart Advisory Router (Fim de falsos bloqueios com deny)
new_hooks["context-mode-guard"] = {
    "enabled": True,
    "PreToolUse": [
        {
            "matcher": "run_command|view_file|grep_search|read_url_content",
            "hooks": [
                {
                    "type": "command",
                    "command": "python3 \"$HOME/.gemini/config/hooks/context_mode_advisory_router.py\"",
                    "timeout": 10
                }
            ]
        }
    ],
    "PostToolUse": [
        {
            "matcher": "run_command|view_file|grep_search|read_url_content",
            "hooks": [
                {
                    "type": "command",
                    "command": "context-mode hook antigravity-cli posttooluse",
                    "timeout": 10
                }
            ]
        }
    ]
}

# Preserva quaisquer outros hooks existentes (ex: ceh-stop-guard)
for k, v in data.items():
    if k not in new_hooks:
        new_hooks[k] = v

with open(hooks_file, "w", encoding="utf-8") as f:
    json.dump(new_hooks, f, indent=2, ensure_ascii=False)
print("  ✓ hooks.json sincronizado com sucesso!")
PYEOF

# 8. Verificação de Ferramentas Complementares (RTK)
echo "🔍 Verificando presença do RTK (Rust Terminal Kit)..."
if command -v rtk &> /dev/null; then
    echo "  ✓ rtk detectado ($(rtk --version 2>/dev/null || echo 'ativo')) — compressão determinística habilitada"
else
    echo "  ℹ️  rtk não encontrado no PATH. Instalação recomendada para redução de até 56% no volume de bytes de terminal."
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

# Checar Hooks da Tríade
if [ -f "$HOME/.gemini/config/hooks/context_mode_advisory_router.py" ] && [ -f "$HOME/.gemini/config/hooks/scoped_execution_guard.py" ]; then
    echo "  [OK] Hooks da Tríade: context_mode_advisory_router e scoped_execution_guard ativos"
else
    echo "  [FALHA] Hooks da Tríade não encontrados em ~/.gemini/config/hooks/"
    CHECK_FAILURES=$((CHECK_FAILURES + 1))
fi

echo "========================================================"
if [ "$CHECK_FAILURES" -eq 0 ]; then
    echo "✅ Provisionamento Concluído com 100% de Sucesso!"
else
    echo "❌ Concluído com $CHECK_FAILURES falha(s). Verifique os logs acima."
fi
echo "O ambiente está configurado com a Tríade Determinística (Smart Router + Scoped Guard + Git Inspect)."
