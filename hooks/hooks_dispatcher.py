#!/usr/bin/env python3
"""
hooks_dispatcher.py — Unified Guardrails Dispatcher com Normalizador Universal P0
Antigravity Engineering Lab & Harness Enhancements (SECURITY-OPT-01 — Fase P0)

Responsabilidades do Dispatcher Monoprocesso:
  1. Fail-Closed Rigoroso: Validação estrita de sintaxe, tipos, payloads vazios e erros com exit 0 + deny.
  2. Normalizador Universal de Payloads: Desembrulho iterativo de 'call_mcp_tool', normalização tipada
     de comandos ('CommandLine', 'code', 'commands[]') e caminhos ('Path', 'TargetFile').
  3. Confinamento de Escopo & Proteção de Filesystem: Bloqueio de escape do workspace, proteção de .ceh/ e .git/.
  4. Elo 1 (CEH Safety Gate): Governança de destruição, ambientes (DEV/HML/PRD) e chamadas de SO embutidas.
  5. Elo 2 (Scoped Execution Guard): Bloqueio determinístico de varreduras na raiz (find /, grep -r /).
  6. Elo 3 (Smart Advisory Router): Roteamento delimitado silencioso e consulta context-mode com timeout estrito.

Contrato com a IDE Antigravity:
  Toda decisão estruturada ('allow' silencioso ou 'deny' com justificativa) DEVE retornar exit code 0.
  Códigos de saída != 0 são interpretados pela IDE como falha de infraestrutura, resultando em bypass (fail-open).
"""

from __future__ import annotations
import sys
import os
import re
import json
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, List, Tuple, Optional

# Inclusão de caminhos de módulos (prioriza repositório dev se presente, com fallback para plugin ativo)
DEV_CEH_SCRIPTS = Path("/home/nandodev/projects/clearer-engineering-harness/clearer-engineering/scripts")
PLUGIN_CEH_SCRIPTS = Path("/home/nandodev/.gemini/config/plugins/clearer-engineering/scripts")
HOOKS_CONFIG_DIR = Path("/home/nandodev/.gemini/config/hooks")
LOCAL_HOOKS_DIR = Path(__file__).resolve().parent

for p in (DEV_CEH_SCRIPTS, PLUGIN_CEH_SCRIPTS, HOOKS_CONFIG_DIR, LOCAL_HOOKS_DIR):
    if p.is_dir() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

# Importação dos módulos de governança e segurança
_SAFETY_GATE_AVAILABLE = False
_SAFETY_GATE_ERROR = None
try:
    from hook_context import handle_hook_lifecycle
    from ceh_core.engine import evaluate as evaluate_ceh, evaluate_command, Request, Decision, is_protected_target
    _SAFETY_GATE_AVAILABLE = True
except Exception as e:
    _SAFETY_GATE_ERROR = e

_SCOPED_GUARD_AVAILABLE = False
_SCOPED_GUARD_ERROR = None
try:
    import scoped_execution_guard
    check_unbounded_scan = scoped_execution_guard.check_unbounded_scan
    _SCOPED_GUARD_AVAILABLE = True
except Exception as e:
    _SCOPED_GUARD_ERROR = e

_ADVISORY_ROUTER_AVAILABLE = False
_ADVISORY_ROUTER_ERROR = None
try:
    import context_mode_advisory_router
    is_deliberately_bounded = context_mode_advisory_router.is_deliberately_bounded
    _ADVISORY_ROUTER_AVAILABLE = True
except Exception as e:
    _ADVISORY_ROUTER_ERROR = e

