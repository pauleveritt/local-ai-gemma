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

1. Read every existing file the phase names as a target. Run
   `git status --short` and keep the output as your baseline.

2. Build one compact, self-contained packet for the implementer containing:
   every writable repo-relative path, each marked new or existing; for each
   existing file, the required final state and every current behavior that
   must be preserved; and exact literals, imports, route signatures, and test
   semantics when they are contract requirements. Do not refer the implementer
   to specification files or include file contents. Do not provide complete
   files, complete functions, code blocks, pseudocode, or line-by-line
   implementations. Include this exact instruction: "For every writable file,
   use `write` with its complete final content; never use `edit`. Read only
   the files this packet names."

3. Delegate exactly once to a fresh `@implementer1a` subagent with the packet
   as the prompt.

4. After it returns: run `.venv/bin/python -m pytest tests/` exactly once, run
   `git status --short`, compare against your baseline, and read each changed
   file. Complete a coverage matrix: requirement, expected evidence, observed
   file and line, pass or fail. Keep it terse.

5. If validation passed, report the matrix, the exact pytest result, and the
   changed files, then stop.

6. If validation failed, you get exactly one repair. Delegate once more to a
   fresh `@implementer1a` whose packet contains only: the names of the
   implicated files, the exact failing pytest output, and the required fix.
   Do not include file contents; the implementer reads the named files itself.
   Then run pytest exactly once more, redo the matrix, report the outcome —
   pass or fail — and stop. Never repair twice. A missing environment or
   permission is evidence to report, not something to fix.
