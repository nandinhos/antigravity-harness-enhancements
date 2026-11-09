#!/usr/bin/env bash
# sync_telemetry.sh — Sincroniza logs de telemetria da estação local para a branch remota dev-security-opt-01-p01
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> Sincronizando telemetria em: $REPO_DIR"

# Adiciona apenas a pasta telemetry/runs/
git -C "$REPO_DIR" add telemetry/runs/

# Commita se houver alterações
if ! git -C "$REPO_DIR" diff --cached --quiet; then
    TERMINAL_NAME="$(cat ~/.gemini/config/terminal.id 2>/dev/null || echo "terminal-local")"
    DATE_STR="$(date +%F)"
    git -C "$REPO_DIR" commit -m "chore (telemetry): sincronizar logs operacionais de $DATE_STR ($TERMINAL_NAME)

- Atualização periódica de logs em telemetry/runs/
- Registrado automaticamente pelo script de sincronização." --no-verify
    echo "==> Commit de telemetria registrado com sucesso."
else
    echo "==> Nenhum log novo para commitar."
fi

# Dispara o push para a branch dev-security-opt-01-p01
echo "==> Enviando logs para origin dev-security-opt-01-p01..."
git -C "$REPO_DIR" push origin dev-security-opt-01-p01
echo "==> Sincronização concluída com sucesso."

