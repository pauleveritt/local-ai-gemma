# How To Keep Local AI Out Of The Ditch

The idea of this project is to show how to steer Local AI agent/model towards better/faster outcomes.

## New sections

- Simple version (Kostia) and bigger version (Isabel)
- Gemma 12, 26, DeepSeek Flash
- Explain why SLMs need so much help
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

Nothing matters except evidence. Our hunches about why an agent was slow or why a small model stumbled are usually wrong
until the session telemetry proves them. OpenCode records the useful evidence: which model and agent actually ran,
parent and child timing, turns, context growth, KV-cache reads, tool calls, and large tool outputs. That evidence
explains slowness especially well. A small model needs a lot of help eliminating unnecessary exploration, retries, and
context pollution; telemetry shows where that help is needed.

The repository includes the Codex skill
`.codex/skills/opencode-telemetry`. It automates the mechanical collection and leaves interpretation to an
evidence-based report. The skill works on macOS, Windows, and Linux. Its bundled Python collector:

- Locates the OpenCode SQLite database using `OPENCODE_DATA_DIR`, XDG paths, macOS application-data paths, or Windows
  `LOCALAPPDATA`/`APPDATA` paths.
- Follows a parent session's child sessions and reports model, agent, lifetime, active message span, turns, tool calls,
  input/output tokens, and context.
- Separates fresh input from `cache_read` tokens, so LM Studio and oMLX metrics are not incorrectly compared as if they
  used the same accounting.
- Flags recursive listings, protected-directory traversal, and unusually large tool output that can explain context
  growth and slowness.
- Reads the database read-only. It does not start OpenCode or change project files.

### Run and analyze

1. Run the phase prompt in OpenCode. Let the run finish, or record the session ID if it fails. The session ID is
   available from OpenCode's session list.
2. In Codex or OpenCode, invoke the `opencode-telemetry` skill and provide the session ID. Ask it to collect the
   telemetry, inspect the relevant files and validation output, and report metrics and quality.
3. The collector can also be run directly:

   ```bash
   # macOS/Linux
   python3 .codex/skills/opencode-telemetry/scripts/collect_telemetry.py --list
   python3 .codex/skills/opencode-telemetry/scripts/collect_telemetry.py --session ses_...

   # Windows
   py -3 .codex/skills/opencode-telemetry/scripts/collect_telemetry.py --list
   py -3 .codex/skills/opencode-telemetry/scripts/collect_telemetry.py --session ses_...
   ```

The report must distinguish parent lifetime from active work, because a reused chat can contain idle gaps. It must also
distinguish main-agent time from nested implementer time, and treat nonzero KV-cache reads as evidence of reuse, not
proof of a speedup. Quality claims require the actual test result and a source/spec inspection, not the agent's final
assertion that everything passed.

## Prompts

### Minimum prompt

Use the project `@implementer1` subagent. Start a new chat for each phase and replace `N` with its number.

The benefits:

1. *Complete, narrow handoff packet*. The child receives only allowed files, exact strings/behavior, and one validation
   command. This removes the most costly decisions: what to inspect, what to change, and how to judge success.

2. *Fresh, single-purpose implementer*. A new @implementer1 has one job: implement one scoped phase. It avoids the
   parent’s accumulated context and prevents planning, design, and broad exploration from consuming the small model’s
   budget.

3. *One validation path and a stop boundary*. The child runs one specified command and reports its exact result. The
   parent reviews but does not repair. This baseline exposes failures without starting a repair loop; it is not yet
   independent verification.

Here's the prompt to enter which triggers `implementer1`:

```markdown
Read @specs/mission.md, @specs/tech-stack.md, and @specs/roadmap.md. Run only Phase N from the roadmap. Keep this chat
phase-local.

Parent: make a short task list, then delegate the whole phase once to a fresh @implementer1. Give it only the files it
may change, required strings and behavior, and validation command `.venv/bin/python -m pytest tests/`.

Tell the child to implement, validate, and report the exact result tersely. Do not fix code afterward; review and report
only critical mistakes. If @implementer1 fails to start, report the error and stop—do not use another agent.
```

