#!/usr/bin/env python3
"""
OPT-004: Utilitário Parametrizado de Auditoria de Git de Baixo Overhead
Antigravity Engineering Lab

Permite extrair status, histórico, commits, diffs e arquivos modificados com custo
mínimo de tokens de saída para LLMs, dispensando a escrita de scripts ad-hoc.

Compatível com:
  - Modo legado posicional: git_inspect.py <repo> [--limit 15] [--target HASH] [--grep PAT]
  - Subcomandos documentados:
      git_inspect.py status [--repo .]
      git_inspect.py log [--repo .] [--max-count 15 | --limit 15] [--target HASH] [--grep PAT] [--stat]
      git_inspect.py diff [--repo .] [--target HEAD~1] [--stat]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Any, Dict, List, Optional

SUBCOMMANDS = ("status", "log", "diff")
DEFAULT_TIMEOUT_SEC = 15


def _run_git(repo_path: str, git_args: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", repo_path, *git_args],
        capture_output=True,
        text=True,
        timeout=DEFAULT_TIMEOUT_SEC,
    )


def inspect_commits(
    repo_path: str,
    limit: int = 15,
    target_hash: Optional[str] = None,
    search_pattern: Optional[str] = None,
    include_stat: bool = False,
) -> Dict[str, Any]:
    cmd = [
        "log", f"-n{limit}",
        "--pretty=format:%h|%an|%ad|%s",
        "--date=short",
    ]
    if search_pattern:
        cmd.extend(["--grep", search_pattern])

    res = _run_git(repo_path, cmd)
    if res.returncode != 0:
        return {"error": res.stderr.strip()}

    commits = []
    for line in res.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("|", 3)
        if len(parts) == 4:
            commits.append({
                "hash": parts[0],
                "author": parts[1],
                "date": parts[2],
                "subject": parts[3],
            })

    files_modified = []
    if target_hash:
        f_res = _run_git(repo_path, ["show", "--name-only", "--pretty=format:", target_hash])
        if f_res.returncode == 0:
            files_modified = [f for f in f_res.stdout.strip().split("\n") if f]

    out: Dict[str, Any] = {
        "repo": repo_path,
        "total_commits": len(commits),
        "commits": commits,
        "target_commit_files": files_modified,
    }
    if include_stat:
        stat_cmd = ["log", f"-n{limit}", "--stat", "--oneline"]
        if search_pattern:
            stat_cmd.extend(["--grep", search_pattern])
        s_res = _run_git(repo_path, stat_cmd)
        out["stat_summary"] = s_res.stdout.strip() if s_res.returncode == 0 else s_res.stderr.strip()
    return out


def inspect_status(repo_path: str) -> Dict[str, Any]:
    res = _run_git(repo_path, ["status", "--short", "-b"])
    if res.returncode != 0:
        return {"error": res.stderr.strip()}

    lines = [l for l in res.stdout.splitlines() if l.strip()]
    branch = ""
    entries: List[Dict[str, str]] = []
    for line in lines:
        if line.startswith("## "):
            branch = line[3:].strip()
        else:
            code = line[:2].strip() or "M"
            path = line[3:].strip()
            entries.append({"status": code, "path": path})

    return {
        "repo": repo_path,
        "branch": branch,
        "modified_count": len(entries),
        "entries": entries,
    }


def inspect_diff(repo_path: str, target: str = "HEAD~1") -> Dict[str, Any]:
    num_res = _run_git(repo_path, ["diff", "--numstat", target])
    if num_res.returncode != 0:
        return {"error": num_res.stderr.strip()}

    files: List[Dict[str, Any]] = []
    for line in num_res.stdout.splitlines():
        parts = line.split("\t", 2)
        if len(parts) == 3:
            added = int(parts[0]) if parts[0].isdigit() else None
            deleted = int(parts[1]) if parts[1].isdigit() else None
            files.append({"path": parts[2], "added": added, "deleted": deleted})

    stat_res = _run_git(repo_path, ["diff", "--stat", target])
    stat_summary = stat_res.stdout.strip() if stat_res.returncode == 0 else ""

    return {
        "repo": repo_path,
        "target": target,
        "files_changed": len(files),
        "files": files,
        "stat_summary": stat_summary,
    }


def main(argv: Optional[List[str]] = None) -> int:
    raw_argv = sys.argv[1:] if argv is None else argv

    if raw_argv and raw_argv[0] in SUBCOMMANDS:
        subcmd = raw_argv[0]
        parser = argparse.ArgumentParser(description=f"Auditoria rápida de Git ({subcmd})")
        parser.add_argument("--repo", default=".", help="Caminho do repositório (default: .)")
        parser.add_argument("--limit", "--max-count", dest="limit", type=int, default=15, help="Quantidade de commits")
        parser.add_argument("--target", default="HEAD~1" if subcmd == "diff" else None, help="Commit/ref alvo")
        parser.add_argument("--grep", default=None, help="Padrão de busca na mensagem")
        parser.add_argument("--stat", action="store_true", help="Incluir resumo --stat")
        args = parser.parse_args(raw_argv[1:])

        if subcmd == "status":
            data = inspect_status(args.repo)
        elif subcmd == "diff":
            data = inspect_diff(args.repo, args.target or "HEAD~1")
        else:
            data = inspect_commits(args.repo, args.limit, args.target, args.grep, include_stat=args.stat)
    else:
        parser = argparse.ArgumentParser(description="Auditoria rápida de Git")
        parser.add_argument("repo", help="Caminho do repositório")
        parser.add_argument("--limit", "--max-count", dest="limit", type=int, default=15, help="Quantidade de commits")
        parser.add_argument("--target", default=None, help="Commit hash específico")
        parser.add_argument("--grep", default=None, help="Padrão de busca na mensagem")
        args = parser.parse_args(raw_argv)
        data = inspect_commits(args.repo, args.limit, args.target, args.grep)

    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 1 if "error" in data else 0


if __name__ == "__main__":
    sys.exit(main())

