---
name: opencode-telemetry
description: Collect and analyze OpenCode session telemetry after a local coding run, including parent and child sessions, durations, turns, context and KV-cache usage, tool calls, output pollution, model resolution, and validation results. Use when a user asks what happened in an OpenCode run, why it was slow, whether a subagent struggled, or for a report comparing runs.
---

# OpenCode Telemetry

Treat telemetry as evidence. Do not explain a run from intuition before checking
the recorded session, message, and tool data. Small models often stumble in a
way that is invisible in the final prose; repeated tool calls, oversized output,
cache behavior, and parent/child timing usually explain the result.

## Workflow

1. Identify the OpenCode session from the user's run. If no ID is given, use the
   collector's latest-session listing and confirm the title and timestamp.
2. Run `scripts/collect_telemetry.py --session SESSION_ID` from this skill
   directory. Pass `--db PATH` only when automatic discovery finds the wrong
   database. Use `--format json` when another script needs the data.
3. Treat a parent session's database lifetime as an upper bound, not active work.
   Report both lifetime and the message activity span. A reused chat can contain
   long idle gaps.
4. Separate main-agent time from implementer time. Child sessions are nested in
   the parent lifetime, so do not add them and call the sum wall-clock time.
5. Interpret context as `input + cache_read` per assistant request. Report fresh
   input and cache-read tokens separately because LM Studio and oMLX account for
   them differently.
6. Inspect flagged tool output before forming a model diagnosis. Recursive
   listings, virtualenv contents, logs, and generated files can dominate context
   and duration without indicating a reasoning failure.
7. Run the repository's stated validation command when the user asks for quality.
   Report the exact result, including warnings and failures. Inspect the diff and
   relevant specs for behavior the tests do not cover.
8. Lead with evidence, then explain likely causes and confidence. Mark a theory
   as unproven when the telemetry does not contain a control run.

## Report

Use this compact structure:

```text
This run passed the smoke test: 1 passed, 2 warnings.

Metrics:
- Parent lifetime: ...; active message span: ...
- Main-agent time: ...; implementer time: ...
- Turns: ... main, ... implementer
- Implementer context: ... mean, ... peak; ... fresh input, ... cache read

Evidence:
- ... tool or session fact explaining the run

Quality:
- Findings first, with file and line references when applicable.
- State what passed, what is incomplete, and what the tests missed.
```

Never claim that cache was effective merely because `cache_read` is nonzero.
That proves reuse. Claim a speed benefit only when per-request timing or an
otherwise comparable no-cache run supports it.

## Collector

The bundled `scripts/collect_telemetry.py` uses only Python's standard library.
It searches platform-appropriate OpenCode data locations and opens the SQLite
database read-only. It also follows descendants through `parent_id`, counts
assistant turns and tool calls, computes context statistics, and flags suspicious
large tool outputs and recursive discovery commands.

Examples:

```bash
python scripts/collect_telemetry.py --list
python scripts/collect_telemetry.py --session ses_...
python scripts/collect_telemetry.py --session ses_... --format json
```

Use the project's Python interpreter when one is specified. The collector does
not mutate the database, start OpenCode, or infer code quality without a test
command and source inspection.
