#!/usr/bin/env python3
"""
OPT-003 / HOOK-OPT-03: Smart Advisory Router para Context-Mode
Antigravity Engineering Lab

Intercepta chamadas PreToolUse para run_command em 3 estágios:
1. SAFE_NATIVE_ALLOWLIST: comandos deliberadamente delimitados recebem allow silencioso (< 1ms).
2. compute_deterministic_overwrite: comandos seguros e verbosos recebem decision="allow" com
   objeto top-level "overwrite" (RTK ou delimitador seguro) sem subprocesso e sem turno extra.
3. Fallback: comandos complexos não cobertos delegam ao hook oficial do context-mode.
"""
import sys
import json
import shutil
import subprocess
import re
from typing import Optional, Tuple

# Comandos de leitura delimitada, mutação segura e metadados que devem rodar diretamente no shell
SAFE_NATIVE_ALLOWLIST = [
    # Git leitura delimitada: status, branch, tags, remotes, hash, diff com flags enxutas, log limitado
    r"^git\s+(?:-C\s+\S+\s+)?(status|branch|tag|remote|rev-parse|diff\s+--stat|diff\s+--check)\b",
    r"^git\s+(?:-C\s+(?:\"[^\"]+\"|'[^']+'|\S+)\s+)?diff\s+(?:[^;|&]*\s)?--(stat|check|numstat|shortstat|name-only|name-status)\b",
    r"^git\s+(?:-C\s+\S+\s+)?log\b.*(-n\s*\d+|--oneline|-\d+)\b",
    r"^git\s+(?:-C\s+\S+\s+)?show\s+--stat\b",
    # Git mutação e sincronização (saída curta / estado)
    r"^git\s+(?:-C\s+\S+\s+)?(add|commit|fetch|pull|push|merge|checkout|switch|stash)\b",
    # Linters com auto-fix intencional (execução direta segura sem overwrite para rtk)
    r"^(?:ruff\s+check|golangci-lint\s+run)\b[^;|&><`\n]*\s(?:--fix\b|--unsafe-fixes\b|--fix-only\b)[^;|&><`\n]*$",
    # Runners de teste com flags explícitas de debug/stdout (não ocultar saída sob rtk)
    r"^(?:pytest|cargo\s+test|npm\s+test|pnpm\s+test)\b[^;|&><`\n]*\s(?:-s\b|--capture=no\b|-r[aAPfE]+\b|-vv+\b|--pdb\b|--nocapture\b)[^;|&><`\n]*$",
    r"^go\s+test\b[^;|&><`\n]*\s-v\b[^;|&><`\n]*$",
    # Scripts utilitários canônicos (portável entre usuários) e checks determinísticos
    r"^python3\s+(?:/home/[^/\s]+|/Users/[^/\s]+|~|\$HOME)/\.gemini/config/scripts/.*",
    r"^python3\s+-m\s+py_compile\b",
    r"^(?:(?:bash|sh)\s+)?(?:\./|(?:/home/[^/\s]+|/Users/[^/\s]+|~|\$HOME)/\S+/)?(?:scripts/|ceh-)[a-zA-Z0-9_.-]+\.sh(?:\s+[^;|&><`\n]*)?$",
    # Utilitários rápidos de sistema, navegação e leitura/manipulação delimitada
    r"^(pwd|whoami|date|uname|id|true)\b(?:\s+-[a-zA-Z0-9]+)*\s*$",
    r"^(?:du\s+-sh|df\s+-h)\b(?:\s+[^\s;|&><`]+)*$",
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


ENV_ASSIGN_PREFIX_RE = re.compile(
    r'^(?:[A-Za-z_][A-Za-z0-9_]*=(?:"[^"]*"|\'[^\']*\'|[^\s;|&><`]+)\s+)+'
)


def _is_single_bounded(segment: str) -> bool:
    cmd_clean = segment.strip()
    if not cmd_clean:
        return False
    cmd_clean = ENV_ASSIGN_PREFIX_RE.sub("", cmd_clean, count=1).strip()
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


def _has_forbidden_shell_syntax(cmd: str) -> bool:
    """Detecta metacaracteres shell complexos fora de aspas (ou substituição em aspas duplas)."""
    if "\n" in cmd or "\r" in cmd:
        return True
    quote = None
    i = 0
    n = len(cmd)
    while i < n:
        ch = cmd[i]
        if ch == "\\" and quote != "'" and i + 1 < n:
            i += 2
            continue
        if ch in ("'", '"'):
            if quote is None:
                quote = ch
            elif quote == ch:
                quote = None
            i += 1
            continue
        if quote == '"':
            if ch == "`" or (ch == "$" and i + 1 < n and cmd[i + 1] == "("):
                return True
        elif quote is None:
            if ch in (";", "|", ">", "<", "`"):
                return True
            if ch == "$" and i + 1 < n and cmd[i + 1] == "(":
                return True
            if ch == "&":
                if i + 1 < n and cmd[i + 1] == "&":
                    i += 2
                    continue
                return True
        i += 1
    return False


def _extract_prefix_and_body(cmd: str) -> Optional[Tuple[str, str]]:
    """Extrai no máximo um prefixo 'cd <dir> &&' e variáveis KEY=VAL iniciais de comandos simples."""
    if _has_forbidden_shell_syntax(cmd):
        return None
    parts = _split_and_chains(cmd.strip())
    if not parts or len(parts) > 2:
        return None

    if len(parts) == 2:
        cd_part = parts[0].strip()
        if not re.match(r'^cd\s+(?:"[^"]+"|\'[^\']+\'|\S+)$', cd_part):
            return None
        cd_prefix = f"{cd_part} && "
        remainder = parts[1].strip()
    else:
        cd_prefix = ""
        remainder = parts[0].strip()

    env_match = re.match(
        r'^((?:[A-Za-z_][A-Za-z0-9_]*=(?:"[^"]*"|\'[^\']*\'|[^\s]+)\s+)+)(.+)$',
        remainder,
    )
    if env_match:
        env_prefix = env_match.group(1)
        base_cmd = env_match.group(2).strip()
    else:
        env_prefix = ""
        base_cmd = remainder

    if not base_cmd or base_cmd.startswith("rtk "):
        return None
    return cd_prefix + env_prefix, base_cmd


MUTATION_OR_OUTPUT_FLAG_RE = re.compile(
    r"(?:^|\s)(?:--fix\b|--unsafe-fixes\b|--fix-only\b|--output(?:=|\s|$)|-o(?:\s|=|$)|--ext-diff\b)"
)
DEBUG_TEST_FLAG_RE = re.compile(
    r"(?:^|\s)(?:-s\b|--capture=no\b|-r[aAPfE]+\b|-vv+\b|--pdb\b|--nocapture\b)"
)


def compute_deterministic_overwrite(
    cmd: str, rtk_available: Optional[bool] = None
) -> Optional[Tuple[str, str]]:
    """
    Estágio 3.2 (HOOK-OPT-03): Reescrita determinística para comandos verbosos seguros.
    Retorna (rewritten_cmd, rule_tag) ou None se já delimitado ou elegível apenas ao context-mode.
    """
    if not cmd or not cmd.strip():
        return None
    if is_deliberately_bounded(cmd):
        return None

    extracted = _extract_prefix_and_body(cmd)
    if extracted is None:
        return None
    prefix, base_cmd = extracted

    # Blindagem Ponto 1: nunca reescrever comandos contendo flags de mutação ou escrita em arquivo
    if MUTATION_OR_OUTPUT_FLAG_RE.search(base_cmd):
        return None

    if rtk_available is None:
        rtk_available = bool(shutil.which("rtk"))

    # OVW-RTK: git diff (flags enxutas já passaram na SAFE_NATIVE_ALLOWLIST)
    if re.match(r'^git\s+(?:-C\s+(?:"[^"]+"|\'[^\']+\'|\S+)\s+)?diff(?:\s|$)', base_cmd):
        if rtk_available:
            return f"{prefix}rtk {base_cmd}", "[ELO3-OVERWRITE-RTK]"
        return None

    # OVW-RTK / OVW-BOUND: git log sem limite (-n / --max-count / -<N>)
    m_log = re.match(
        r'^(git\s+(?:-C\s+(?:"[^"]+"|\'[^\']+\'|\S+)\s+)?log)(?:\s+(.*))?$',
        base_cmd,
    )
    if m_log:
        has_limit = bool(
            re.search(r"(?:^|\s)(?:-n\s*\d+|--max-count(?:=\d+|\s+\d+)|-\d+)\b", base_cmd)
        )
        if not has_limit:
            log_head = m_log.group(1)
            log_rest = (m_log.group(2) or "").strip()
            if rtk_available:
                rewritten_base = f"rtk {log_head} -n 30" + (f" {log_rest}" if log_rest else "")
                return prefix + rewritten_base, "[ELO3-OVERWRITE-RTK]"
            has_format = bool(
                re.search(r"(?:^|\s)(?:--oneline|--pretty(?:=|\s|$)|--format(?:=|\s|$))", base_cmd)
            )
            bound_flags = "-n 30" if has_format else "-n 30 --oneline"
            rewritten_base = f"{log_head} {bound_flags}" + (f" {log_rest}" if log_rest else "")
            return prefix + rewritten_base, "[ELO3-OVERWRITE-BOUND]"
        return None

    # OVW-RTK: runners de teste suportados pelo RTK
    # Blindagem Ponto 2: preservar saída nativa quando flags explícitas de debug estiverem presentes
    if rtk_available and re.match(
        r"^(?:pytest|cargo\s+test|npm\s+test|pnpm\s+test|go\s+test)(?:\s|$)",
        base_cmd,
    ):
        is_go_verbose = bool(
            re.match(r"^go\s+test(?:\s|$)", base_cmd) and re.search(r"(?:^|\s)-v\b", base_cmd)
        )
        if DEBUG_TEST_FLAG_RE.search(base_cmd) or is_go_verbose:
            return None
        return f"{prefix}rtk {base_cmd}", "[ELO3-OVERWRITE-RTK]"

    # OVW-RTK: linters suportados pelo RTK (já filtrados quanto a flags de mutação no Ponto 1)
    if rtk_available and re.match(r"^(?:ruff\s+check|golangci-lint)(?:\s|$)", base_cmd):
        return f"{prefix}rtk {base_cmd}", "[ELO3-OVERWRITE-RTK]"

    # OVW-RTK / OVW-BOUND: leitura de árvore/diretórios sem limite explícito
    # Blindagem Ponto 3: priorizar rtk (preserva exit code nativo) e manter '| head -n 100' como fallback
    is_ro_find = bool(
        re.match(r"^find(?:\s|$)", base_cmd)
        and not re.search(
            r"(?:^|\s)(?:-delete|-exec|-execdir|-ok|-okdir|-fprint0?|-fls|-fprintf)\b",
            base_cmd,
        )
    )
    is_recursive_ls = bool(
        re.match(r"^ls\b", base_cmd)
        and re.search(r"(?:\s-[a-zA-Z]*R|\s--recursive\b)", base_cmd)
    )
    is_tree = bool(
        re.match(r"^tree(?:\s|$)", base_cmd)
        and not re.search(r"(?:^|\s)-o\b", base_cmd)
    )
    if is_ro_find or is_recursive_ls or is_tree:
        if rtk_available:
            return f"{prefix}rtk {base_cmd}", "[ELO3-OVERWRITE-RTK]"
        return f"{prefix}{base_cmd} | head -n 100", "[ELO3-OVERWRITE-BOUND]"

    return None


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
    args = tool_call.get("args", {}) or {}
    if "CommandLine" in args:
        arg_key = "CommandLine"
        command = args.get("CommandLine", "")
    elif "command" in args:
        arg_key = "command"
        command = args.get("command", "")
    else:
        arg_key = "CommandLine"
        command = ""

    # 1. Se for run_command e o comando for deliberadamente delimitado, permite execução silenciosa
    if tool_name == "run_command" and isinstance(command, str):
        if is_deliberately_bounded(command):
            # Saída vazia com exit code 0 significa ALLOW no protocolo de hooks
            sys.exit(0)

        # 2. Reescrita determinística (allow + overwrite) antes do fallback externo
        ovw = compute_deterministic_overwrite(command)
        if ovw is not None:
            rewritten_cmd, rule_tag = ovw
            resp = {
                "decision": "allow",
                "overwrite": {arg_key: rewritten_cmd},
                "reason": f"{rule_tag} Comando reescrito deterministicamente: {rewritten_cmd}",
            }
            sys.stdout.write(json.dumps(resp, ensure_ascii=False))
            sys.exit(0)

    # 3. Se for comando de potencial alto volume ou outra ferramenta, delega para o binário do context-mode
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

