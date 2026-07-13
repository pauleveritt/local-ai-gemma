#!/usr/bin/env python3
"""Collect evidence from an OpenCode SQLite database without mutating it."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import sqlite3
import statistics
import sys
from pathlib import Path
from typing import Any


RECURSIVE_COMMAND = re.compile(r"\b(?:ls\s+[^;&|]*-[^;&|]*r|tree|find)\b", re.I)
PROTECTED_PATH = re.compile(r"(?:\.venv|\.git|node_modules|__pycache__|\.cache|dist|build)", re.I)


def data_roots() -> list[Path]:
    home = Path.home()
    roots: list[Path] = []
    explicit = os.environ.get("OPENCODE_DATA_DIR")
    if explicit:
        roots.append(Path(explicit).expanduser())

    system = platform.system()
    if system == "Windows":
        for variable in ("LOCALAPPDATA", "APPDATA"):
            value = os.environ.get(variable)
            if value:
                roots.append(Path(value) / "opencode")
        roots.append(home / ".local" / "share" / "opencode")
    elif system == "Darwin":
        roots.extend(
            [
                home / ".local" / "share" / "opencode",
                home / "Library" / "Application Support" / "opencode",
            ]
        )
    else:
        roots.append(Path(os.environ.get("XDG_DATA_HOME", home / ".local" / "share")) / "opencode")

    # Keep order stable while removing duplicates.
    return list(dict.fromkeys(roots))


def find_database(explicit: str | None) -> Path | None:
    if explicit:
        path = Path(explicit).expanduser()
        return path if path.is_file() else None
    for root in data_roots():
        candidate = root / "opencode.db"
        if candidate.is_file():
            return candidate
    return None


def parse_json(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def ms_duration(start: int | None, end: int | None) -> float | None:
    if start is None or end is None:
        return None
    return round(max(0, end - start) / 1000, 3)


def connect(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def session_rows(db: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = db.execute(
        """
        SELECT id, parent_id, title, agent, model, directory,
               time_created, time_updated, tokens_input, tokens_output,
               tokens_reasoning, tokens_cache_read, tokens_cache_write
        FROM session ORDER BY time_created DESC
        """
    ).fetchall()
    names = [description[0] for description in db.execute("SELECT id, parent_id, title, agent, model, directory, time_created, time_updated, tokens_input, tokens_output, tokens_reasoning, tokens_cache_read, tokens_cache_write FROM session LIMIT 1").description]
    return [dict(zip(names, row)) for row in rows]


def descendants(rows: list[dict[str, Any]], root_id: str) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    pending = [root_id]
    while pending:
        current = pending.pop(0)
        matches = [row for row in rows if row["id"] == current]
        selected.extend(matches)
        pending.extend(row["id"] for row in rows if row["parent_id"] == current)
    return selected


def message_data(db: sqlite3.Connection, session_id: str) -> list[dict[str, Any]]:
    result = []
    for message_id, created, data in db.execute(
        "SELECT id, time_created, data FROM message WHERE session_id = ? ORDER BY time_created, id",
        (session_id,),
    ):
        item = parse_json(data)
        item["_id"] = message_id
        item["_time_created"] = created
        result.append(item)
    return result


def parts_for(db: sqlite3.Connection, session_id: str) -> list[dict[str, Any]]:
    result = []
    for created, data in db.execute(
        "SELECT time_created, data FROM part WHERE session_id = ? ORDER BY time_created, id",
        (session_id,),
    ):
        item = parse_json(data)
        item["_time_created"] = created
        result.append(item)
    return result


def analyze_session(db: sqlite3.Connection, row: dict[str, Any]) -> dict[str, Any]:
    messages = message_data(db, row["id"])
    parts = parts_for(db, row["id"])
    assistants = [message for message in messages if message.get("role") == "assistant"]
    contexts = []
    token_totals = {key: 0 for key in ("input", "output", "reasoning", "cache_read", "cache_write")}
    for message in assistants:
        tokens = message.get("tokens") or {}
        cache = tokens.get("cache") or {}
        for key in token_totals:
            if key in ("cache_read", "cache_write"):
                token_totals[key] += int(cache.get(key.removeprefix("cache_"), 0) or 0)
            else:
                token_totals[key] += int(tokens.get(key, 0) or 0)
        contexts.append(int(tokens.get("input", 0) or 0) + int(cache.get("read", 0) or 0))

    tools: dict[str, int] = {}
    suspicious: list[dict[str, Any]] = []
    for part in parts:
        if part.get("type") != "tool":
            continue
        name = str(part.get("tool", "unknown"))
        tools[name] = tools.get(name, 0) + 1
        state = part.get("state") or {}
        command = str((state.get("input") or {}).get("command", ""))
        output = str(state.get("output", ""))
        if name == "bash" and (RECURSIVE_COMMAND.search(command) or len(output) > 10000):
            suspicious.append(
                {
                    "tool": name,
                    "command": command[:240],
                    "output_chars": len(output),
                    "protected_path": bool(PROTECTED_PATH.search(command + output)),
                }
            )

    message_times = [message["_time_created"] for message in messages]
    first_message = min(message_times) if message_times else None
    last_message = max(message_times) if message_times else None
    return {
        "id": row["id"],
        "parent_id": row["parent_id"],
        "title": row["title"],
        "agent": row["agent"],
        "model": parse_json(row["model"]),
        "directory": row["directory"],
        "lifetime_seconds": ms_duration(row["time_created"], row["time_updated"]),
        "activity_span_seconds": ms_duration(first_message, last_message),
        "turns": len(assistants),
        "tokens": token_totals,
        "context": {
            "mean": round(statistics.mean(contexts), 1) if contexts else 0,
            "peak": max(contexts, default=0),
            "requests": len(contexts),
        },
        "tools": tools,
        "suspicious_tool_calls": suspicious,
    }


def render(report: dict[str, Any]) -> str:
    lines = ["OpenCode Telemetry Report", ""]
    lines.append(f"Database: `{report['database']}`")
    lines.append(f"Root session: `{report['root_session']}`")
    lines.append("")
    for session in report["sessions"]:
        model = session["model"]
        model_name = f"{model.get('providerID', '?')}/{model.get('id', '?')}"
        tokens = session["tokens"]
        context = session["context"]
        lines.extend(
            [
                f"### {session['title']} (`{session['id']}`)",
                f"- Agent/model: `{session['agent']}` / `{model_name}`",
                f"- Lifetime: `{session['lifetime_seconds']}s`; activity span: `{session['activity_span_seconds']}s`",
                f"- Turns: `{session['turns']}`; tools: `{session['tools']}`",
                f"- Tokens: input `{tokens['input']}`, output `{tokens['output']}`, reasoning `{tokens['reasoning']}`, cache read `{tokens['cache_read']}`",
                f"- Effective context: mean `{context['mean']}`, peak `{context['peak']}`",
            ]
        )
        for finding in session["suspicious_tool_calls"]:
            lines.append(
                f"- **Context risk:** `{finding['tool']}` command `{finding['command']}` produced `{finding['output_chars']}` output characters."
            )
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", help="Root OpenCode session ID; include descendants")
    parser.add_argument("--db", help="Path to opencode.db; otherwise discover it")
    parser.add_argument("--list", action="store_true", help="List recent sessions and exit")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()

    database = find_database(args.db)
    if database is None:
        print("Could not find opencode.db. Set OPENCODE_DATA_DIR or pass --db PATH.", file=sys.stderr)
        return 2

    with connect(database) as db:
        rows = session_rows(db)
        if args.list:
            for row in rows[:50]:
                print(f"{row['id']}\t{row['title']}\t{row['agent']}\t{row['directory']}")
            return 0
        if not args.session:
            print("Pass --session SESSION_ID, or use --list.", file=sys.stderr)
            return 2
        selected = descendants(rows, args.session)
        if not selected:
            print(f"Session not found: {args.session}", file=sys.stderr)
            return 2
        report = {
            "database": str(database),
            "root_session": args.session,
            "sessions": [analyze_session(db, row) for row in reversed(selected)],
        }

    if args.format == "json":
        print(json.dumps(report, indent=2))
    else:
        print(render(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