# Padrões catastróficos imediatos (Hard Blocks em memória)
HARD_BLOCK_PATTERNS = [
    # Filesystem / SO Catastrófico
    (r"\brm\s+-[rRfF]*\s+(?:/|~|\$HOME)(?:\s|$)", "Tentativa de exclusão catastrófica da raiz ou home do sistema."),
    (r"\brm\s+-[rRfF]*\s+\.git\b", "Tentativa de exclusão do diretório de versionamento Git (.git)."),
    (r"\bmkfs\b", "Comando de formatação de sistema de arquivos (mkfs) não permitido."),
    (r"\bdd\s+if=", "Comando de baixo nível 'dd' não permitido."),
    (r"\bchmod\s+-[rRfF]*\s+777\s+/(?:\s|$)", "Permissões abertas e inseguras (chmod 777 /) não permitidas."),
    (r":\(\)\s*\{\s*:\|:&\s*\};:", "Fork bomb detectada e bloqueada."),

    # Banco de Dados - Artisan / Laravel Destrutivo
    (r"\bphp\s+artisan\s+migrate:fresh\b", "Comando destrutivo 'migrate:fresh' apagaria todas as tabelas e dados. Use 'migrate' incremental."),
    (r"\bphp\s+artisan\s+migrate:reset\b", "Comando 'migrate:reset' reverteria todas as migrações. Operação proibida."),
    (r"\bphp\s+artisan\s+db:wipe\b", "Comando 'db:wipe' apagaria completamente o banco de dados. Operação proibida."),
    (r"\bartisan\s+migrate:fresh\b", "Comando 'migrate:fresh' apagaria todas as tabelas e dados. Operação proibida."),
    (r"\bartisan\s+migrate:reset\b", "Comando 'migrate:reset' reverteria todas as migrações. Operação proibida."),
    (r"\bartisan\s+db:wipe\b", "Comando 'db:wipe' apagaria o banco de dados. Operação proibida."),

    # Banco de Dados - SQL Destrutivo direto
    (r"\bDROP\s+DATABASE\b", "Comando SQL 'DROP DATABASE' não permitido."),
    (r"\bDROP\s+SCHEMA\b", "Comando SQL 'DROP SCHEMA' não permitido."),
    (r"\bTRUNCATE\s+(?:TABLE\s+)?[`\"']?[a-zA-Z0-9_]+[`\"']?", "Comando 'TRUNCATE TABLE' destrutivo em banco de dados bloqueado."),
    (r"\bDELETE\s+FROM\s+[`\"']?[a-zA-Z0-9_]+[`\"']?\s*(?:;|\s*$)", "Comando 'DELETE' sem cláusula WHERE detectado. Risco de perda total de registros."),

    # Git Destrutivo em Branches Principais
    (r"\bgit\s+push\b.*(?:-f\b|--force\b|--force-with-lease\b).*(?:\bmain\b|\bmaster\b|\bproduction\b|\bprod\b)", "Force push para branches protegidas (main/master/production) estritamente proibido."),
    (r"\bgit\s+push\b.*(?:\bmain\b|\bmaster\b|\bproduction\b|\bprod\b).*(?:-f\b|--force\b|--force-with-lease\b)", "Force push para branches protegidas (main/master/production) estritamente proibido."),
]

# Ferramentas benignas ou de suporte nativo reconhecidas pelo harness e MCPs instalados
ALLOWED_BENIGN_TOOLS = {
    # Ferramentas nativas do Antigravity
    "read_file", "view_file", "grep_search", "read_url_content",
    "ask_question", "schedule", "manage_task", "send_message",
    "manage_subagents", "define_subagent", "invoke_subagent",
    "list_resources", "read_resource", "search_marketplace", "search_web",
    "list_plugin_accounts",

    # MCP gemini-api-docs
    "gemini_search_docs", "gemini_get_doc",

    # MCP context-mode (consultas e metadados)
    "ctx_search", "ctx_stats", "ctx_index", "ctx_insight", "ctx_doctor",
    "ctx_upgrade", "ctx_fetch_and_index",

    # MCP dev-memory
    "memory_list", "memory_search", "memory_get", "memory_related",
    "relation_extract_propose", "memory_create", "memory_stats",
    "memory_update", "memory_validate", "memory_promote", "memory_delete",
    "hub_briefing", "memory_ingest", "harness_paths", "harness_capture",
    "harness_list", "harness_provision", "harness_installer_script",
    "harness_hook_script",

    # MCP dak-notebook
    "get_cell_outputs", "search_cells", "create_notebook", "read_cell",
    "replace_cell", "list_cells", "insert_cell", "delete_cell", "get_notebook_info"
}

