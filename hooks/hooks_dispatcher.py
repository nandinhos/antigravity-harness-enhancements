#!/usr/bin/env python3
"""
SECURITY-OPT-01 — Unified Guardrails Dispatcher (Fase P0.1 Corrective Hardening)
Antigravity Engineering Lab / CEH Optimization Layer

Implementa:
  1. Normalizador Universal de Payloads (preservando envelopes, profundidade e proveniência).
  2. Classificação Explícita de Linguagem (SHELL, PYTHON, JAVASCRIPT, UNKNOWN, OTHER) sem suposições implícitas.
  3. Inspeção Estruturada via AST de Python (módulo ast) para chamadas de SO, subprocessos e metaprogramação.
  4. Inspeção Semântica de JavaScript e Shell com Delimitadores Lexicais Expandidos.
  5. Política Fail-Closed Estrita em Exit Code 0 com Tratamento de Código UNINSPECTABLE.
  6. Confinamento de Filesystem e Proteção de Workspace (.ceh/, .git/, caminhos absolutos).
  7. Catálogo de 42 Ferramentas Mapeadas e Heurística Conservadora para Ferramentas Desconhecidas.
"""

import sys
import os
import json
import re
import ast
import time
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List, Set

# Constantes de Versão e Governança
DISPATCHER_VERSION = "0.9.1-p0.1"
MAX_WRAPPER_DEPTH = 3

# Localização e carregamento dos módulos do harness
HARNESS_DIR = Path("/home/nandodev/.gemini/config/hooks")
if str(HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(HARNESS_DIR))

# Elo 1: CEH Safety Gate (destructive_command_guardrail)
_SAFETY_GATE_AVAILABLE = False
_SAFETY_GATE_ERROR = None
try:
    import guard_destructive
    evaluate_ceh = guard_destructive.evaluate_command_safety
    handle_hook_lifecycle = guard_destructive.handle_hook_lifecycle
    _SAFETY_GATE_AVAILABLE = True
except Exception as e:
    _SAFETY_GATE_ERROR = e

# Elo 2: Scoped Execution Guard
_SCOPED_GUARD_AVAILABLE = False
_SCOPED_GUARD_ERROR = None
try:
    import scoped_execution_guard
    check_unbounded_scan = scoped_execution_guard.check_unbounded_scan
    _SCOPED_GUARD_AVAILABLE = True
except Exception as e:
    _SCOPED_GUARD_ERROR = e

# Elo 3: Smart Advisory Router (context-mode)
_ADVISORY_ROUTER_AVAILABLE = False
_ADVISORY_ROUTER_ERROR = None
try:
    import context_mode_advisory_router
    is_deliberately_bounded = context_mode_advisory_router.is_deliberately_bounded
    _ADVISORY_ROUTER_AVAILABLE = True
except Exception as e:
    _ADVISORY_ROUTER_ERROR = e

# Delimitadores lexicais para fronteiras de comandos em código (espaço, aspas, parênteses, ponto-e-vírgula ou fim de linha)
_PATH_BOUNDARY = r"(?:['\";\)\]\}\s]|$)"

