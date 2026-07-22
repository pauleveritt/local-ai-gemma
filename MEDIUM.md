# Brief: Build the "Medium" tier (command + implementer)

## Goal

Replace the retired "Minimum Plus", "Medium", and "Maximum" tiers with a single
new **Medium** tier: a `/phase N` OpenCode command that turns the main chat into
a controller/validator, delegating all writing to a fresh, write-only
`implementer1a` subagent, with at most one repair. Clean the repo and README to
leave exactly two tiers: **minimum** and **medium**.

## Context you need

- This is a teaching repo showing how to steer small local models (Gemma 4 12B
  via OpenCode) through constrained subagent workflows. Read `README.md`
  (especially the "Minimum prompt" section) and skim `LESSONS.md` before
  starting.
- The runtime is OpenCode 1.18.4 under PyCharm ACP. Key verified mechanics:
  - A command template is delivered to the main chat **verbatim**
    (`$ARGUMENTS` substituted); no model paraphrases it. This kills an observed
    failure where the main rewrote "Run Phase 1" into "provide a summary".
  - `@specs/foo.md` references inside a command template are resolved
    server-side into attached file parts — the spec content arrives with the
    message, deterministically.
  - `@implementer1a` in a template resolves to an agent mention that nudges the
    main to call the `task` tool with that subagent.
  - `read` and `edit` permissions match **worktree-relative** path patterns, so
    `specs/*` denies work. The `edit` permission key governs `write`, `edit`,
    and `patch` collectively. Last matching rule wins.
  - A `"*": deny` permission rule hides every tool not explicitly re-allowed,
    including tools injected by IDE clients. Subagents are additionally denied
    `task` automatically (no nested delegation).
  - Gemma's per-turn output is capped in provider config; packets and reports
    must stay terse, and repair packets must NAME files, never inline contents.
- Design rationale that must survive into the README (see task 5): the
  telemetry evidence for these choices lives in three failure sessions from
  2026-07-21 — a main-model prompt rewrite, an IDE-tool escape after denied
  Bash, and a subagent depth-limit failure. Do not re-investigate; the design
  below already accounts for them.

## Tasks

### 1. Create `.opencode/command/phase.md`

Exactly this content:

```markdown
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
```

### 2. Rewrite `.opencode/agents/implementer1a.md`

Replace its entire content with:

```markdown
---
description: >-
  Write-only implementer for one packetized roadmap phase. Its entire
  knowledge of the phase is the packet: it reads only packet-named files and
  writes complete final file contents. Validation belongs to the parent.
mode: subagent
model: lmstudio/gemma-4-12b-it-mlx
steps: 10
permission:
  "*": deny
  read:
    "*": allow
    "specs/*": deny
  edit:
    "*": allow
    "specs/*": deny
  pycharm_execute_tool: deny
---

You are a direct implementation agent for one delegated phase packet. Your
entire knowledge of the phase is the packet; you cannot and must not consult
specifications.

Read every existing packet-named file completely before changing anything;
read nothing else. For every writable file, use `write` with its complete
final content; never use `edit`. For a path marked new, create it directly
with `write`; do not inspect or verify its directory. Preserve every behavior
the packet lists for shared files.

Do not run tests, diagnose failures, or touch files outside the packet.
Finish by listing the files you wrote and a one-line summary of each, tersely.
```

Notes: the `"*": deny` default hides bash, glob, grep, list, todowrite,
webfetch, skill, task, and any client-injected tool; `read`/`edit` stay usable
everywhere except `specs/*`. The explicit `pycharm_execute_tool: deny` is
redundant under the default-deny but stays as a record of an observed escape —
do not mention it or PyCharm anywhere in the README.

