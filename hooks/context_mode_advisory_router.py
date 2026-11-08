#!/usr/bin/env python3
"""
OPT-003: Smart Advisory Router para Context-Mode
Antigravity Engineering Lab

Intercepta chamadas PreToolUse para run_command:
- Comandos deliberadamente delimitados (git status, log -n, branch, diff --stat, etc.)
  recebem execução nativa silenciosa (SILENT_ALLOW), eliminando falsos bloqueios.
- Comandos potencialmente massivos (git log -p ilimitado, dumps, find aberto)
  são delegados ao hook oficial do context-mode para emitir a recomendação de MCP.
"""
import sys
import json
import subprocess
import re

# Comandos de leitura delimitada e metadados que devem rodar diretamente no shell
SAFE_NATIVE_ALLOWLIST = [
    # Git: status, branch, tags, remotes, hash, diff --stat, log limitado
    r"^git\s+(status|branch|tag|remote|rev-parse|diff\s+--stat|diff\s+--check)",
    r"^git\s+(-C\s+\S+\s+)?(status|branch|tag|remote|rev-parse|diff\s+--stat|diff\s+--check)",
    r"^git\s+(-C\s+\S+\s+)?log\s+.*(-n\s*\d+|--oneline|-[\d]+).*",
    r"^git\s+log\s+.*(-n\s*\d+|--oneline|-[\d]+).*",
    r"^git\s+show\s+--stat",
    # Scripts utilitarios canonicos em ~/.gemini/config/scripts/
    r"^python3\s+/home/nandodev/\.gemini/config/scripts/.*",
    # Utilitários rápidos de sistema e navegação
    r"^(pwd|which|whoami|echo\s+|head\s+|tail\s+|wc\s+|cat\s+[^\s]+)$",
    # Pipelines com delimitador explícito no final
    r".*\|\s*(head|tail|wc|grep)\b.*"
]

def is_deliberately_bounded(cmd: str) -> bool:
    cmd_clean = cmd.strip()
    # Suporte nativo transparente ao prefixo rtk
    if cmd_clean.startswith('rtk '):
        cmd_clean = cmd_clean[4:].strip()
    for pattern in SAFE_NATIVE_ALLOWLIST:
        if re.search(pattern, cmd_clean, re.IGNORECASE):
            return True
    return False

def main():
    try:
        raw_input = sys.stdin.read()
        if not raw_input:
            sys.exit(0)
            
        payload = json.loads(raw_input)
    except Exception:
        # Em caso de falha de parsing, fail-safe permitindo a execução
        sys.exit(0)

    tool_call = payload.get("toolCall", {})
    tool_name = tool_call.get("name", "")
    args = tool_call.get("args", {})
    command = args.get("CommandLine", "")

    # 1. Se for run_command e o comando for deliberadamente delimitado, permite execução silenciosa
    if tool_name == "run_command" and is_deliberately_bounded(command):
        # Saída vazia com exit code 0 significa ALLOW no protocolo de hooks
        sys.exit(0)

    # 2. Se for comando de potencial alto volume ou outra ferramenta, delega para o binário do context-mode
    try:
        proc = subprocess.run(
            ["context-mode", "hook", "antigravity-cli", "pretooluse"],
            input=raw_input,
            capture_output=True,
            text=True
        )
        sys.stdout.write(proc.stdout)
        sys.exit(proc.returncode)
    except Exception:
        sys.exit(0)

if __name__ == "__main__":
    main()

