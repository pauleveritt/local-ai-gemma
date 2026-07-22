# How To Keep Local AI Out Of The Ditch

The idea of this project is to show how to steer Local AI agent/model towards better/faster outcomes.

Kostia TODO

- Remove `uv` from prompt1

## Setup

Use the locked course-consistent environment for every workflow:

```bash
uv sync --frozen
uv run --frozen python -m pytest tests/
```

Do not change dependencies between minimum and medium. The specification and `uv.lock` are part of the experiment;
changing versions after a run makes the comparison invalid.

## New sections

- Simple version (Kostia) and bigger version (Isabel)
- Gemma 12, 26, DeepSeek Flash
- Explain why SLMs need so much help
- Qwen as big brain

## Model config

The LM Studio baseline came from the Gemma 4 12B IT MLX model metadata and the global LM Studio setting in
`~/.lmstudio`. The coding profile is the deliberate override used for small-agent runs.

```json
{
  "model": "lmstudio-community/gemma-4-12B-it-MLX-8bit",
  "native": {
    "max_position_embeddings": 262144,
    "default_context_length": 8192,
    "temperature": 1.0,
    "top_p": 0.95,
    "top_k": 64,
    "do_sample": true
  },
  "coding_profile": {
    "context": 40960,
    "input": 32768,
    "output": 4096,
    "temperature": 0.2,
    "top_p": 0.9,
    "top_k": 64
  }
}
```

- `max_position_embeddings`: The model supports a 256K position window, but using the maximum is unnecessary for these
  small coding tasks.
- `default_context_length`: LM Studio's global default was 8192; that is too tight for multi-turn orchestration, so the
  coding profile raises it.
- `context`: `40960` gives the parent and implementer room for tool results without reopening the earlier
  unbounded-context behavior.
- `input`: `32768` reserves part of the context budget for generated output and tool-call continuation.
- `output`: `4096` keeps medium-tier packets and coverage matrices from truncating mid-message.
- `temperature`: The native `1.0` setting is useful for general generation; `0.2` is more stable for repetitive code
  edits.
- `top_p`: The native `0.95` setting is retained for broad generation, while `0.9` narrows the coding distribution.
- `top_k`: `64` follows the model's native recommendation and is left unchanged in the coding profile.
- `do_sample`: Sampling remains enabled, with the lower coding temperature providing the needed determinism.

## Telemetry workflow

After an OpenCode run, ask Codex or OpenCode:

> Use your `opencode-telemetry` skill to evaluate the last prompt.

The skill finds the relevant session and produces an evidence-based report on the run: timing, agent and model activity,
context and cache use, tool calls, and validation or quality signals. Use its report to understand slowdowns or
unexpected outcomes; you do not need to run the telemetry collector yourself.

## Prompts

### Minimum prompt

Use your normal primary agent. Start a new chat for each phase and replace `N`
with its number. The prompt below tells the primary agent to use a fresh
`@implementer1` subagent; no UI agent selection is required.

The benefits:

1. *Phase-local, contract-complete scope*. The parent reads every shared target directly, then gives `@implementer1` one
   phase's requirements, named files, exact preservation requirements, and one validation command rather than an
   open-ended request.

2. *Fresh, single-purpose implementer*. A new @implementer1 has one job: implement one scoped phase. It avoids the
   parent’s accumulated context and prevents planning, design, and broad exploration from consuming the small model’s
   budget.

3. *One validation path and hard discovery boundaries*. The only permitted Bash command is the direct-venv validation
   command, preventing recursive listings, environment activation, and other dives into `.venv`. `glob` is also
   disabled, so an incomplete packet fails visibly instead of triggering broad repository discovery. The agent reports
   the exact result and does not diagnose or repair after validation. Treat the requested terminal ordering as a policy
   to inspect in telemetry, not as a mechanical guarantee; the Bash allowlist does not stop a later write tool call.

Notes:

a. Model instructions can still be ignored. Use telemetry to see what actually happened before adding another rule.

b. Ensure `.venv/bin/python -m pytest tests/` matches the implementer's Bash allowlist. Pointing directly at the virtual
environment works whether or not the project uses `uv`.

c. Plain Minimum works best from a fresh parent chat per phase. Medium below also creates a fresh phase runner for every
invocation, but a fresh parent chat remains the strongest isolation.

