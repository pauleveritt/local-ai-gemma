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

1. *Phase-local scope*. `@implementer1` receives one phase, the project specifications, and one validation command
   rather than an open-ended request.

2. *Fresh, single-purpose implementer*. A new @implementer1 has one job: implement one scoped phase. It avoids the
   parent’s accumulated context and prevents planning, design, and broad exploration from consuming the small model’s
   budget.

3. *One validation path and hard discovery boundaries*. The only permitted Bash command is the specified validation
   command, preventing recursive listings, environment activation, and other dives into `.venv`. `glob` is also
   disabled, so an incomplete packet fails visibly instead of triggering broad repository discovery. The agent reports
   the exact result and does not diagnose or repair after validation. This baseline exposes failures without starting a
   repair loop; it is not independent verification.

Notes:

a. Even though we give explicit instructions (e.g. the parent shouldn't run pytest), sometimes these get ignored.

b. Make sure to replace the `uv` part (including the use of `pyproject.toml`) with regular venv/pip use if that's your
setup.

c. We need to do each phase in a new parent chat. We'll tackle that with an orchestrator in Lesson 12.

```markdown
Read @specs/mission.md, @specs/tech-stack.md, and @specs/roadmap.md. Run only Phase N.

Read the phase's target files, then delegate this phase exactly once to a fresh `@implementer1` subagent with a compact
packet of repo-relative paths, not file contents: allowed files (new/shared), required changes, and exact behavior/tests
to preserve. Give one acceptance path, not alternatives. Do not modify phase files or use another agent.

Supply this validation command verbatim, with no other commands: `uv run --frozen python -m pytest tests/`.

After it returns, use only `read` on the reported changed files. Do not use Bash, glob, task, edit, or write. Report the
exact validation result, files changed, and only critical contract violations: missing required strings, routes,
imports, or unexpected files.
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