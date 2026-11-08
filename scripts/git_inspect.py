#!/usr/bin/env python3
"""
OPT-004: Utilitário Parametrizado de Auditoria de Git de Baixo Overhead
Antigravity Engineering Lab

Permite extrair histórico, commits, diffs e arquivos modificados com custo
mínimo de tokens de saída para LLMs, dispensando a escrita de scripts ad-hoc.
"""
import sys
import subprocess
import json
import argparse

def inspect_commits(repo_path, limit=15, target_hash=None, search_pattern=None):
    cmd = [
        "git", "-C", repo_path, "log", f"-n{limit}",
        "--pretty=format:%h|%an|%ad|%s",
        "--date=short"
    ]
    if search_pattern:
        cmd.extend(["--grep", search_pattern])

    res = subprocess.run(cmd, capture_output=True, text=True)
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
                "subject": parts[3]
            })

    # Obter arquivos modificados no commit alvo se especificado
    files_modified = []
    if target_hash:
        f_cmd = ["git", "-C", repo_path, "show", "--name-only", "--pretty=format:", target_hash]
        f_res = subprocess.run(f_cmd, capture_output=True, text=True)
        if f_res.returncode == 0:
            files_modified = [f for f in f_res.stdout.strip().split("\n") if f]

    return {
        "repo": repo_path,
        "total_commits": len(commits),
        "commits": commits,
        "target_commit_files": files_modified
    }

def main():
    parser = argparse.ArgumentParser(description="Auditoria rápida de Git")
    parser.add_argument("repo", help="Caminho do repositório")
    parser.add_argument("--limit", type=int, default=15, help="Quantidade de commits")
    parser.add_argument("--target", default=None, help="Commit hash específico")
    parser.add_argument("--grep", default=None, help="Padrão de busca na mensagem")
    args = parser.parse_args()

    data = inspect_commits(args.repo, args.limit, args.target, args.grep)
    print(json.dumps(data, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()