d. These constraints came from observed potholes. Keep the prompt only as strict as the telemetry evidence requires.

```markdown
Read @specs/mission.md, @specs/tech-stack.md, and @specs/roadmap.md. Run only Phase N.

Read the phase's target files, then delegate this phase exactly once to a fresh `@implementer1` subagent with a compact,
self-contained packet: repo-relative writable paths, complete required final state, and exact behavior/tests to
preserve. Do not refer the child to specification files or include file contents. Do not provide complete files,
complete functions, code blocks, pseudocode, or line-by-line implementations. Include exact literals, imports, route
signatures, API constraints, test semantics, and preserved behavior when they are contract requirements.

Include this exact instruction: "For every writable file, use `write` with its complete final content; never use
`edit`." Do not modify phase files or use another agent.

Tell the child this is its final tool call and it must stop whether it passes or fails:
`.venv/bin/python -m pytest tests/`.

After it returns, use only `read` on the reported changed files. Do not use Bash, glob, task, edit, or write. Report the
exact validation result, files changed, and only critical contract violations: missing required strings, routes,
imports, or unexpected files.
```

### Medium

Start a fresh main chat and type `/phase N`. Use your normal primary agent; no UI agent selection is required.

The command expands into a controller protocol for the main chat. The main creates one canonical packet, delegates to
a fresh write-only `@implementer1a`, validates independently with `.venv/bin/python -m pytest tests/`, a `git
status --short` baseline diff, and an atomic-requirement matrix, then may send exactly one evidence-based repair to a
fresh implementer child.

The medium tier expects both Gemma provider entries in the user-global
`~/.config/opencode/opencode.jsonc` to set `limit.output` to `4096`.

After changing `.opencode` agents, commands, or `opencode.jsonc`, restart the ACP session or IDE before running
`/phase`. OpenCode can retain an older registered command definition. Commit these control files before resetting a
phase worktree so a broad reset cannot silently restore an older workflow.

What changed from minimum, and why:

1. The protocol is delivered by a command, not typed: `$ARGUMENTS` is substituted and the template reaches the main
   verbatim, so the learner prompt shrinks to `/phase N` and paraphrase drift at kickoff is eliminated. The command
   guarantees the protocol is *received*, not that it is *followed*; telemetry remains the check.
2. Validation moved from the implementer to the main chat. The implementer has no Bash at all; the main runs the one
   validation command itself and diffs `git status --short` against a pre-delegation baseline, so scope checking no
   longer trusts the implementer's self-report and the old non-mechanical "terminal validation ordering" rule is
   retired.
3. The packet is the canonical requirement ledger: every atomic requirement has one ID and exact wording, with no ID
   ranges or paraphrase. Validation passes only when pytest passes, every ID has evidence, and no path outside the
   packet changed. A passing smoke test alone cannot conceal a dropped requirement.
4. The controller has a task-call state machine: it reads targets itself, makes one implementation delegation, then its
   next tool call must be pytest. A second fresh implementer is permitted only after pytest and an explicit failed
   requirement; it cannot replace an ambiguous but completed first task.
5. One repair is now allowed: exactly one delegation to a *fresh* implementer child carrying only implicated file names
   and roles, failed requirement IDs with expected and observed evidence, the required fix, and pytest output when
   pytest failed — never file contents, which would risk truncation under the model's output cap. The repair child reads
   the named files itself and rewrites complete files, so the edit-anchor (`oldString`) failure mode never applies.
6. The project build agent can call only `@implementer1a`; `@explore`, `@general`, and any other subagent are denied by
   the project `opencode.jsonc`. This makes the two-agent boundary enforceable instead of relying solely on prose.
7. The implementer's permissions are default-deny: every tool is denied unless explicitly allowed, including any tool an
   IDE client injects. Reads and writes are allowed everywhere except `specs/*` — the implementer structurally cannot
   consult the roadmap and improvise scope — its entire knowledge of the phase is the packet.
8. The controller is bounded: a step cap on the primary agent converts runaway drift into visible failure.
9. The Gemma model entries raise `limit.output` to 4096 so packets and coverage matrices are not truncated mid-message;
   packets must still stay terse and never inline file contents.
10. The command's first line tells the main to refuse to run in a chat with prior phase work. This is model-enforced, but
   it fails visibly to the learner instead of silently degrading isolation.