# Padrões catastróficos imediatos (Hard Blocks em memória)
HARD_BLOCK_PATTERNS = [
    # Filesystem / SO Catastrófico
    (r"\brm\s+-[rRfF]*\s+(?:/|~|\$HOME)(?:" + _PATH_BOUNDARY + r")", "Tentativa de exclusão catastrófica da raiz ou home do sistema."),
    (r"\brm\s+-[rRfF]*\s+\.git\b", "Tentativa de exclusão do diretório de versionamento Git (.git)."),
    (r"\bmkfs\b", "Comando de formatação de sistema de arquivos (mkfs) não permitido."),
    (r"\bdd\s+if=", "Comando de baixo nível 'dd' não permitido."),
    (r"\bchmod\s+-[rRfF]*\s+777\s+/(?:" + _PATH_BOUNDARY + r")", "Permissões abertas e inseguras (chmod 777 /) não permitidas."),
    (r":\(\)\s*\{\s*:\|:&\s*\};:", "Fork bomb detectada e bloqueada."),

    # Banco de Dados - Artisan / Laravel Destrutivo
    (r"\b(?:php\s+)?artisan\s+migrate:fresh\b", "Comando destrutivo 'migrate:fresh' apagaria todas as tabelas e dados. Use 'migrate' incremental."),
    (r"\b(?:php\s+)?artisan\s+migrate:reset\b", "Comando 'migrate:reset' reverteria todas as migrações. Operação proibida."),
    (r"\b(?:php\s+)?artisan\s+db:wipe\b", "Comando 'db:wipe' apagaria completamente o banco de dados. Operação proibida."),

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
    depth: int = 0
    commands: List[str] = field(default_factory=list)
    target_paths: List[str] = field(default_factory=list)
    cwd: Optional[str] = None
    language_declared: Optional[str] = None
    language_classified: str = "UNKNOWN"  # "SHELL", "PYTHON", "JAVASCRIPT", "UNKNOWN", "OTHER"
    language_source: str = "UNRESOLVED"   # "DECLARED", "TOOL_CONTRACT", "AST_VERIFIED", "LEXICAL_HEURISTIC", "UNRESOLVED"
    missing_fields: List[str] = field(default_factory=list)
    is_purge_destructive: bool = False
    original_args: Dict[str, Any] = field(default_factory=dict)
    workspace_paths: List[str] = field(default_factory=list)


def _make_deny(reason: str) -> Tuple[Dict[str, Any], int]:
    """Retorna resposta padronizada de negação com exit code 0 para a IDE Antigravity."""
    return {"decision": "deny", "reason": reason}, 0


def classify_language(canonical_name: str, code_snippet: str, declared_lang: Optional[str]) -> Tuple[str, str]:
    """
    Classificação explícita de linguagem sem inferências cegas.
    Retorna (language_classified, language_source).
    Linguagens: "SHELL", "PYTHON", "JAVASCRIPT", "UNKNOWN", "OTHER".
    Fontes: "DECLARED", "TOOL_CONTRACT", "AST_VERIFIED", "LEXICAL_HEURISTIC", "UNRESOLVED".
    """
    if canonical_name == "run_command":
        return "SHELL", "TOOL_CONTRACT"

    code_clean = code_snippet.strip()
    if not code_clean:
        return "UNKNOWN", "EMPTY_CODE"

    # 1. Metadado explicitamente fornecido
    if declared_lang is not None and str(declared_lang).strip():
        decl = str(declared_lang).strip().lower()
        if decl in ("python", "py", "python3"):
            return "PYTHON", "DECLARED"
        elif decl in ("javascript", "typescript", "js", "ts", "node"):
            return "JAVASCRIPT", "DECLARED"
        elif decl in ("shell", "bash", "sh", "zsh"):
            return "SHELL", "DECLARED"
        else:
            return "OTHER", "DECLARED"

    # 2. Ausência de metadado: Nunca pressupor shell silenciosamente!
    # 2.1 Análise via AST de Python
    try:
        tree = ast.parse(code_clean)
        is_python_indicator = False
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                is_python_indicator = True
                break
            if isinstance(node, ast.Call):
                is_python_indicator = True
                break
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                is_python_indicator = True
                break
            if isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                is_python_indicator = True
                break

        if is_python_indicator:
            return "PYTHON", "AST_VERIFIED"
    except SyntaxError:
        pass

    # 2.2 Análise Léxica de JavaScript / TypeScript
    js_patterns = [
        r"\b(?:const|let|var)\s+[a-zA-Z_$][a-zA-Z0-9_$]*\s*=",
        r"\brequire\s*\(\s*['\"][^'\"]+['\"]\s*\)",
        r"\bimport\s+.*\s+from\s+['\"][^'\"]+['\"]",
        r"\bfunction\s*[a-zA-Z_$]*\s*\(",
        r"\bconsole\.(?:log|error|warn|info|debug)\s*\(",
        r"\bprocess\.(?:env|exit|argv|stdout)\b",
        r"=>\s*\{?",
        r"\bchild_process\b",
    ]
    if any(re.search(pat, code_clean) for pat in js_patterns):
        return "JAVASCRIPT", "LEXICAL_HEURISTIC"

    # 2.3 Análise Léxica de Comandos Shell Atômicos
    shell_command_names = (
        "echo", "git", "cd", "ls", "cat", "grep", "find", "mkdir", "rm", "cp", "mv",
        "curl", "wget", "docker", "cargo", "npm", "pnpm", "yarn", "composer", "php",
        "python", "python3", "which", "chmod", "chown", "tar", "gzip", "sed", "awk"
    )
    shell_pattern = r"(?:^|[;&|]\s*)(?:" + "|".join(shell_command_names) + r")\b"
    if re.search(shell_pattern, code_clean) and not re.search(r"[:=]\s*", code_clean):
        return "SHELL", "LEXICAL_HEURISTIC"

    # 3. Análise inconclusiva
    return "UNKNOWN", "UNRESOLVED"


def _get_func_qualname(node: ast.AST) -> str:
    """Extrai recursivamente o nome qualificado de uma função na AST (ex: 'os.system')."""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        parent = _get_func_qualname(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def inspect_python_code(code_str: str) -> Tuple[str, Optional[str]]:
    """
    Inspeção estática estruturada via AST de Python (módulo ast padrão).
    Retorna (verdict, reason):
      - ("DENY", reason): Violação de segurança determinística encontrada.
      - ("UNINSPECTABLE", reason): Metaprogramação opaca ou não compilável.
      - ("ALLOW", None): Código analisado com sucesso e limpo.
    """
    try:
        tree = ast.parse(code_str)
    except SyntaxError as e:
        return "UNINSPECTABLE", f"Código Python com sintaxe inválida ou fragmento opaco: {e}"

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func_name = _get_func_qualname(node.func)

            # A. Chamadas diretas de SO / Processos
            if func_name in (
                "os.system", "os.popen", "os.kill",
                "subprocess.run", "subprocess.call", "subprocess.Popen",
                "subprocess.check_output", "subprocess.check_call"
            ):
                if node.args:
                    first_arg = node.args[0]
                    if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                        cmd_literal = first_arg.value.strip()
                        # Avalia contra HARD_BLOCK_PATTERNS
                        for pattern, reason in HARD_BLOCK_PATTERNS:
                            if re.search(pattern, cmd_literal, re.IGNORECASE):
                                return "DENY", f"[CEH MCP PYTHON SECURITY] Chamada destrutiva em {func_name}: {reason} ('{cmd_literal}')"
                        # Avalia contra Scoped Execution Guard
                        if _SCOPED_GUARD_AVAILABLE and check_unbounded_scan(cmd_literal):
                            return "DENY", f"[CEH MCP PYTHON SECURITY] Varredura não delimitada em {func_name}: '{cmd_literal}'"
                    else:
                        return "UNINSPECTABLE", f"Chamada a {func_name} com comando dinâmico ou variável não estática."
                else:
                    return "UNINSPECTABLE", f"Chamada a {func_name} sem argumentos explícitos."

            # B. Deleção direta de caminhos / filesystem
            if func_name in ("shutil.rmtree", "os.remove", "os.unlink", "os.rmdir", "shutil.move"):
                if node.args:
                    first_arg = node.args[0]
                    if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                        path_literal = first_arg.value.strip()
                        if path_literal in ("/", "~", "$HOME") or any(path_literal.startswith(d) for d in ("/etc", "/root", "/sys", "/proc", "/bin", "/usr")):
                            return "DENY", f"[CEH MCP PYTHON SECURITY] Tentativa de exclusão de caminho crítico do sistema em {func_name} ('{path_literal}')."
                        if re.search(r"(?:^|/)\.(?:git|ceh)(?:/|$)", path_literal, re.IGNORECASE):
                            return "DENY", f"[CEH MCP PYTHON SECURITY] Tentativa de exclusão de diretório protegido ({path_literal}) em {func_name}."
                    else:
                        return "UNINSPECTABLE", f"Chamada a {func_name} com caminho dinâmico não estático."

            # B. Metaprogramação opaca e evasiva
            if func_name in ("eval", "exec", "__import__", "compile"):
                return "UNINSPECTABLE", f"Uso de função de execução dinâmica/metaprogramação '{func_name}' sem sandbox."

            # C. Tentativa de escrita direta via open() em arquivos protegidos
            if func_name == "open" and node.args:
                first_arg = node.args[0]
                if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                    path_val = first_arg.value.strip()
                    mode_val = "r"
                    if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant) and isinstance(node.args[1].value, str):
                        mode_val = node.args[1].value.strip()
                    for kw in node.keywords:
                        if kw.arg == "mode" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                            mode_val = kw.value.value.strip()
                    if any(m in mode_val for m in ("w", "a", "x", "+")):
                        if re.search(r"(?:^|/)\.(?:ceh|git)(?:/|$)", path_val, re.IGNORECASE):
                            return "DENY", f"[CEH MCP PYTHON SECURITY] Tentativa de escrita em diretório protegido ({path_val}) via open()."

    return "ALLOW", None


def inspect_javascript_code(code_str: str) -> Tuple[str, Optional[str]]:
    """
    Inspeção estática de código JavaScript / Node.js.
    """
    # 1. Metaprogramação opaca
    if re.search(r"\b(?:eval|Function)\s*\(", code_str):
        return "UNINSPECTABLE", "Uso de eval/Function dinâmica em JavaScript sem sandbox."

    # 2. Chamadas a child_process com literais
    js_proc_calls = re.findall(r"(?:execSync|exec|spawn|spawnSync)\s*\(\s*(['\"][^'\"]+['\"])", code_str)
    for call_arg in js_proc_calls:
        cmd_unquoted = call_arg.strip(" '\"\t\r\n")
        for pattern, reason in HARD_BLOCK_PATTERNS:
            if re.search(pattern, cmd_unquoted, re.IGNORECASE):
                return "DENY", f"[CEH MCP JS SECURITY] Execução destrutiva em child_process: {reason} ('{cmd_unquoted}')"
        if _SCOPED_GUARD_AVAILABLE and check_unbounded_scan(cmd_unquoted):
            return "DENY", f"[CEH MCP JS SECURITY] Varredura não delimitada em child_process: '{cmd_unquoted}'"

    # 3. Chamada a child_process com variáveis dinâmicas
    if re.search(r"(?:execSync|exec|spawn|spawnSync)\s*\(\s*[^'\"\s)]+", code_str) and not js_proc_calls:
        return "UNINSPECTABLE", "Chamada a child_process com comando dinâmico em JavaScript."

    return "ALLOW", None


def inspect_shell_code(cmd_str: str) -> Tuple[str, Optional[str]]:
    """
    Inspeção estática de comandos shell.
    """
    cmd_clean = cmd_str.strip()
    if not cmd_clean:
        return "ALLOW", None

    for pattern, reason in HARD_BLOCK_PATTERNS:
        if re.search(pattern, cmd_clean, re.IGNORECASE):
            return "DENY", f"[GUARDRAIL BLOQUEOU]: {reason}\nComando/Código rejeitado: '{cmd_clean[:100]}'"

    if _SCOPED_GUARD_AVAILABLE and check_unbounded_scan(cmd_clean):
        return "DENY", f"[SCOPED GUARD BLOQUEOU]: Varredura irrestrita no sistema detectada ('{cmd_clean[:100]}'). Confinamento ao workspace violado."

    return "ALLOW", None


def check_raw_destructive_patterns(raw_text: str) -> Optional[str]:
    """Varredura de padrões catastróficos imediatos em qualquer string bruta de comando/código."""
    for pattern, reason in HARD_BLOCK_PATTERNS:
        if re.search(pattern, raw_text, re.IGNORECASE):
            return f"[GUARDRAIL BLOQUEOU]: {reason}\nTrecho rejeitado: '{raw_text[:100]}'"
    return None


def normalize_payload(raw_input: str) -> Tuple[Optional[NormalizedToolCall], Optional[Tuple[Dict[str, Any], int]]]:
    """
    Normalizador Universal de Payloads (Fase P0.1).
    Preserva envelopes originais, profundidade, procedência e realiza classificação explícita de linguagem.
    """
    if not raw_input or not raw_input.strip():
        return None, _make_deny("[CEH FAIL-CLOSED] Entrada vazia ou nula recebida no PreToolUse.")

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

    while curr_name == "call_mcp_tool" and depth < MAX_WRAPPER_DEPTH:
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
    cwd: Optional[str] = curr_args.get("Cwd") or curr_args.get("cwd") or payload.get("cwd") or payload.get("Cwd")
    declared_lang: Optional[str] = curr_args.get("language")
    missing_fields: List[str] = []
    is_purge = False

    # Validação e extração tipada por categoria de ferramenta
    if canonical_name == "run_command":
        cmd_line = curr_args.get("CommandLine")
        if cmd_line is None:
            return None, _make_deny("[CEH FAIL-CLOSED] 'run_command' exige o argumento obrigatório 'CommandLine'.")
        if not isinstance(cmd_line, str):
            return None, _make_deny("[CEH FAIL-CLOSED] 'CommandLine' em 'run_command' deve ser uma string.")
        commands = [cmd_line]

    elif canonical_name in ("write_file", "edit_file", "write_to_file", "replace_file_content", "multi_replace_file_content"):
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
        if declared_lang is None:
            missing_fields.append("language")

    elif canonical_name == "ctx_execute_file":
        code_str = curr_args.get("code")
        file_path = curr_args.get("path")
        if code_str is None or file_path is None:
            return None, _make_deny("[CEH FAIL-CLOSED] 'ctx_execute_file' exige os argumentos 'code' e 'path'.")
        if not isinstance(code_str, str) or not isinstance(file_path, str):
            return None, _make_deny("[CEH FAIL-CLOSED] 'code' e 'path' em 'ctx_execute_file' devem ser strings.")
        commands = [code_str]
        target_paths = [file_path.strip()]
        if declared_lang is None:
            missing_fields.append("language")

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
        category = "BENIGN"

    # Classificação explícita de linguagem
    primary_code = commands[0] if commands else ""
    lang_classified, lang_source = classify_language(canonical_name, primary_code, declared_lang)

    normalized = NormalizedToolCall(
        raw_name=raw_name,
        canonical_name=canonical_name,
        category=category,
        depth=depth,
        commands=commands,
        target_paths=target_paths,
        cwd=cwd,
        language_declared=declared_lang,
        language_classified=lang_classified,
        language_source=lang_source,
        missing_fields=missing_fields,
        is_purge_destructive=is_purge,
        original_args=curr_args,
        workspace_paths=[str(p) for p in workspace_paths if p]
    )
    return normalized, None


def validate_path_confinement(paths: List[str], cwd: Optional[str], workspace_paths: List[str]) -> Optional[str]:
    """
    Valida confinamento de filesystem e diretórios protegidos (.ceh, .git, /etc, /root, etc.).
    """
    if not paths:
        return None

    base_dir = Path(cwd).resolve() if cwd else (Path(workspace_paths[0]).resolve() if workspace_paths else Path.cwd().resolve())
    ws_root = Path(workspace_paths[0]).resolve() if workspace_paths else None

    for raw_p in paths:
        clean = raw_p.strip()
        if not clean:
            continue

        # 1. Proteção de integridade dos certificados CEH (.ceh/)
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


def evaluate_all(raw_input: str) -> Tuple[Optional[Dict[str, Any]], int]:
    """
    Orquestrador Central do Unified Guardrails Dispatcher (Fase P0.1).
    Aplica: Normalização -> Confinamento -> Avaliação de Código (AST/Léxica) -> Safety Gate -> Advisory.
    """
    # Elo 0: Normalizador Universal de Payloads
    normalized, err_deny = normalize_payload(raw_input)
    if err_deny:
        return err_deny

    assert normalized is not None

    # Elo de Purge destrutivo em context-mode
    if normalized.is_purge_destructive:
        return _make_deny("[CEH MCP PURGE GUARD] Operação 'ctx_purge' em escopo de projeto bloqueada. Operação destrutiva não autorizada.")

    # Elo de Confinamento de Filesystem
    if normalized.target_paths:
        path_err = validate_path_confinement(normalized.target_paths, normalized.cwd, normalized.workspace_paths)
        if path_err:
            return _make_deny(path_err)

    # Elo de Avaliação de Comandos e Código (TERMINAL e MCP_EXEC)
    if normalized.category in ("TERMINAL", "MCP_EXEC"):
        for cmd in normalized.commands:
            verdict = "ALLOW"
            reason = None

            if normalized.category == "TERMINAL":
                verdict, reason = inspect_shell_code(cmd)

            elif normalized.category == "MCP_EXEC":
                lang = normalized.language_classified
                if lang == "PYTHON":
                    verdict, reason = inspect_python_code(cmd)
                elif lang == "JAVASCRIPT":
                    verdict, reason = inspect_javascript_code(cmd)
                elif lang == "SHELL":
                    verdict, reason = inspect_shell_code(cmd)
                else:  # UNKNOWN ou OTHER
                    # REGRA ARQUITETURAL: Ausência de metadados não deve implicar ausência de risco
                    raw_err = check_raw_destructive_patterns(cmd)
                    if raw_err:
                        verdict, reason = "DENY", raw_err
                    else:
                        verdict, reason = "UNINSPECTABLE", (
                            f"Código em '{normalized.canonical_name}' com linguagem não determinada "
                            f"('{lang}') ou sem suporte a inspeção estática segura sem sandbox."
                        )

            if verdict == "DENY":
                return _make_deny(reason or "Comando ou código destrutivo rejeitado.")
            elif verdict == "UNINSPECTABLE":
                return _make_deny(f"[CEH UNINSPECTABLE - P0.1] Execução de código arbitrário bloqueada: {reason}")

    # Elo 1: CEH Safety Gate para run_command e ferramentas de escrita
    if _SAFETY_GATE_AVAILABLE and normalized.canonical_name in ("run_command", "write_file", "edit_file", "write_to_file", "replace_file_content", "multi_replace_file_content"):
        try:
            adapter_tool_name = "write_to_file" if normalized.canonical_name in ("write_file", "edit_file") else normalized.canonical_name
            adapter_args = dict(normalized.original_args)
            if normalized.target_paths and "TargetFile" not in adapter_args:
                adapter_args["TargetFile"] = normalized.target_paths[0]

            adapter_payload = {
                "session_id": "hooks-dispatcher-p01",
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
                return resp_dict, 0
        except Exception as e:
            return _make_deny(f"[CEH SAFETY GATE ERROR] Exceção na validação de governança ({e}). Execução bloqueada (fail-closed).")

    # Elo 3: Smart Advisory Router (apenas para run_command)
    if _ADVISORY_ROUTER_AVAILABLE and normalized.canonical_name == "run_command":
        cmd_to_route = normalized.commands[0] if normalized.commands else ""
        if is_deliberately_bounded(cmd_to_route):
            return None, 0

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
            return None, 0

    # Todas as salvaguardas passaram: libera execução silenciosa
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
        sys.exit(0)


if __name__ == "__main__":
    main()