# Categorias canônicas de ferramentas
TOOL_CATEGORIES = {
    "run_command": "TERMINAL",
    "write_file": "FILE_WRITE",
    "edit_file": "FILE_WRITE",
    "write_to_file": "FILE_WRITE",
    "replace_file_content": "FILE_WRITE",
    "multi_replace_file_content": "FILE_WRITE",
    "ctx_execute": "MCP_EXEC",
    "ctx_execute_file": "MCP_EXEC",
    "ctx_batch_execute": "MCP_EXEC",
    "ctx_purge": "MCP_DATA",
}


@dataclass
class NormalizedToolCall:
    raw_name: str
    canonical_name: str
    category: str
    commands: List[str] = field(default_factory=list)
    target_paths: List[str] = field(default_factory=list)
    cwd: Optional[str] = None
    language: Optional[str] = None
    is_purge_destructive: bool = False
    original_args: Dict[str, Any] = field(default_factory=dict)
    workspace_paths: List[str] = field(default_factory=list)


def _make_deny(reason: str) -> Tuple[Dict[str, Any], int]:
    """Retorna resposta padronizada de negação com exit code 0 para a IDE Antigravity."""
    return {"decision": "deny", "reason": reason}, 0


def normalize_payload(raw_input: str) -> Tuple[Optional[NormalizedToolCall], Optional[Tuple[Dict[str, Any], int]]]:
    """
    Normalizador Universal de Payloads (Fase P0).
    Realiza validação sintática, tipada, desembrulho de call_mcp_tool e extração estruturada.
    Retorna (normalized_tool_call, error_tuple). Se error_tuple for preenchido, encerra imediatamente.
    """
    if raw_input is None or not raw_input.strip():
        return None, _make_deny("[CEH FAIL-CLOSED] Payload vazio ou ausente recebido pelo hook PreToolUse.")

    try:
        payload = json.loads(raw_input)
    except Exception as e:
        return None, _make_deny(f"[CEH FAIL-CLOSED] Payload JSON malformado ou truncado ({e}).")

    if not isinstance(payload, dict):
        return None, _make_deny("[CEH FAIL-CLOSED] Formato de payload inválido: esperava objeto JSON na raiz.")

    tc = payload.get("toolCall")
    if not isinstance(tc, dict):
        return None, _make_deny("[CEH FAIL-CLOSED] Formato inválido: campo 'toolCall' ausente ou inválido.")

    raw_name = str(tc.get("name", "")).strip()
    if not raw_name:
        return None, _make_deny("[CEH FAIL-CLOSED] Nome de ferramenta ausente ou vazio em 'toolCall.name'.")

    args = tc.get("args")
    if args is None:
        args = {}
    if not isinstance(args, dict):
        return None, _make_deny("[CEH FAIL-CLOSED] 'toolCall.args' deve ser um objeto JSON.")

    workspace_paths = payload.get("workspacePaths") or []
    if not isinstance(workspace_paths, list):
        workspace_paths = []

    # Desembrulho iterativo de 'call_mcp_tool' com limite de profundidade (max_depth=3)
    curr_name = raw_name
    curr_args = args
    depth = 0

    while curr_name == "call_mcp_tool" and depth < 3:
        depth += 1
        inner_tool = curr_args.get("ToolName")
        inner_args = curr_args.get("Arguments")

        if not inner_tool or not isinstance(inner_tool, str):
            return None, _make_deny("[CEH FAIL-CLOSED] 'call_mcp_tool' requer 'ToolName' como string válida.")
        if inner_args is None:
            inner_args = {}
        if not isinstance(inner_args, dict):
            return None, _make_deny("[CEH FAIL-CLOSED] 'call_mcp_tool.Arguments' deve ser um objeto JSON.")

        curr_name = str(inner_tool).strip()
        curr_args = inner_args

    if curr_name == "call_mcp_tool":
        return None, _make_deny("[CEH FAIL-CLOSED] Limite de profundidade de aninhamento de call_mcp_tool excedido (>3).")

    canonical_name = curr_name
    category = TOOL_CATEGORIES.get(canonical_name, "BENIGN" if canonical_name in ALLOWED_BENIGN_TOOLS else "UNKNOWN")

    commands: List[str] = []
    target_paths: List[str] = []
    cwd: Optional[str] = curr_args.get("Cwd") or curr_args.get("cwd")
    language: Optional[str] = curr_args.get("language")
    is_purge = False

    # Validação e extração tipada por categoria de ferramenta
    if canonical_name == "run_command":
        cmd_line = curr_args.get("CommandLine")
        if cmd_line is None:
            return None, _make_deny("[CEH FAIL-CLOSED] 'run_command' exige o argumento obrigatório 'CommandLine'.")
        if not isinstance(cmd_line, str):
            return None, _make_deny("[CEH FAIL-CLOSED] 'CommandLine' em 'run_command' deve ser uma string.")
        if not cmd_line.strip():
            # Comando vazio em run_command
            commands = [""]
        else:
            commands = [cmd_line]

    elif canonical_name in ("write_file", "edit_file", "write_to_file", "replace_file_content", "multi_replace_file_content"):
        # Suporte unificado: Path (nativo atual) ou TargetFile (legado)
        target = curr_args.get("Path") or curr_args.get("TargetFile")
        if target is None:
            return None, _make_deny(f"[CEH FAIL-CLOSED] Ferramenta de escrita '{canonical_name}' sem caminho de arquivo alvo (Path/TargetFile).")
        if not isinstance(target, str):
            return None, _make_deny(f"[CEH FAIL-CLOSED] Caminho do arquivo em '{canonical_name}' deve ser uma string.")
        if not target.strip():
            return None, _make_deny(f"[CEH FAIL-CLOSED] Caminho de arquivo alvo vazio em '{canonical_name}'.")
        target_paths = [target.strip()]

    elif canonical_name == "ctx_execute":
        code_str = curr_args.get("code")
        if code_str is None:
            return None, _make_deny("[CEH FAIL-CLOSED] 'ctx_execute' exige o argumento obrigatório 'code'.")
        if not isinstance(code_str, str):
            return None, _make_deny("[CEH FAIL-CLOSED] Argumento 'code' em 'ctx_execute' deve ser uma string.")
        commands = [code_str]

    elif canonical_name == "ctx_execute_file":
        code_str = curr_args.get("code")
        file_path = curr_args.get("path")
        if code_str is None or file_path is None:
            return None, _make_deny("[CEH FAIL-CLOSED] 'ctx_execute_file' exige os argumentos 'code' e 'path'.")
        if not isinstance(code_str, str) or not isinstance(file_path, str):
            return None, _make_deny("[CEH FAIL-CLOSED] 'code' e 'path' em 'ctx_execute_file' devem ser strings.")
        commands = [code_str]
        target_paths = [file_path.strip()]

    elif canonical_name == "ctx_batch_execute":
        batch_cmds = curr_args.get("commands")
        if not isinstance(batch_cmds, list) or len(batch_cmds) == 0:
            return None, _make_deny("[CEH FAIL-CLOSED] 'ctx_batch_execute' exige lista não-vazia no argumento 'commands'.")
        for idx, item in enumerate(batch_cmds):
            if not isinstance(item, dict):
                return None, _make_deny(f"[CEH FAIL-CLOSED] Item {idx} em 'ctx_batch_execute.commands' deve ser um objeto JSON.")
            c_str = item.get("command")
            if not isinstance(c_str, str):
                return None, _make_deny(f"[CEH FAIL-CLOSED] Campo 'command' do item {idx} no 'ctx_batch_execute' deve ser string.")
            commands.append(c_str)

    elif canonical_name == "ctx_purge":
        confirm_val = curr_args.get("confirm")
        scope_val = str(curr_args.get("scope", "")).strip().lower()
        if confirm_val is True and scope_val in ("project", ""):
            is_purge = True

    elif category == "UNKNOWN":
        name_lower = canonical_name.lower()
        dangerous_keywords = ("exec", "run", "eval", "shell", "cmd", "bash", "delete", "drop", "wipe", "purge", "write", "modify", "destroy", "kill", "tunnel")
        if any(kw in name_lower for kw in dangerous_keywords):
            return None, _make_deny(f"[CEH FAIL-CLOSED] Ferramenta não homologada com perfil de risco de execução/mutação ('{canonical_name}').")
        # Se for ferramenta não cadastrada de consulta, registra como benigna com aviso em DEV
        category = "BENIGN"

    normalized = NormalizedToolCall(
        raw_name=raw_name,
        canonical_name=canonical_name,
        category=category,
        commands=commands,
        target_paths=target_paths,
        cwd=cwd,
        language=language,
        is_purge_destructive=is_purge,
        original_args=curr_args,
        workspace_paths=[str(p) for p in workspace_paths if p]
    )
    return normalized, None


