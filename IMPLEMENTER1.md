# Implementer1 and Orchestrator1 Plan

## Goal

Keep the teaching workflow small while moving orchestration and validation out
of the implementation model. A long-running learner chat launches a fresh,
phase-local `orchestrator1`; that orchestrator launches a fresh writer for the
requested roadmap phase. Version 1 has no repair loop and no documentation
lookup.

```text
learner/main chat -> fresh orchestrator1 -> fresh implementer1
```

The main chat receives only the final compact report. It does not copy its
prior transcript, summaries, or implementation code into `orchestrator1`.
This provides per-phase context isolation without requiring learners to start
a new chat.

## Role boundaries

| Role | Responsibility | May change application files? | May run pytest? |
|---|---|---:|---:|
| Main chat | Launch one phase and receive its report | No | No |
| `orchestrator1` | Read, packetize, delegate, validate, check contract, report | No | Yes |
| `implementer1` | Read named targets and write the requested phase | Yes | No |

`orchestrator1` never writes application code. `implementer1` never runs
Bash, validates, or repairs its own failed validation. This makes the
orchestrator's deterministic validation result the source of truth.

## Orchestrator1 workflow

1. Accept only a requested roadmap phase.
2. Read `specs/mission.md`, `specs/tech-stack.md`, the requested roadmap
   phase, and every existing target file directly. A glob result is not a read.
3. Classify each path as `new`, `shared`, or `read-only`.
4. Record `git status --short` before delegation. Treat it as diagnostic only:
   it cannot attribute rewrites of already-modified or untracked files. Use a
   clean or committed phase checkpoint when changed-file attribution matters.
5. Build one compact, self-contained packet for `implementer1` containing:
   - repo-relative writable paths and their ownership classification;
   - exact required behavior, user-visible literals, routes, imports, and
     tests;
   - all behavior, routes, imports, strings, and tests that shared files must
     preserve; and
   - phase-specific framework facts needed to avoid known traps.
6. Do not include full file contents, code blocks, pseudocode, or a line-by-line
   solution. Exact acceptance facts are allowed.
7. Delegate exactly once to a fresh `implementer1`.
8. Run `.venv/bin/python -m pytest tests/` exactly once after the child returns.
9. Record `git status --short` again and report it. With a clean phase
   checkpoint, fail if application files outside the packet changed; otherwise
   do not claim that status alone proves attribution.
10. Read changed packet files and complete a coverage matrix for every roadmap
    requirement: requirement, expected evidence, observed file and line, and
    pass or fail. Important requirements should also be covered by deterministic
    tests or string checks.
11. Report the exact pytest output, warnings, files changed, coverage matrix,
    and every contract failure. Do not infer success from the child summary.

## Failure policy

Version 1 does not repair. The implementation child never repairs itself, and
`orchestrator1` never delegates a second writer or edits code. On a pytest
failure, missing contract evidence, unavailable environment, or unexpected
change, it stops and returns the evidence to the main chat.

Warnings are reported but do not fail the phase unless the phase contract says
that warnings are an acceptance failure. A missing environment or permission is
not a code-repair task.

## Implementer1 contract

`implementer1` is a narrow writer:

- Read only named existing target files.
- Create paths marked `new` directly.
- For small targets, write complete final contents and preserve every shared
  behavior named in the packet.
- Do not call `task`, Bash, documentation tools, or external search.
- Do not test, diagnose, repair, or broaden scope.
- Return a structured list of files created or modified and any blocking tool
  error.

The desired mutation style is `write`, not anchor-based `edit`, because stale
`oldString` anchors caused repeated no-op loops. Current OpenCode permission
mapping does not reliably distinguish `write` from `edit`; a true write-only
guarantee requires a custom write-only tool or deterministic transform. Until
then, enforce the preference in the packet and inspect telemetry.

## Permissions and limits

`orchestrator1` should deny application writes and edits. It needs direct
`read`, one nested `task`, `git status --short`, and the exact direct-venv
pytest command. Disable broad `glob`, shell exploration, web search, and skills
by default. Pin the resolved Gemma 4 12B provider and model in its definition,
then confirm the resolved value in telemetry.

`implementer1` should allow only direct reads and application mutation. Remove
`mkdir`, `ls`, broad pytest patterns, and default documentation lookup. Earlier
runs showed that permissive Bash invited unnecessary directory creation and
retry loops.

Use a modest step cap for `orchestrator1` and a smaller cap for each writer.
The caps are circuit breakers, not proof that the repair limit is enforced.

## Context and Context7

Run `orchestrator1` as a fresh nested subagent for each phase. It reads the
workspace itself and receives no copied main-chat history. Its implementer is
also fresh and receives only the compact packet.

Context7 is out of scope for version 1. The Phase 1 and 2 Gemma parent contexts
peaked near 12K effective tokens; the observed failures were packet coverage
and role-boundary failures, not context-window exhaustion. Reconsider a tightly
bounded lookup only after the basic nested-agent pilot is reliable.

The nested-agent architecture passed a local read-only platform pilot on
OpenCode 1.17.18: a fresh primary session spawned `orchestrator1`, which spawned
a fresh `implementer1`, and the leaf result returned through both parents.
This confirms the session and permission path, including explicit
`task: implementer1: allow` on the subagent orchestrator. It does not prove
that a full phase workflow is reliable; rerun the smoke test after OpenCode
upgrades.

## Pilot success criteria

- The parent reads every shared target before delegation.
- The packet covers every roadmap bullet and preserved contract without
  containing complete source code.
- Only a writer changes application files.
- Pytest is run once by the orchestrator and its literal result is reported.
- A failed first attempt is reported to the main chat; it is never silently
  repaired by the original child or the orchestrator.
- Telemetry confirms the resolved models, tool calls, changed-file set, raw
  request timing, fresh input, and cache reads.
- The nested-session smoke test remains green after an OpenCode upgrade.
