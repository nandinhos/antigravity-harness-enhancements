#!/usr/bin/env python3
"""
harness-telemetry-benchmark.py
Bateria de Testes e Telemetria de Eficiência de Tokens e Latência do Harness Antigravity.
Metodologia Ponytail: Verificação Determinística e Observação Direta (OBSERVED).
"""

import os
import sys
import time
import json
import subprocess
from pathlib import Path

WORKSPACE = Path("/home/nandodev/projects/antigravity-harness-enhancements")

def estimate_tokens(text: str) -> int:
    """Estimativa conservadora padrão da indústria para modelos LLM modernos (média ~3.8 chars/token)."""
    if not text:
        return 0
    return max(1, int(len(text) / 3.8))

def run_cmd(cmd: list[str], cwd: Path = WORKSPACE) -> tuple[int, str, float]:
    start = time.perf_counter()
    env = os.environ.copy()
    env["PATH"] = f"/home/nandodev/.gemini/antigravity/bin:/home/nandodev/.local/bin:{env.get('PATH', '')}"
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            timeout=30
        )
        duration_ms = (time.perf_counter() - start) * 1000
        output = proc.stdout if proc.returncode == 0 else proc.stderr
        return proc.returncode, output, duration_ms
    except Exception as e:
        duration_ms = (time.perf_counter() - start) * 1000
        return 1, str(e), duration_ms

