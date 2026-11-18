#!/usr/bin/env python3
"""
Sincronizador e Reparador de Metadados Antigravity (WSL -> Windows) — Otimizado O(1)
1. Associa conversas aos UUIDs dos projetos com base no workspace_uris (somente quando há pendências).
2. Garante títulos válidos onde estiver vazio.
3. Sincroniza com fast-path O(1) por conversationId no evento Stop (evitando varreduras 9P O(N))
   e throttle configurável para o backup de conversation_summaries.db.
4. Retorna JSON válido ({}) para compatibilidade estrita com o Stop Hook (protojson).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

PROJECT_MAP = {
    "projects/clearer-engineering-harness": "76673107-434a-4840-83db-1b0ae92657cf",
    "projects/verificador-deterministico": "15b68596-7443-4e75-a36c-41e886706394",
    "projects/events": "f9aafe1d-967d-441a-94a3-f45a20678788",
    "projects/skynet-v2": "1e12a4fa-fa44-42a4-95c0-80fa356457eb",
    "projects/eleicao": "26b4128c-8c0f-4620-a27d-67903b6dfed9",
    "projects/aidev-superpowers-v3-1": "549bffde-f798-49e2-81a1-8020cb18cad7",
    "projects/audit-legay": "ca5a0146-8adf-42f0-83b4-df6f89ba9b03",
    "projects/aviationstack_api": "4dd13701-0412-436c-8875-24510cd9587e",
    "projects/bruno-example": "e49cd811-e56e-4836-86f4-2065190e3e01",
    "projects/guest-list-pro": "2e40296a-6cbe-40a1-9756-f8ea71f508a6",
    "projects/metodo-akita": "33ad355b-7f77-4a59-bbae-eee80569757f",
    "projects/dev-memory-laravel": "476a112e-3472-42b9-b4ed-f1bb5016aa61",
    "projects/clickup_integration": "715ec129-fa38-4103-a017-d87131d2ccfb",
    "projects/devorq": "7cab3739-34e1-4d4f-aac0-a09e7861f4fa",
    "projects/neo-brutalist-theme": "8e270a92-4fb0-4c01-908b-508294247631",
    "projects/remessa-calc": "a0a080ba-de7c-43ea-8bc2-ff9cae0e1d4c",
    "projects/dash_orange": "cce78410-a4d7-4ca5-85e8-a6a9a5af00d9",
    "projects/EventosPro": "d21db2a7-1e0e-403f-9f51-869b2cdf2255",
    "projects/filament-design-kit": "e2111c77-5061-4fba-a703-c40b37b48d63",
    "projects/codex-report": "5b28e1e4-3542-42f1-8215-7348b95fec7c",
    "projects/nandorag": "57b78088-367b-4d1f-a504-6611202fc128",
    "projects/personal_fin": "0a2cbc48-c849-4f19-8e0b-605f7c682e1c",
    "projects/eventos-control": "06386542-669f-42bf-91bf-cd2f07f457aa",
}

_SAFE_CONV_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def safe_copy(src: Path, dst: Path, dry_run: bool = False) -> bool:
    if dry_run:
        return True
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        with open(src, "rb") as fsrc:
            with open(dst, "wb") as fdst:
                while True:
                    chunk = fsrc.read(64 * 1024)
                    if not chunk:
                        break
                    fdst.write(chunk)
        return True
    except Exception as e:
        print(f"Aviso safe_copy {src.name} -> {dst.name}: {e}", file=sys.stderr)
        return False


def _read_hook_payload() -> Dict[str, Any]:
    try:
        if sys.stdin is None or sys.stdin.isatty():
            return {}
        raw = sys.stdin.read()
        if not raw or not raw.strip():
            return {}
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _load_state(state_file: Path) -> Dict[str, Any]:
    if not state_file.is_file():
        return {}
    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_state(state_file: Path, state: Dict[str, Any], dry_run: bool) -> None:
    if dry_run:
        return
    try:
        state_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = state_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
        os.replace(tmp, state_file)
    except Exception as e:
        print(f"Aviso save_state: {e}", file=sys.stderr)


def _repair_wsl_db_if_needed(wsl_root: Path, wsl_db: Path, dry_run: bool) -> Dict[str, Any]:
    metrics = {"db_check_ran": False, "db_repairs_needed": False}
    if not wsl_db.exists():
        return metrics

    metrics["db_check_ran"] = True
    try:
        if dry_run:
            conn = sqlite3.connect(f"file:{wsl_db}?mode=ro", uri=True, timeout=10)
        else:
            conn = sqlite3.connect(wsl_db, timeout=10)
        cur = conn.cursor()

        cur.execute(
            """
            SELECT 1 FROM conversation_summaries
            WHERE project_id = ''
               OR project_id = 'default-cli-project'
               OR project_id IS NULL
               OR source = 'CORTEX_TRAJECTORY_SOURCE_CLI'
               OR title = ''
               OR title IS NULL
            LIMIT 1
            """
        )
        if cur.fetchone() is None:
            conn.close()
            return metrics

        metrics["db_repairs_needed"] = True
        if dry_run:
            conn.close()
            return metrics

        for folder, pid in PROJECT_MAP.items():
            cur.execute(
                """
                UPDATE conversation_summaries
                SET project_id = ?
                WHERE (project_id = '' OR project_id = 'default-cli-project' OR project_id IS NULL)
                  AND workspace_uris LIKE ?
                """,
                (pid, f"%{folder}%"),
            )

        cur.execute(
            """
            UPDATE conversation_summaries
            SET source = ''
            WHERE source = 'CORTEX_TRAJECTORY_SOURCE_CLI'
            """
        )

        cur.execute("SELECT conversation_id, preview FROM conversation_summaries WHERE title = '' OR title IS NULL")
        rows = cur.fetchall()
        for cid, prev in rows:
            pbtxt_path = wsl_root / "annotations" / f"{cid}.pbtxt"
            found_title = ""
            if pbtxt_path.exists():
                try:
                    content = pbtxt_path.read_text(errors="ignore")
                    if 'title:"' in content:
                        found_title = content.split('title:"')[1].split('"')[0].strip()
                    elif 'title: "' in content:
                        found_title = content.split('title: "')[1].split('"')[0].strip()
                except Exception:
                    pass

            if not found_title and prev:
                clean = prev.strip().replace("\n", " ").replace("\r", "")
                found_title = clean[:57] + "..." if len(clean) > 60 else clean

            if found_title:
                cur.execute("UPDATE conversation_summaries SET title = ? WHERE conversation_id = ?", (found_title, cid))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Aviso reparo DB: {e}", file=sys.stderr)
    return metrics


def _sync_single_file_if_changed(src: Path, dst: Path, dry_run: bool) -> bool:
    if not src.is_file():
        return False
    try:
        if not dst.exists() or src.stat().st_size != dst.stat().st_size:
            return safe_copy(src, dst, dry_run=dry_run)
    except Exception:
        return False
    return False


def repair_and_sync(full: bool = False, dry_run: bool = False, conversation_id: str = "") -> Dict[str, Any]:
    t0 = time.perf_counter_ns()
    wsl_root = Path("/home/nandodev/.gemini/antigravity")
    win_root = Path("/mnt/c/Users/atiga/.gemini/antigravity")

    stats: Dict[str, Any] = {
        "mode": "skipped",
        "db_copied": False,
        "proto_copied": False,
        "files_copied": 0,
        "ninep_stats": 0,
        "dry_run": dry_run,
    }

    if not wsl_root.exists() or not win_root.exists():
        stats["elapsed_ms"] = round((time.perf_counter_ns() - t0) / 1e6, 2)
        return stats

    wsl_db = wsl_root / "conversation_summaries.db"
    win_db = win_root / "conversation_summaries.db"
    state_file = Path(os.environ["AGY_WIN_SYNC_STATE_FILE"]) if os.environ.get("AGY_WIN_SYNC_STATE_FILE") else (wsl_root / "cache" / "win_sync_state.json")

    now = time.time()
    db_interval_sec = int(os.environ.get("AGY_WIN_SYNC_DB_INTERVAL_SEC", "300"))
    full_interval_sec = int(os.environ.get("AGY_WIN_SYNC_FULL_INTERVAL_SEC", "3600"))
    state = _load_state(state_file)

    # 1. Reparar no banco do WSL somente se houver registros pendentes
    db_info = _repair_wsl_db_if_needed(wsl_root, wsl_db, dry_run=dry_run)
    stats.update(db_info)

    # 2. Backup do conversation_summaries.db apenas quando alterado + intervalo respeitado (ou --full)
    if wsl_db.exists():
        db_st = wsl_db.stat()
        db_changed = (
            db_st.st_mtime_ns != state.get("last_db_mtime_ns")
            or db_st.st_size != state.get("last_db_size")
        )
        db_due = (now - float(state.get("last_db_sync_ts", 0))) >= db_interval_sec
        if full or (db_changed and db_due) or not state.get("last_db_sync_ts"):
            if not dry_run:
                try:
                    src_conn = sqlite3.connect(wsl_db, timeout=10)
                    dst_conn = sqlite3.connect(win_db, timeout=10)
                    src_conn.backup(dst_conn)
                    dst_conn.close()
                    src_conn.close()
                except Exception as e:
                    print(f"Fallback para safe_copy do DB: {e}", file=sys.stderr)
                    safe_copy(wsl_db, win_db)
            state["last_db_sync_ts"] = now
            state["last_db_mtime_ns"] = db_st.st_mtime_ns
            state["last_db_size"] = db_st.st_size
            stats["db_copied"] = True

    # 3. Sincronizar agyhub_summaries_proto.pb via assinatura em cache ext4
    wsl_proto = wsl_root / "agyhub_summaries_proto.pb"
    win_proto = win_root / "agyhub_summaries_proto.pb"
    if wsl_proto.exists():
        p_st = wsl_proto.stat()
        proto_changed = (
            p_st.st_mtime_ns != state.get("last_proto_mtime_ns")
            or p_st.st_size != state.get("last_proto_size")
        )
        if full or proto_changed or not state.get("last_proto_mtime_ns"):
            if safe_copy(wsl_proto, win_proto, dry_run=dry_run):
                state["last_proto_mtime_ns"] = p_st.st_mtime_ns
                state["last_proto_size"] = p_st.st_size
                stats["proto_copied"] = True

    # 4. Fast-path O(1) por conversationId vs Sweep completo (intervalo de 1h ou --full)
    conv_id = conversation_id.strip()
    valid_conv_id = bool(conv_id and _SAFE_CONV_ID_RE.fullmatch(conv_id))
    full_sweep_due = (now - float(state.get("last_full_sweep_ts", 0))) >= full_interval_sec

    if not full and valid_conv_id and not full_sweep_due:
        stats["mode"] = "fast_path_o1"
        ann_src = wsl_root / "annotations" / f"{conv_id}.pbtxt"
        if ann_src.is_file():
            stats["ninep_stats"] += 1
            if _sync_single_file_if_changed(ann_src, win_root / "annotations" / ann_src.name, dry_run):
                stats["files_copied"] += 1

        conv_src = wsl_root / "conversations" / f"{conv_id}.db"
        if conv_src.is_file():
            stats["ninep_stats"] += 1
            if _sync_single_file_if_changed(conv_src, win_root / "conversations" / conv_src.name, dry_run):
                stats["files_copied"] += 1

        brain_src = wsl_root / "brain" / conv_id
        if brain_src.is_dir():
            for item in brain_src.iterdir():
                if item.is_file() and item.suffix.lower() in (".md", ".html"):
                    stats["ninep_stats"] += 1
                    if _sync_single_file_if_changed(item, win_root / "brain" / conv_id / item.name, dry_run):
                        stats["files_copied"] += 1
    else:
        stats["mode"] = "full_sweep"
        wsl_ann = wsl_root / "annotations"
        win_ann = win_root / "annotations"
        if not dry_run:
            win_ann.mkdir(parents=True, exist_ok=True)
        if wsl_ann.exists():
            for f in wsl_ann.glob("*.pbtxt"):
                stats["ninep_stats"] += 1
                if _sync_single_file_if_changed(f, win_ann / f.name, dry_run):
                    stats["files_copied"] += 1

        wsl_conv = wsl_root / "conversations"
        win_conv = win_root / "conversations"
        if not dry_run:
            win_conv.mkdir(parents=True, exist_ok=True)
        if wsl_conv.exists():
            for f in wsl_conv.glob("*.db"):
                stats["ninep_stats"] += 1
                if _sync_single_file_if_changed(f, win_conv / f.name, dry_run):
                    stats["files_copied"] += 1

        wsl_brain = wsl_root / "brain"
        win_brain = win_root / "brain"
        if not dry_run:
            win_brain.mkdir(parents=True, exist_ok=True)
        if wsl_brain.exists():
            for conv_dir in wsl_brain.iterdir():
                if conv_dir.is_dir():
                    dst_conv = win_brain / conv_dir.name
                    for item in conv_dir.iterdir():
                        if item.is_file() and item.suffix.lower() in (".md", ".html"):
                            stats["ninep_stats"] += 1
                            if _sync_single_file_if_changed(item, dst_conv / item.name, dry_run):
                                stats["files_copied"] += 1
        state["last_full_sweep_ts"] = now

    _save_state(state_file, state, dry_run=dry_run)
    stats["elapsed_ms"] = round((time.perf_counter_ns() - t0) / 1e6, 2)
    return stats


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Sincronizador Antigravity WSL -> Windows (O(1) Stop Hook)")
    parser.add_argument("--full", action="store_true", help="Força sweep completo e backup imediato do DB")
    parser.add_argument("--dry-run", action="store_true", help="Simula e contabiliza sem gravar alterações")
    parser.add_argument("--stats-stderr", action="store_true", help="Emite métricas JSON em stderr")
    args = parser.parse_args(argv)

    payload = _read_hook_payload()
    conv_id = str(payload.get("conversationId") or payload.get("conversation_id") or "").strip()

    stats = repair_and_sync(full=args.full, dry_run=args.dry_run, conversation_id=conv_id)
    if args.stats_stderr:
        print(json.dumps(stats, ensure_ascii=False), file=sys.stderr)

    print(json.dumps({}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