def validate_path_confinement(paths: List[str], cwd: Optional[str], workspace_paths: List[str]) -> Optional[str]:
    """
    Valida confinamento de caminhos de arquivos contra:
      1. Caracteres nulos (\0) e injeção lexical.
      2. Certificados protegidos de CI (.ceh/last-ci-run.json, etc.).
      3. Estruturas internas do Git (.git/).
      4. Diretórios restritos do sistema (/etc, /root, /boot, /sys, /proc, /usr, /bin, /sbin).
      5. Escape dos limites do workspace via traversal (..).
    Retorna mensagem de erro para bloqueio imediato ou None se válido.
    """
    ws_root: Optional[Path] = None
    if workspace_paths:
        try:
            ws_root = Path(workspace_paths[0]).resolve()
        except Exception:
            ws_root = None
    if ws_root is None:
        ws_root = Path.cwd().resolve()

    base_dir = Path(cwd).resolve() if cwd and os.path.isabs(cwd) else ws_root

    for raw_p in paths:
        if "\0" in raw_p:
            return f"[CEH PATH SAFETY] Caractere nulo detectado no caminho '{raw_p}'."

        clean = raw_p.replace("\\", "/").strip("'\"")

        # 1. Proteção de certificados de CI e pasta .ceh/
        if any(sig in clean.lower() for sig in ("last-ci-run.json", "last-ci-run.log", "last-evals-run.json")):
            return f"[CEH CERTIFICATE INTEGRITY - G9] ⛔ Tentativa de escrita/modificação de certificado de CI ({clean}). Arquivos sob .ceh/ são imutáveis."
        if re.search(r"(?:^|/)\.ceh(?:/|$)", clean, re.IGNORECASE):
            return f"[CEH CERTIFICATE INTEGRITY - G9] ⛔ Modificação em arquivos sob .ceh/ ({clean}) bloqueada por governança de CI."

        # 2. Proteção de estruturas internas do Git (.git/)
        if re.search(r"(?:^|/)\.git(?:/|$)", clean, re.IGNORECASE):
            return f"[CEH GIT PROTECTION] ⛔ Modificação direta em estruturas de versionamento Git (.git/) bloqueada ({clean})."

        # 3. Resolução no filesystem e confinamento
        try:
            p_obj = Path(clean)
            if not p_obj.is_absolute():
                resolved = (base_dir / p_obj).resolve()
            else:
                resolved = p_obj.resolve()

            resolved_str = str(resolved)

            # Bloqueio de diretórios de sistema críticos
            if any(resolved_str.startswith(d) for d in ("/etc", "/root", "/boot", "/sys", "/proc", "/bin", "/sbin", "/usr")):
                return f"[CEH WORKSPACE CONFINEMENT] ⛔ Tentativa de modificação em diretório restrito do sistema ({resolved_str})."

            # Confinamento ao workspace: se escapar do workspace e não estiver em /tmp
            if ws_root is not None:
                ws_str = str(ws_root)
                if not resolved_str.startswith(ws_str) and not resolved_str.startswith("/tmp"):
                    return f"[CEH WORKSPACE CONFINEMENT] ⛔ Tentativa de escrita fora dos limites do workspace ({raw_p} -> {resolved_str})."
        except Exception as pe:
            return f"[CEH PATH SAFETY] Erro na resolução canônica do caminho '{raw_p}': {pe}"

    return None