def benchmark_suite():
    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "environment": "WSL2 Ubuntu (Linux x86_64)",
        "cases": []
    }

    print("🚀 Iniciando Bateria de Testes de Telemetria do Harness Antigravity...")

    # =========================================================================
    # Caso 1: Descoberta Arquitetural (Leitura Bruta vs Graphify AST)
    # =========================================================================
    print("\n[Caso 1] Descoberta Arquitetural...")
    files_to_read = [
        WORKSPACE / "bootstrap-workstation.sh",
        WORKSPACE / "HARNESS_DOCUMENTATION.md",
        WORKSPACE / "SETUP_WORK_MACHINE.md",
        WORKSPACE / "templates/gemini-orchestrator.agent.md"
    ]
    raw_content = ""
    for f in files_to_read:
        if f.exists():
            raw_content += f.read_text(encoding="utf-8")
    
    raw_bytes = len(raw_content.encode("utf-8"))
    raw_tokens = estimate_tokens(raw_content)

    # Graphify query
    code, graphify_out, graphify_ms = run_cmd(["graphify", "query", "bootstrap"])
    graph_bytes = len(graphify_out.encode("utf-8"))
    graph_tokens = estimate_tokens(graphify_out)
    reduction_pct = ((raw_bytes - graph_bytes) / raw_bytes) * 100 if raw_bytes > 0 else 0

    case1 = {
        "id": "CASE-01",
        "name": "Descoberta Arquitetural e Mapeamento de Dependências",
        "traditional": {
            "strategy": "Leitura bruta de arquivos (view_file em lote)",
            "bytes": raw_bytes,
            "estimated_tokens": raw_tokens,
            "lines": raw_content.count("\n")
        },
        "optimized": {
            "strategy": "Graphify AST Knowledge Graph (Tree-Sitter zero-token)",
            "bytes": graph_bytes,
            "estimated_tokens": graph_tokens,
            "lines": graphify_out.count("\n"),
            "latency_ms": round(graphify_ms, 2),
            "exit_code": code
        },
        "token_reduction_pct": round(reduction_pct, 2)
    }
    results["cases"].append(case1)
    print(f"  ✓ Tradicional: {raw_tokens} tokens | Graphify: {graph_tokens} tokens | Redução: {reduction_pct:.2f}% | Latência: {graphify_ms:.1f}ms")

    # =========================================================================
    # Caso 2: Inspeção de God-Nodes & Topologia Central
    # =========================================================================
    print("\n[Caso 2] Identificação de Componentes Centrais (God Nodes)...")
    # Tradicional: grep recursivo e contagem manual em múltiplos scripts
    grep_code, grep_out, grep_ms = run_cmd(["grep", "-rn", "function\\|class\\|def", str(WORKSPACE)])
    grep_bytes = len(grep_out.encode("utf-8"))
    grep_tokens = estimate_tokens(grep_out)

    # Graphify god-nodes
    gn_code, gn_out, gn_ms = run_cmd(["graphify", "god-nodes", "--top", "5"])
    gn_bytes = len(gn_out.encode("utf-8"))
    gn_tokens = estimate_tokens(gn_out)
    gn_reduction = ((grep_bytes - gn_bytes) / grep_bytes) * 100 if grep_bytes > 0 else 0

    case2 = {
        "id": "CASE-02",
        "name": "Identificação de Nós Centrais de Arquitetura",
        "traditional": {
            "strategy": "Grep recursivo de símbolos no repositório",
            "bytes": grep_bytes,
            "estimated_tokens": grep_tokens,
            "latency_ms": round(grep_ms, 2)
        },
        "optimized": {
            "strategy": "Graphify PageRank & Centrality Analysis",
            "bytes": gn_bytes,
            "estimated_tokens": gn_tokens,
            "latency_ms": round(gn_ms, 2),
            "exit_code": gn_code
        },
        "token_reduction_pct": round(gn_reduction, 2)
    }
    results["cases"].append(case2)
    print(f"  ✓ Grep bruto: {grep_tokens} tokens | Graphify God-Nodes: {gn_tokens} tokens | Redução: {gn_reduction:.2f}% | Latência: {gn_ms:.1f}ms")

    # =========================================================================
    # Caso 3: Overhead e Latência de Interceptação dos Hooks do context-mode
    # =========================================================================
    print("\n[Caso 3] Teste de Sobrecarga (Hook Latency & Resilience)...")
    payload = json.dumps({"toolCall": {"name": "run_command", "args": {"command": "git status"}}, "output": "clean"})
    
    # Executar 5 iterações para medir média e desvio
    latencies = []
    for _ in range(5):
        t0 = time.perf_counter()
        p = subprocess.run(
            ["context-mode", "hook", "antigravity-cli", "posttooluse"],
            input=payload,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=os.environ.copy()
        )
        latencies.append((time.perf_counter() - t0) * 1000)

    avg_hook_ms = sum(latencies) / len(latencies)
    case3 = {
        "id": "CASE-03",
        "name": "Sobrecarga de Interceptação (Hook Execution Latency)",
        "iterations": 5,
        "avg_latency_ms": round(avg_hook_ms, 2),
        "min_latency_ms": round(min(latencies), 2),
        "max_latency_ms": round(max(latencies), 2),
        "exit_code": p.returncode,
        "status": "PASS" if p.returncode == 0 and avg_hook_ms < 500 else "FAIL"
    }
    results["cases"].append(case3)
    print(f"  ✓ Latência média do hook: {avg_hook_ms:.2f}ms | Exit code: {p.returncode} | Status: {case3['status']}")

    # Resumo Geral
    total_raw_tokens = raw_tokens + grep_tokens
    total_opt_tokens = graph_tokens + gn_tokens
    total_reduction = ((total_raw_tokens - total_opt_tokens) / total_raw_tokens) * 100

    results["summary"] = {
        "total_traditional_tokens": total_raw_tokens,
        "total_optimized_tokens": total_opt_tokens,
        "global_reduction_pct": round(total_reduction, 2),
        "hook_overhead_ms": round(avg_hook_ms, 2)
    }

    print("\n========================================================")
    print(f"📊 RESUMO DA TELEMETRIA:")
    print(f"   Tokens Tradicionais: {total_raw_tokens}")
    print(f"   Tokens com Harness:  {total_opt_tokens}")
    print(f"   Economia Global:     {total_reduction:.2f}%")
    print(f"   Overhead de Hook:    {avg_hook_ms:.2f} ms")
    print("========================================================")

    out_file = WORKSPACE / "telemetry_benchmark_report.json"
    out_file.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n✓ Relatório de telemetria salvo em: {out_file}")

if __name__ == "__main__":
    benchmark_suite()
