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

1. Run `git status --short` and keep the output as your baseline. Read every
   existing writable target directly with `read`. Do not delegate discovery or
   reading, and do not read sibling files that the phase does not target.

2. Build the canonical ledger and packet directly in the first `task` call; do
   not print a separate ledger or packet in your own response. The packet must
   list every readable repo-relative path as either writable (new or existing)
   or read-only. For each existing writable file, state its required final
   state and every behavior that must be preserved. Assign a stable ID to every
   atomic Phase $ARGUMENTS requirement, including nested bullets and exact
   contract requirements. Use one line per ID: never combine IDs, use ID
   ranges, or paraphrase an exact literal, import, annotation, route signature,
   template fragment, or test semantic. Do not refer the implementer to
   specification files or include file contents. Do not provide complete files,
   complete functions, code blocks, pseudocode, or invented implementation
   details. Quote only an exact single-line fragment already present in the
   specifications when it is a contract requirement. Include this exact
   instruction: "For every writable file, use `write` with its complete final
   content; never use `edit`. Read only paths explicitly listed as writable or
   read-only in this packet."

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
   compare against your baseline, and read each changed file. Complete the
   canonical ledger as a compact matrix: ID, pass or fail, and observed file
   and line. Keep every ID distinct and preserve its packet wording. Validation
   passes only when pytest passes, every ledger ID passes, and no path outside
   the packet changed. Pytest passing alone is never sufficient.

5. If validation passed, report the compact matrix, the exact pytest result,
   and the changed files, then stop.

6. If validation failed, you get exactly one repair. Delegate once more to a
   fresh `@implementer1a` whose packet contains only: the names and roles of
   implicated files; every failed ledger ID with its exact expected and
   observed evidence; the required fix; and exact pytest output only if pytest
   failed. Do not include file contents. Then run pytest exactly once more, run
   `git status --short`, reread implicated and changed files, and redo the
   complete matrix. Report the outcome — pass or fail — and stop. Never repair
   twice. A missing environment or permission is evidence to report, not
   something to fix.