def inspect_command_safety(command_str: str, language: Optional[str] = None) -> Optional[str]:
    """
    Inspeção estática poliglota de comandos e código para PreToolUse:
      1. Varredura contra HARD_BLOCK_PATTERNS (catastróficos, migrate:fresh, db:wipe, DROP DATABASE).
      2. Varredura de chamadas de SO de linguagens de script (Python, Node/JS, PHP) se language != shell.
      3. Verificação contra Scoped Execution Guard (find / irrestrito).
    Retorna mensagem de motivo de bloqueio ou None se seguro.
    """
    cmd_clean = command_str.strip()
    if not cmd_clean:
        return None

    # 1. Checagem de padrões catastróficos imediatos na string bruta
    for pattern, reason in HARD_BLOCK_PATTERNS:
        if re.search(pattern, cmd_clean, re.IGNORECASE):
            return f"[GUARDRAIL BLOQUEOU]: {reason}\nComando/Código rejeitado: '{cmd_clean[:100]}'"

    # 2. Se for código em linguagens de script (Python, Node, PHP), inspecionar chamadas de SO
    lang = (language or "shell").lower()
    if lang in ("python", "py"):
        # Detecta chamadas a subprocessos executando comandos destrutivos
        py_os_calls = re.findall(r"(?:os\.system|subprocess\.(?:run|call|Popen|check_output)|shutil\.rmtree)\s*\(([^)]+)\)", cmd_clean)
        for call_arg in py_os_calls:
            unquoted = call_arg.strip(" '\"\t\r\n")
            for pattern, reason in HARD_BLOCK_PATTERNS:
                if re.search(pattern, unquoted, re.IGNORECASE) or re.search(pattern, call_arg, re.IGNORECASE):
                    return f"[CEH MCP SECURITY]: Execução destrutiva embutida em Python bloqueada: {reason}"
    elif lang in ("javascript", "typescript", "js", "ts"):
        # Detecta chamadas a child_process executando comandos destrutivos
        js_os_calls = re.findall(r"(?:execSync|exec|spawn|spawnSync)\s*\(([^)]+)\)", cmd_clean)
        for call_arg in js_os_calls:
            unquoted = call_arg.strip(" '\"\t\r\n")
            for pattern, reason in HARD_BLOCK_PATTERNS:
                if re.search(pattern, unquoted, re.IGNORECASE) or re.search(pattern, call_arg, re.IGNORECASE):
                    return f"[CEH MCP SECURITY]: Execução destrutiva embutida em Node/JS bloqueada: {reason}"

    # 3. Verificação de varreduras não delimitadas via Scoped Execution Guard
    if _SCOPED_GUARD_AVAILABLE:
        if check_unbounded_scan(cmd_clean):
            return "[OPT-002 SCOPED EXECUTION] Varredura recursiva não delimitada bloqueada. Especifique um subdiretório do projeto ou utilize '-maxdepth 3' para evitar sobrecarga de I/O."

    return None


