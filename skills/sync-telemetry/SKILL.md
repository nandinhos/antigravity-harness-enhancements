---
name: sync-telemetry
description: >
  Sincroniza os logs operacionais da estacao de trabalho local com a branch remota
  dev-security-opt-01-p01 no GitHub. Executa o script oficial de telemetria, valida o
  envio do arquivo .jsonl do terminal e exibe o resumo consolidado do dia.
  Ative sempre que o usuario invocar /sync-telemetry ou solicitar sincronizar telemetria.
---

# Sincronizacao de Telemetria Operacional (Multiterminal)

Quando esta skill for invocada (via `/sync-telemetry`):

1. Execute o script canonico no terminal:
   ```bash
   ~/projects/antigravity-harness-enhancements/scripts/sync_telemetry.sh
   ```

2. Obtenha a identidade do terminal e a data atual:
   - Terminal: `cat ~/.gemini/config/terminal.id`
   - Data: `date +%F`

3. Inspecione o arquivo de log correspondente em `~/projects/antigravity-harness-enhancements/telemetry/runs/` e informe:
   - Total de eventos/chamadas de ferramentas registrados hoje.
   - Status do envio para a branch `dev-security-opt-01-p01` no GitHub.
   - Confirmacao visual clara e objetiva para o usuario.
