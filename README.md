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

Do not change dependencies between minimum, medium, and maximum. The specification and `uv.lock` are part of the
experiment; changing versions after a run makes the comparison invalid.

## New sections

- Simple version (Kostia) and bigger version (Isabel)
- Gemma 12, 26, DeepSeek Flash
- Explain why SLMs need so much help
- Qwen as big brain
- Options for maxiumum
    - LSP, RTK, Context7, caveman, speculative decoding, AFM
    - More subagents: validator, researcher (Context7), planner (roadmap)
    -

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
    "output": 2048,
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
- `output`: `2048` is enough for routine implementation while limiting runaway reasoning and repair loops.
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

1. *Phase-local, contract-complete scope*. The parent reads every shared target
   directly, then gives `@implementer1` one phase's requirements, named files,
   exact preservation requirements, and one validation command rather than an
   open-ended request.

2. *Fresh, single-purpose implementer*. A new @implementer1 has one job: implement one scoped phase. It avoids the
   parent’s accumulated context and prevents planning, design, and broad exploration from consuming the small model’s
   budget.

3. *One validation path and hard discovery boundaries*. The only permitted Bash
   command is the direct-venv validation command, preventing recursive listings,
   environment activation, and other dives into `.venv`. `glob` is also disabled,
   so an incomplete packet fails visibly instead of triggering broad repository
   discovery. The agent reports the exact result and does not diagnose or repair
   after validation. Treat the requested terminal ordering as a policy to inspect
   in telemetry, not as a mechanical guarantee; the Bash allowlist does not stop
   a later write tool call.

Notes:

a. Model instructions can still be ignored. Use telemetry to see what actually
happened before adding another rule.

b. Ensure `.venv/bin/python -m pytest tests/` matches the implementer's Bash
allowlist. Pointing directly at the virtual environment works whether or not the
project uses `uv`.

c. Plain Minimum works best from a fresh parent chat per phase. Minimum Plus
below also creates a fresh phase runner for every invocation, but a fresh
parent chat remains the strongest isolation.

d. These constraints came from observed potholes. Keep the prompt only as strict
as the telemetry evidence requires.

```markdown
Read @specs/mission.md, @specs/tech-stack.md, and @specs/roadmap.md. Run only Phase N.

Read the phase's target files, then delegate this phase exactly once to a fresh `@implementer1` subagent with a compact,
self-contained packet: repo-relative writable paths, complete required final state, and exact behavior/tests to
preserve. Do not refer the child to specification files or include file contents.
Do not provide complete files, complete functions, code blocks, pseudocode, or line-by-line implementations. Include
exact literals, imports, route signatures, API constraints, test semantics, and preserved behavior when they are
contract requirements.

Include this exact instruction: "For every writable file, use `write` with its complete final content; never use
`edit`." Do not modify phase files or use another agent.

Tell the child this is its final tool call and it must stop whether it passes or fails:
`.venv/bin/python -m pytest tests/`.

After it returns, use only `read` on the reported changed files. Do not use Bash, glob, task, edit, or write. Report the
exact validation result, files changed, and only critical contract violations: missing required strings, routes,
imports, or unexpected files.
```

### Minimum Plus

Use this when you want the same phase-local implementation context with a much
shorter kickoff prompt. `@implementer1a` is a fresh, self-contained phase
runner: it reads the local specifications and existing targets, implements one
phase, and runs the direct-venv test command. Its OpenCode permissions deny
delegation, `edit`, and broad discovery, and allow only the direct-venv test
command through Bash. It uses complete-file `write` operations and direct reads.

This removes the handoff packet and nested orchestration layer. The tradeoff is
deliberate: the phase runner validates its own work, so there is no separate
agent independently inspecting the result. Use the longer Minimum workflow
above when an independently constructed packet and parent-side inspection are
more important than a short prompt.

Use your normal primary agent. A fresh main chat per phase remains the most
isolated setup, but every `@implementer1a` invocation creates a fresh child even
when you reuse a longer-running main chat.

```markdown
@implementer1a Run Phase N.
```

### Medium prompt

Use the project `orchestrator2` as the primary agent. It prepares the handoff for a write-only `@implementer2`,
validates the result independently, and may send one exact failure to one fresh repair child. Both roles use Gemma 4 12B
so the orchestrator is deliberately procedural rather than a general code reviewer.

The benefits over minimum:

1. *A reusable orchestration contract*. Packet construction, validation, changed-file checks, and stopping rules live in
   `orchestrator2`, leaving the kickoff prompt small.
2. *Independent evidence*. The orchestrator runs pytest and checks the changed files instead of trusting the implementer
   report.
3. *Fresh-context repair*. A failed check gets at most one new `@implementer2` with the exact failure and current file
   state. The original child is never resumed.

Start a new chat for each phase, select `orchestrator2`, and enter:

```markdown
Run Phase N from @specs/roadmap.md.
```

The one-repair rule is still model-enforced; the 16-step cap is the mechanical circuit breaker. Telemetry must show
whether Gemma follows that boundary.

Possibilities

- Context7
- Fix at the end
- Make sure context is "cleared" between runs
    - Explain that context accumulates in the main chat but not in the implementer
    - Or, perhaps we want that context to come in
- Investigate a simpler roadmap and the orchestrator is able to convert to details
