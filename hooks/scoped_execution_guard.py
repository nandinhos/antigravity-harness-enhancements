#!/usr/bin/env python3
"""
OPT-002: Scoped Execution Guard & Process Confinement
Antigravity Engineering Lab

Aplica limites operacionais determinísticos contra comandos não delimitados:
1. Bloqueia buscas recursivas irrestritas na raiz (/) ou na home do usuário (~).
2. Permite buscas que possuam delimitadores de profundidade (-maxdepth) ou escopo em subdiretórios.
3. Opera com latência inferior a 2 milissegundos.
"""
import sys
import json
import re

# Padrões perigosos de busca global aberta sem delimitadores de profundidade
UNBOUNDED_SCAN_PATTERNS = [
    r"find\s+(~|\$HOME|/home/\w+|/)\s+(?!.*-maxdepth)",
    r"grep\s+(-r|-R)\s+.*(~|\$HOME|/home/\w+|/)\s*$",
]

def check_unbounded_scan(command: str) -> bool:
    cmd_clean = command.strip()
    for pattern in UNBOUNDED_SCAN_PATTERNS:
        if re.search(pattern, cmd_clean):
            return True
    return False

def main():
    try:
        raw_input = sys.stdin.read()
        if not raw_input:
            sys.exit(0)
        payload = json.loads(raw_input)
    except Exception:
        sys.exit(0)

    tool_call = payload.get("toolCall", {})
    tool_name = tool_call.get("name", "")
    args = tool_call.get("args", {})
    command = args.get("CommandLine", "")

    # 1. Interceptação de comandos não delimitados em run_command
    if tool_name == "run_command" and check_unbounded_scan(command):
        output = {
            "decision": "deny",
            "reason": "[OPT-002 SCOPED EXECUTION] Varredura recursiva não delimitada bloqueada. Especifique um subdiretório do projeto ou utilize '-maxdepth 3' para evitar sobrecarga de I/O."
        }
        sys.stdout.write(json.dumps(output))
        sys.exit(0)

    # 2. Comando seguro e dentro do escopo
    sys.exit(0)

if __name__ == "__main__":
    main()