### Medium prompt

Use the project `orchestrator2` as the primary agent. It prepares the handoff for a write-only `@implementer2`, validates
the result independently, and may send one exact failure to one fresh repair child. Both roles use Gemma 4 12B so the
orchestrator is deliberately procedural rather than a general code reviewer.

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

The one-repair rule is still model-enforced; the 16-step cap is the mechanical
circuit breaker. Telemetry must show whether Gemma follows that boundary.

### Lesson 3 in Claude Code

```
Look in @specs/mission.md and @specs/tech-stack.md for project details.
Look at the @specs/roadmap.md and:
- Implement each task one at a time from Phase 1 and Phase 2.

Do not fix anything after the subagent. Do a review and provide a list of critical mistakes.
```

### Lesson 4 in Claude Code

```
Look in @specs/mission.md and @specs/tech-stack.md for project details.
Look at the @specs/roadmap.md and:
- Implement Phase 1 using a **new spawned** @general subagent.
- Implement Phase 2 using a **new spawned** @general subagent.

Do not fix anything after the subagent. Do a review and provide a list of critical mistakes.
```

### Lesson 5 in Claude Code

```
Look in @specs/mission.md and @specs/tech-stack.md for project details.
Look at the @specs/roadmap.md and:
- Implement Phase 1 using a **new spawned** Haiku subagent.
- Implement Phase 2 using a **new spawned** Haiku subagent.

Do not fix anything after the subagent. Do a review and provide a list of critical mistakes.
```

### Lesson 7 in OpenCode

```
Look in @specs/mission.md and @specs/tech-stack.md for project details.
Look at the @specs/roadmap.md and:
- Implement Phase 1
- Implement Phase 2

Do not fix anything after the subagent. Do a review and provide a list of critical mistakes.
```

### Lesson 8 in OpenCode

```
Look in @specs/mission.md and @specs/tech-stack.md for project details.
Look at the @specs/roadmap.md and:
- Implement Phase 1 using a *new spawned* general subagent.
- Implement Phase 2 using a *new spawned* general subagent.


Do not fix anything after the subagent. Do a review and provide a list of critical mistakes.
```

### Lesson 9 in OpenCode

```
Look in @specs/mission.md and @specs/tech-stack.md for project details.
Look at the @specs/roadmap.md and:
- Generate Phase 1 spec for the implementer subagent with task list
- Spawn one new implementer subagent at a time and delegate implementation of each task in Phase 1 spec list. New implementer subagent to each task.

Then do the same steps for the Phase 2.

- Do not write the full code file for/instead of subagents, only suggest snippets.
- Do not make fixes after subagents.
- Do a review and provide a list of critical mistakes.
```

#### Setup OpenCode Agent

This step should be run before running the prompt. It configures the project to have an OpenCode subagent named
`implementer`.

```
Create an "Implementer" subagent:
- This subagent should use the `lmstudio/gemma-4-12b-it-mlx` model
- The main goal of this agent is to generate code and implement tasks delegated to it
```

### Lesson 11 in OpenCode

Run one phase per new chat. Replace `N` with `1`, `2`, or `3`.

```markdown
Look in @specs/mission.md, @specs/tech-stack.md, and @specs/roadmap.md. Run only Phase N from the roadmap. Keep this
chat phase-local.

Parent: read the phase, then use the task tool once with a fresh spawned @implementer subagent. Send the child a tiny
packet: repo-relative files only, exact user-visible strings, and validation command
`.venv/bin/python -m pytest tests/`. Tell the child to implement directly, make file changes before its final response,
and keep that final response terse and factual.

For tiny generated files, tell the child to read once and then write the complete final file. For 303 redirect tests,
tell the child that TestClient follows redirects by default and to use `follow_redirects=False`.

After the child returns, do not fix code. Review and list only critical mistakes. If the @implementer task fails to
start, report the exact error and stop. Do not retry with @general or any other subagent.
```

### Lesson 12 in OpenCode
