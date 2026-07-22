---
description: Run one roadmap phase — packet, fresh implementer, validation, one repair
---
If this chat contains prior phase work, stop and tell the learner to start a
fresh chat.

Run only Phase $ARGUMENTS. The specifications are attached:
@specs/mission.md @specs/tech-stack.md @specs/roadmap.md
Do not re-read them with tools.

You are the controller for this phase. You never write or edit application or
test files yourself; a fresh implementer subagent does all writing.

1. Run `git status --short` and keep the output as your baseline. In one
   assistant turn, issue a `read` call for every existing writable target.
   Do not delegate discovery or reading, wait between independent reads, or
   read files that are only read-only dependencies.

2. Build the canonical ledger and packet directly in the first `task` call; do
   not print a separate ledger or packet in your own response. The packet must
   have exactly three sections: Paths, Requirements, and Write Instruction.
   Paths use repo-relative names and label each readable path writable (new or
   existing) or read-only. For each existing writable file, state its required
   final state and every behavior that must be preserved. Requirements use one
   line per stable ID for every atomic Phase $ARGUMENTS requirement, including
   nested bullets and exact contract requirements. Never combine IDs, use ID
   ranges, paraphrase an exact literal, or add a grouped summary that restates
   requirements. Do not refer the implementer to specification files or
   include file contents. Do not provide complete files, complete functions,
   code blocks, pseudocode, or invented implementation details. Quote only an
   exact single-line fragment already present in the specifications when it is
   a contract requirement. The Write Instruction is exactly: "For every
   writable file, use `write` with its complete final content; never use
   `edit`. Read only paths explicitly listed as writable or read-only in this
   packet."

3. Task-call invariant:
   - Never call `explore` or `general`.
   - Your first `task` call must delegate exactly once to a fresh
     `@implementer1a` with the canonical packet.
   - If that task returns `state="completed"`, your next tool call must be
     `.venv/bin/python -m pytest tests/`, regardless of the child's prose.
   - Never make consecutive `task` calls. A second task call is allowed only
     after pytest has run and at least one ledger ID is explicitly failed.
   - If a task errors, report the error and stop; do not substitute another
     subagent or retry.

4. After the completed implementation task: run
   `.venv/bin/python -m pytest tests/` exactly once, run `git status --short`,
   compare against your baseline, then in one assistant turn issue a `read`
   call for every changed file. Complete the canonical ledger with exactly one
   line per ID in this form: `<ID>: pass — <repo-relative-path>:<line>` or
   `<ID>: fail — <repo-relative-path>:<line>`. Do not use a Markdown table,
   absolute paths, requirement prose, or additional matrix commentary.
   Validation passes only when pytest passes, every ledger
   ID passes, and no path outside the packet changed. Pytest passing alone is
   never sufficient.

5. If validation passed, report exactly these four sections, then stop:
   - `Outcome: complete — every packet requirement passed and no out-of-packet paths changed.`
   - `Validation: <exact final pytest summary line>`
   - `Changed: <comma-separated repo-relative paths>`
   - `Evidence:` followed by the readable ledger lines.

6. If validation failed, you get exactly one repair. Delegate once more to a
   fresh `@implementer1a` whose packet contains only: the names and roles of
   implicated files; every failed ledger ID with its exact expected and
   observed evidence; the required fix; and exact pytest output only if pytest
   failed. Do not include file contents. Then run pytest exactly once more, run
   `git status --short`, reread implicated and changed files in one assistant
   turn, and redo the complete readable ledger. Report the same four sections,
   using `Outcome: incomplete — <brief reason>.`, with the final pass-or-fail
   pytest summary, then stop. Never repair twice. A missing environment or
   permission is evidence to report, not something to fix.