def evaluate_all(raw_input: str) -> Tuple[Optional[Dict[str, Any]], int]:
    """
    Ponto de entrada unificado para avaliação PreToolUse com arquitetura P0:
      1. Normalização universal e validação de schema (fail-closed).
      2. Confinamento de caminhos e integridade de certificados/Git.
      3. Avaliação de segurança (CEH Safety Gate + Scoped Guard).
      4. Roteamento de contexto delimitado vs context-mode com timeout estrito.
    """
    normalized, err = normalize_payload(raw_input)
    if err is not None:
        return err

    assert normalized is not None

    # Operação de wipe destrutivo em ctx_purge
    if normalized.is_purge_destructive:
        return _make_deny("[CEH DATA INTEGRITY] ctx_purge com scope 'project' apagaria a base de dados do projeto. Operação proibida por guardrail de governança.")

    # Confinamento de arquivos (se houver alvos de path)
    if normalized.target_paths:
        path_err = validate_path_confinement(normalized.target_paths, normalized.cwd, normalized.workspace_paths)
        if path_err:
            return _make_deny(path_err)

    # Avaliação de comandos e código
    for cmd in normalized.commands:
        sec_err = inspect_command_safety(cmd, normalized.language)
        if sec_err:
            return _make_deny(sec_err)

    # Elo 1: CEH Safety Gate para run_command e ferramentas de escrita
    if _SAFETY_GATE_AVAILABLE and normalized.canonical_name in ("run_command", "write_file", "edit_file", "write_to_file", "replace_file_content", "multi_replace_file_content"):
        try:
            # Normalização de compatibilidade com o AntigravityAdapter:
            # Mapeia write_file/edit_file para write_to_file com TargetFile para suportar qualquer versão de runtime
            adapter_tool_name = "write_to_file" if normalized.canonical_name in ("write_file", "edit_file") else normalized.canonical_name
            adapter_args = dict(normalized.original_args)
            if normalized.target_paths and "TargetFile" not in adapter_args:
                adapter_args["TargetFile"] = normalized.target_paths[0]

            adapter_payload = {
                "session_id": "hooks-dispatcher-p0",
                "hook_event_name": "PreToolUse",
                "workspacePaths": normalized.workspace_paths,
                "toolCall": {
                    "name": adapter_tool_name,
                    "args": adapter_args
                }
            }
            resp_dict, exit_code = handle_hook_lifecycle(json.dumps(adapter_payload), evaluate_ceh)
            dec = resp_dict.get("decision", "allow")
            if dec in ("deny", "ask"):
                # Antigravity exige exit code 0 para processar o JSON de negação
                return resp_dict, 0
        except Exception as e:
            return _make_deny(f"[CEH SAFETY GATE ERROR] Exceção na validação de governança ({e}). Execução bloqueada (fail-closed).")

    # Elo 3: Smart Advisory Router (apenas para run_command)
    if _ADVISORY_ROUTER_AVAILABLE and normalized.canonical_name == "run_command":
        cmd_to_route = normalized.commands[0] if normalized.commands else ""
        if is_deliberately_bounded(cmd_to_route):
            return None, 0

        # Delegação ao context-mode com timeout estrito de 250ms
        try:
            proc = subprocess.run(
                ["context-mode", "hook", "antigravity-cli", "pretooluse"],
                input=raw_input,
                capture_output=True,
                text=True,
                timeout=0.25
            )
            if proc.stdout and proc.stdout.strip():
                try:
                    cm_dict = json.loads(proc.stdout)
                    return cm_dict, 0
                except Exception:
                    pass
        except Exception:
            # Falha de timeout ou ausência do context-mode: não bloqueia (advisory non-blocking)
            return None, 0

    # Todas as salvaguardas passaram: libera execução
    return None, 0


def main():
    try:
        raw_input = sys.stdin.read()
    except Exception:
        raw_input = ""

    resp_dict, exit_code = evaluate_all(raw_input)
    if resp_dict is not None:
        sys.stdout.write(json.dumps(resp_dict, ensure_ascii=False))
        sys.exit(exit_code)
    else:
        # Permissão silenciosa normal (exit 0)
        sys.exit(0)


if __name__ == "__main__":
    main()