### 3. Create project `opencode.jsonc` at the repo root

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "agent": {
    "build": {
      // Circuit breaker for the medium controller; a clean phase run needs
      // ~15-18 steps, so 25 allows one full run plus one repair, never two.
      "steps": 25,
      "permission": {
        "task": {
          // The learner clicks to approve each delegation: a visible handoff
          // and a manual repair counter.
          "implementer1a": "ask"
        }
      }
    }
  }
}
```

### 4. Raise the Gemma output cap to 4096

In `~/.config/opencode/opencode.jsonc` (user-global, outside this repo), change
`"output": 2048` to `"output": 4096` in **both** Gemma model entries:
`provider.omlx.models["gemma-4-12B-it-MLX-8bit"].limit` and
`provider.lmstudio.models["gemma-4-12b-it-mlx"].limit`. Leave everything else
in that file untouched.

### 5. Delete retired agents

`git rm` these four files (history preserves them):

- `.opencode/agents/implementer.md`
- `.opencode/agents/implementer2.md`
- `.opencode/agents/orchestrator1.md`
- `.opencode/agents/orchestrator2.md`

Keep `.opencode/agents/implementer1.md` (minimum tier — already correct, do
not modify) and the rewritten `implementer1a.md`.

### 6. Update `README.md`

- Jargon: exactly two tiers, **minimum** and **medium**. Update the sentence
  near the top that says "Do not change dependencies between minimum, medium,
  and maximum" to reference only minimum and medium. Remove any "Maximum"
  stub from TODO/"New sections" lists.
- Keep the existing "Minimum prompt" section as-is.
- Replace the "Minimum Plus" section with a new "**Medium**" section, and
  delete the old "Medium prompt" section (it described the retired
  orchestrator2/implementer2 pair). The new Medium section must contain:
  - Usage: start a fresh main chat, type `/phase N`. Use your normal primary
    agent; no UI agent selection is required.
  - A short architecture description: the command expands into a controller
    protocol for the main chat; the main authors a handoff packet, delegates
    to a fresh write-only `@implementer1a`, validates independently with
    `.venv/bin/python -m pytest tests/` and a `git status --short` baseline
    diff, reports a coverage matrix, and may send exactly one repair to one
    fresh implementer child.
  - A numbered "What changed from minimum, and why" list covering, in this
    order:
    1. The protocol is delivered by a command, not typed: `$ARGUMENTS` is
       substituted and the template reaches the main verbatim, so the learner
       prompt shrinks to `/phase N` and paraphrase drift at kickoff is
       eliminated. The command guarantees the protocol is *received*, not that
       it is *followed*; telemetry remains the check.
    2. Validation moved from the implementer to the main chat. The implementer
       has no Bash at all; the main runs the one validation command itself and
       diffs `git status --short` against a pre-delegation baseline, so scope
       checking no longer trusts the implementer's self-report and the old
       non-mechanical "terminal validation ordering" rule is retired.
    3. One repair is now allowed: exactly one delegation to a *fresh*
       implementer child carrying only the implicated file names, the exact
       pytest failure, and the required fix — never file contents, which
       would risk truncation under the model's output cap. The repair child
       reads the named files itself and rewrites complete files, so the
       edit-anchor (`oldString`) failure mode never applies.
    4. The implementer's permissions are default-deny: every tool is denied
       unless explicitly allowed, including any tool an IDE client injects.
       Reads and writes are allowed everywhere except `specs/*` — the
       implementer structurally cannot consult the roadmap and improvise
       scope; its entire knowledge of the phase is the packet.
    5. The controller is bounded: a step cap on the primary agent converts
       runaway drift into visible failure, and each delegation requires a
       click-through approval that doubles as a manual repair counter. (If
       the approval dialog offers "always", declining to use it keeps the
       counter working.)
    6. The Gemma model entries raise `limit.output` to 4096 so packets and
       coverage matrices are not truncated mid-message; packets must still
       stay terse and never inline file contents.
    7. The command's first line tells the main to refuse to run in a chat
       with prior phase work. This is model-enforced, but it fails visibly
       to the learner instead of silently degrading isolation.
- Document the required user-global config (task 4) wherever the README
  currently documents environment/setup requirements: the medium tier expects
  the Gemma provider entries to set `limit.output: 4096`.

## Out of scope — do not touch

- `LESSONS.md` and `IMPLEMENTER1.md`: historical evidence/design records;
  leave them even though they reference retired agents.
- `specs/`, `tests/`, application code, `.opencode/agents/implementer1.md`.
- Do not mention PyCharm, ACP, or IDE names anywhere in the README.

## Verification

1. Frontmatter and config parse: check the YAML frontmatter of both agent
   files and the JSONC syntax of `opencode.jsonc` (a Python `yaml.safe_load`
   of the frontmatter block is enough for the former).
2. `.venv/bin/python -m pytest tests/` still passes (you changed no app code).
3. `git status --short` shows only: the new command file, the rewritten
   `implementer1a.md`, the new `opencode.jsonc`, the four deletions, the
   README changes, and this brief.
4. Note for the human (put it in your final report, do not attempt it): smoke
   test `/phase` on a trivial phase from the IDE and confirm in telemetry that
   the template arrived verbatim and the delegation/validation/repair flow ran.

## Commit

One commit at the end, message:
`Add medium tier: /phase command with write-only implementer1a; retire old tiers`
