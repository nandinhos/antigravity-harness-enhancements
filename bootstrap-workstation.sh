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
echo "O ambiente está configurado com o Unified Guardrails Dispatcher v0.9.2-p0.1 + Graphify + Git Inspect + RTK."
