#!/usr/bin/env bash
# ==============================================================================
# bootstrap-workstation.sh
# Automação de Configuração do Harness Antigravity (Máquina do Trabalho)
# ==============================================================================

set -e

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
uv tool install graphifyy --force 2>/dev/null || uv tool upgrade graphifyy 2>/dev/null || true
graphify install --platform antigravity 2>/dev/null || true

# 3. context-mode (Higiene de Contexto)
if command -v npm &> /dev/null; then
    echo "📦 Instalando / atualizando context-mode global via npm..."
    npm install -g context-mode 2>/dev/null || {
        echo "⚠️ Falha ao instalar context-mode globalmente com npm. Tentando com permissões do usuário..."
        mkdir -p "$HOME/.npm-global"
        npm config set prefix "$HOME/.npm-global"
        export PATH="$HOME/.npm-global/bin:$PATH"
        npm install -g context-mode || true
    }
else
    echo "⚠️ npm não encontrado no PATH. Instale o Node.js 20+ para utilizar o context-mode."
fi

# 3.1 Wrappers determinísticos em ~/.gemini/antigravity/bin/ (Resolução do PATH no Antigravity)
echo "⚙️  Configurando wrappers determinísticos em ~/.gemini/antigravity/bin/..."
mkdir -p "$HOME/.gemini/antigravity/bin"

NODE_PATH_FOUND="$(which node 2>/dev/null || echo "$HOME/.nvm/versions/node/v22.22.1/bin/node")"
CONTEXT_MODE_BUNDLE="$(find "$HOME/.nvm" "$HOME/.npm-global" -name "cli.bundle.mjs" 2>/dev/null | grep "context-mode" | head -n 1 || echo "")"

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
TEMPLATE_AGENT="$SCRIPT_DIR/templates/gemini-orchestrator.agent.md"
DEST_AGENT="$HOME/.gemini/config/agents/gemini-orchestrator/agent.md"

if [ -f "$TEMPLATE_AGENT" ]; then
    cp "$TEMPLATE_AGENT" "$DEST_AGENT"
    echo "  ✓ Copiado de templates/gemini-orchestrator.agent.md"
else
    cat << 'EOF' > "$DEST_AGENT"
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
    echo "  ✓ Registrado a partir do fallback inline"
fi

# 7. Instalar Hooks e Scripts Canônicos da Tríade Determinística
echo "⚡ Instalando Hooks e Scripts de Eficiência de Tokens (Tríade Determinística)..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$HOME/.gemini/config/hooks"
mkdir -p "$HOME/.gemini/config/scripts"

if [ -f "$SCRIPT_DIR/hooks/hooks_dispatcher.py" ]; then
    cp "$SCRIPT_DIR/hooks/hooks_dispatcher.py" "$HOME/.gemini/config/hooks/hooks_dispatcher.py"
    chmod +x "$HOME/.gemini/config/hooks/hooks_dispatcher.py"
    echo "  ✓ hooks_dispatcher.py instalado"
fi

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

if [ -f "$SCRIPT_DIR/scripts/sync_telemetry.sh" ]; then
    cp "$SCRIPT_DIR/scripts/sync_telemetry.sh" "$HOME/.gemini/config/scripts/sync_telemetry.sh"
    chmod +x "$HOME/.gemini/config/scripts/sync_telemetry.sh"
    echo "  ✓ sync_telemetry.sh instalado"
fi

# 7.0 Sincronizar Regras Globais always_on enxutas (backup prévio em caso de divergência)
mkdir -p "$HOME/.gemini/config/rules"
if [ -d "$SCRIPT_DIR/rules" ]; then
    for rule_file in "$SCRIPT_DIR/rules/"*.md; do
        [ -f "$rule_file" ] || continue
        rule_name="$(basename "$rule_file")"
        target_rule="$HOME/.gemini/config/rules/$rule_name"
        if [ -f "$target_rule" ] && ! cmp -s "$rule_file" "$target_rule"; then
            mkdir -p "$HOME/.gemini/config/.backups/rules"
            cp "$target_rule" "$HOME/.gemini/config/.backups/rules/${rule_name}.bak-$(date +%Y%m%d%H%M%S)"
        fi
        cp "$rule_file" "$target_rule"
        echo "  ✓ rule global sincronizada: $rule_name"
    done
fi

# 7.1 Sincronizar hooks.json com Unified Guardrails Dispatcher consolidado
echo "⚙️  Configurando ~/.gemini/config/hooks.json..."
python3 - << 'PYEOF'
import json, os

hooks_file = os.path.expanduser("~/.gemini/config/hooks.json")
dispatcher_path = os.path.expanduser("~/.gemini/config/hooks/hooks_dispatcher.py")
data = {}
if os.path.exists(hooks_file):
    try:
        with open(hooks_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        pass

new_hooks = {}

# PreToolUse unificado (Elo 0 -> Elo 1 CEH -> Elo 1.5 Container Guard -> Elo 3 Advisory + Telemetria)
new_hooks["unified-guardrails-dispatcher"] = {
    "enabled": True,
    "PreToolUse": [
        {
            "matcher": "run_command|ctx_execute|ctx_batch_execute|ctx_execute_file|ctx_purge|call_mcp_tool|read_file|view_file|grep_search|read_url_content|write_file|edit_file|write_to_file|replace_file_content|multi_replace_file_content",
            "hooks": [
                {
                    "type": "command",
                    "command": f"python3 {dispatcher_path}",
                    "timeout": 30
                }
            ]
        }
    ]
}

# PostToolUse (indexação e compressão Context-Mode)
new_hooks["context-mode-guard"] = {
    "enabled": True,
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

# Desativa entradas legadas/redundantes no hooks.json global preservando integridade do plugin CEH
for legacy_key in (
    "destructive-command-guardrail",
    "sail-container-guard",
    "scoped-execution-guard",
    "ceh-stop-guard",
):
    if legacy_key in data and isinstance(data[legacy_key], dict):
        legacy_entry = dict(data[legacy_key])
        legacy_entry["enabled"] = False
        new_hooks[legacy_key] = legacy_entry

# Preserva demais hooks ativos existentes (ex: ralph-stop-guard, antigravity-windows-sync)
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

echo ""
echo "✅ Provisionamento Concluído com Sucesso!"
echo "Verificação:"
echo " - Graphify: $(graphify --version 2>/dev/null || echo 'requer restart do terminal')"
echo " - Skills ativas em ~/.gemini/config/skills: $(ls "$HOME/.gemini/config/skills" 2>/dev/null | wc -l)"
echo " - Hooks ativos em ~/.gemini/config/hooks: $(ls "$HOME/.gemini/config/hooks" 2>/dev/null | wc -l)"
echo " - Utilitários em ~/.gemini/config/scripts: $(ls "$HOME/.gemini/config/scripts" 2>/dev/null | wc -l)"
echo ""
echo "O ambiente está configurado com o Unified Guardrails Dispatcher v0.9.3-p0.1 + Graphify + Git Inspect + RTK."
