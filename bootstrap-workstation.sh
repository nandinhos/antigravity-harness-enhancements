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

echo ""
echo "✅ Provisionamento Concluído com Sucesso!"
echo "Verificação:"
echo " - Graphify: $(graphify --version 2>/dev/null || echo 'requer restart do terminal')"
echo " - Skills ativas em ~/.gemini/config/skills: $(ls "$HOME/.gemini/config/skills" 2>/dev/null | wc -l)"
echo " - Hooks ativos em ~/.gemini/config/hooks: $(ls "$HOME/.gemini/config/hooks" 2>/dev/null | wc -l)"
echo " - Utilitários em ~/.gemini/config/scripts: $(ls "$HOME/.gemini/config/scripts" 2>/dev/null | wc -l)"
echo ""
echo "O ambiente está configurado com a Tríade Determinística (Smart Router + Scoped Guard + Git Inspect)."
