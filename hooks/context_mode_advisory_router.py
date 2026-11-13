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

# Comandos de leitura delimitada, mutação segura e metadados que devem rodar diretamente no shell
SAFE_NATIVE_ALLOWLIST = [
    # Git leitura delimitada: status, branch, tags, remotes, hash, diff --stat/--check, log limitado
    r"^git\s+(?:-C\s+\S+\s+)?(status|branch|tag|remote|rev-parse|diff\s+--stat|diff\s+--check)\b",
    r"^git\s+(?:-C\s+\S+\s+)?log\b.*(-n\s*\d+|--oneline|-\d+)\b",
    r"^git\s+(?:-C\s+\S+\s+)?show\s+--stat\b",
    # Git mutação e sincronização (saída curta / estado)
    r"^git\s+(?:-C\s+\S+\s+)?(add|commit|fetch|pull|push|merge|checkout|switch|stash)\b",
    # Scripts utilitários canônicos (portável entre usuários) e checks determinísticos
    r"^python3\s+(?:/home/[^/\s]+|/Users/[^/\s]+|~|\$HOME)/\.gemini/config/scripts/.*",
    r"^python3\s+-m\s+py_compile\b",
    r"^(?:\./)?scripts/[a-zA-Z0-9_.-]+\.sh\b",
    # Utilitários rápidos de sistema, navegação e leitura/manipulação delimitada
    r"^(pwd|whoami)\b\s*$",
    r"^(which|echo|head|tail|wc|stat|mkdir|cp|mv|chmod|diff)\b(?:\s+.*)?$",
    r"^ls\b(?![^|]*\s-[a-zA-Z]*R)(?:\s+.*)?$",
    r"^cat\s+(?:-[a-zA-Z]+\s+)*[^\s]+$",
    # Pipelines com delimitador explícito no final
    r".*\|\s*(head|tail|wc|grep)\b.*",
]


def _split_and_chains(cmd: str) -> list:
    """Divide comandos encadeados por '&&' respeitando aspas simples/duplas."""
    parts = []
    buf = []
    quote = None
    i = 0
    n = len(cmd)
    while i < n:
        ch = cmd[i]
        if ch == "\\" and quote != "'" and i + 1 < n:
            buf.append(ch)
            buf.append(cmd[i + 1])
            i += 2
            continue
        if ch in ("'", '"'):
            if quote is None:
                quote = ch
            elif quote == ch:
                quote = None
            buf.append(ch)
            i += 1
            continue
        if quote is None and cmd[i:i + 2] == "&&":
            seg = "".join(buf).strip()
            if seg:
                parts.append(seg)
            buf = []
            i += 2
            continue
        buf.append(ch)
        i += 1
    tail = "".join(buf).strip()
    if tail:
        parts.append(tail)
    return parts


def _is_single_bounded(segment: str) -> bool:
    cmd_clean = segment.strip()
    if not cmd_clean:
        return False
    # Suporte nativo transparente ao prefixo rtk
    if cmd_clean.startswith("rtk "):
        cmd_clean = cmd_clean[4:].strip()
    for pattern in SAFE_NATIVE_ALLOWLIST:
        if re.search(pattern, cmd_clean, re.IGNORECASE):
            return True
    return False


def is_deliberately_bounded(cmd: str) -> bool:
    parts = _split_and_chains(cmd.strip())
    if not parts:
        return False
    return all(_is_single_bounded(part) for part in parts)

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

