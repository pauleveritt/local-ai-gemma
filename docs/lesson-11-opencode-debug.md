# Lesson 11 OpenCode Debug Notes

This file records the investigation into the Lesson 11 Phase 1 OpenCode run and the fixes made afterward.

## Session

- Parent session: `ses_0bcee48a8ffe37BS5AqvuxBmd9`
- Parent title: `Executing Lesson 11 prompt`
- Parent directory: `/Users/pauleveritt/PycharmProjects/dlai-local-ai-course`
- Child implementer session: `ses_0bcebb748ffeb8SODa3Qr7Jz5d`
- Child title: `Implement Phase 1 Home Page (@implementer subagent)`
- Child model: `lmstudio/mellum2-12b-a2.5b-thinking`

## Where To Look

- Active OpenCode state is under `/Users/pauleveritt/.local/share/opencode`.
- Active global OpenCode config is `/Users/pauleveritt/.config/opencode/opencode.jsonc`.
- Do not use `/Users/pauleveritt/.config/opencode-jetbrains`; it is stale.
- Query the live OpenCode database directly when needed; copying the database to avoid locks is not required.

## Diagnosing From Codex

When we diagnose OpenCode behavior from Codex, the working rule is to trust live runtime state over stale snapshots.

- Use the local OpenCode checkout at `/Users/pauleveritt/PycharmProjects/opencode` when you need source-level answers about agent resolution, task dispatch, or tool behavior.
- Use the live OpenCode database and telemetry under `/Users/pauleveritt/.local/share/opencode` for session evidence.
- Use the LM Studio model bundle under `/Users/pauleveritt/.lmstudio/models/...` for model-specific defaults such as load context, temperature, `top_p`, and `top_k`.
- Use `/Users/pauleveritt/.lmstudio/settings.json` for global LM Studio defaults such as the app-wide context length.
- Use `/Users/pauleveritt/.lmstudio/server-logs/` for backend request timing and model-traffic evidence when you need to confirm that LM Studio actually received a request.
- Use `/Users/pauleveritt/.lmstudio/conversations/` when you need the conversation-side record of a model run, including per-message token counts and generation metadata.
- If the model path looks wrong, inspect the model bundle under `/Users/pauleveritt/.lmstudio/models/JetBrains/mellum2-12b-a2.5b-thinking/model.yaml` first, then compare it with the live logs.
- Prefer direct shell commands for debugging so the output stays compact and readable in Codex.

Typical investigation sequence:

```bash
opencode debug config
opencode debug agent implementer
opencode session list --format json --max-count 50
opencode export <session-id>
sqlite3 /Users/pauleveritt/.local/share/opencode/opencode.db "select * from session limit 5;"
```

The important habit is to reconcile all three layers before drawing conclusions:

1. What OpenCode says the config resolves to.
2. What the session telemetry actually shows.
3. What the local source code says the task and agent resolution logic should do.

## Gemma 4 Notes

Gemma 4 behaves best in this course when the parent agent does the reading and the child agent does the writing.

- The Gemma 4 model bundle reports `max_position_embeddings: 262144`, so the model itself is not the limiting factor for Phase 1.
- The Gemma 4 LM Studio generation defaults are `temperature: 1.0`, `top_k: 64`, `top_p: 0.95`, and `do_sample: true`.
- Our OpenCode overlay intentionally narrows that to `context: 40960`, `input: 32768`, and `output: 2048` to keep small coding runs away from compaction without reopening the old zero-budget problem.
- Use the same shared Gemma profile whether Gemma is the orchestrator or the implementer: `temperature: 0.2`, `top_p: 0.9`, and the model default `top_k: 64`.
- Use `steps: 16` as the single shared compromise when the same configuration must support both roles. If role-specific limits are possible, use `10–12` steps for a write-only implementer and `16–20` for a main agent that also orchestrates.
- Historical Phase 3 runs used all `20` steps while trapped in edit retries, so increasing the cap is not a reliable fix for Gemma drift; keep the packet small and phase-local.
- Keep the parent as the orchestrator. Do not add a separate orchestrator subagent just to clear context between phases; if a small generated file needs attention, have the parent re-read it directly.
- A stronger long-run pattern may be an `@orchestrator` agent that stays in one chat, reads the specs once, delegates each phase to a fresh `@implementer`, reviews the result, and sends back only narrowly scoped repair instructions when needed.
- Keep the implementer prompt short and exact. The parent should send only the required files, required strings, and validation command, and should not forward prior phase summaries unless the next phase truly depends on them.
- For redirect assertions in tests, use `follow_redirects=False` so the raw status code is checked instead of the final response.
- For small files that are already fully read, prefer one full-file `write` over repeated narrow `edit` calls when a repair is needed.
- The latest edit-loop evidence says this is not just a retry policy problem. Gemma repeatedly tried to call `edit` with an empty or stale `oldString`, so the better default for tiny files is to rewrite the whole file after one read instead of trying to preserve a diff anchor.
- Phase 3 hit the full `20`-step cap while still trapped in `edit` retries. That means more steps would not have fixed the failure mode by themselves; the tool choice needs to change first.
- The parent packet should stop framing these files as exact-match edit targets. For tiny generated files, the child should be told to read once and then write the complete final file content.
- Phase 2 is still the hotspot for context growth. Keep that packet especially lean and phase-local: only the files that actually change, the exact strings that must survive, and the one validation command the child needs.
- The latest Phase 2/3 telemetry says the main regression is context growth, not tool churn. The child tool-call count stayed flat while average context jumped from `6998.5` to `12783.1` total tokens and peak context jumped from `9709` to `34091`.
- The latest Phase 3 run also showed that the redirect assertion failure was a test-semantic issue, not a route issue. The child should be told that `TestClient` follows redirects by default when validating 303 behavior.
- The latest Phase 3 run also suggests that when a tiny file only needs a semantic fix, a full-file rewrite is usually a better move than one more anchor-based edit.
- The repeated `<|channel>thought` markers still appear in telemetry, but we are treating that as template behavior outside this round of prompt changes.
- If the model wants a todo list, the tool name is `todowrite`, not `todo`.
- If OpenCode emits an `invalid` tool, it means the model named a tool incorrectly or supplied malformed arguments, not that the session is broken.

## Latest Phase 2/3 Telemetry

The newest run makes the tradeoff clearer:

- Parent session: `ses_0b75b3b84ffeYQQP30M5e5t4hl`
- Phase 1 child: `ses_0b75ae7adffe0F1sQ6BrGsCmFk`
- Phase 2 child: `ses_0b75a233cffeHkZ6XcLim8mrJ3`
- Phase 3 child: `ses_0b757b5b7ffeB2imKMaRP1Bjne`

Compared with the previous run:

- Parent duration rose from `280.732s` to `386.149s`.
- Child duration rose from `200.990s` to `320.638s`.
- Child input tokens rose from `300935` to `562457`.
- Child output tokens rose from `6033` to `6984`.
- Child tool calls stayed flat at `40`.
- Average child context rose from `6998.5` to `12783.1`.
- Peak child context rose from `9709` to `34091`.
- Phase step counts were `7`, `17`, and `20`, so Phase 3 hit the cap exactly.

Conclusion: the model is no longer mainly failing by tool churn. The current bottleneck is packet size and accumulated child context, with Phase 3 spending its budget on a semantic redirect trap rather than on actual implementation work.

## Current State / Known Good

As of the latest verification pass, these are the facts worth preserving:

- The lesson prompt is configured for `deepseek/deepseek-v4-flash` as the main agent model.
- The project `implementer` agent resolves to `lmstudio/mellum2-12b-a2.5b-thinking`.
- The `implementer` agent has `skill: false` and the global OpenCode config has `lsp: false`.
- LM Studio Mellum2 currently shows per-model defaults of `contextLength: 50000`, `temperature: 0.6`, `top_p: 0.95`, and `top_k: 20`.
- LM Studio global `defaultContextLength` is `8192`.
- LM Studio server logs are the best source for confirming actual request traffic and stream completion timing.
- LM Studio conversation JSON is the best source for inspecting per-run metadata, token counts, sender IDs, and model identifiers.
- The model-specific YAML at `/Users/pauleveritt/.lmstudio/models/JetBrains/mellum2-12b-a2.5b-thinking/model.yaml` is where the per-model load and sampling defaults live.
- The generated lesson app now uses `TemplateResponse(request, "home.html")`.
- The generated test now imports `TestClient` from `starlette.testclient`.
- The lesson test suite passes with `.venv/bin/python -m pytest tests/`.
- `pytest -q` is not usable in this repo through the shell wrapper used in earlier runs; use the virtualenv command above instead.
- One FastAPI warning remains about `asyncio.iscoroutinefunction`.
- In the latest Phase 1/2 run, the `implementer` child resolved to `omlx/mellum2-thinking-mlx-q8` instead of the expected LM Studio `lmstudio/mellum2-12b-a2.5b-thinking`. That mismatch is now a live lead for config precedence or agent-resolution debugging.
- The latest Phase 2 child was cancelled after reaching 100 messages; the trace showed file-writing drift and garbled output near the end, but not a completed pytest repair loop.
- That run suggests the main issue is still generation corruption / wandering during implementation, not a permissions problem or a failed pytest self-repair cycle.

Useful commands:

```bash
rtk opencode session list --format json --max-count 50
rtk opencode export ses_0bcee48a8ffe37BS5AqvuxBmd9
rtk opencode export ses_0bcebb748ffeb8SODa3Qr7Jz5d
rtk proxy sqlite3 /Users/pauleveritt/.local/share/opencode/opencode.db "select * from session limit 5;"
```

## Evidence

The relevant child implementer session did not run `pytest`, Python, `.venv`, or shell commands.

Observed tool sequence:

```text
skill brainstorming
glob/read project files
skill writing-plans
question -> error: user dismissed this question
write -> app.py
```

The child session wrote Markdown/design prose into `app.py`. That explains the Pyrefly diagnostics: `app.py` was not valid Python.

## Root Cause

The original hypothesis was that the implementer entered a pytest self-correction loop and repeatedly rewrote `app.py` after failures. That remains a plausible future risk, but it was not what happened in this run.

The actual root cause for this run was that the implementer agent was hijacked by process-oriented skills. Instead of directly implementing Phase 1, it invoked brainstorming and planning behavior, then wrote design prose into an implementation file.

## Fixes Applied

### Implementer Agent Guardrails

Updated `.opencode/agents/implementer.md` so the implementer:

- Implements directly instead of invoking brainstorming, planning, or design-spec skills unless explicitly asked.
- Validates with the project virtual environment using `.venv/bin/python -m pytest tests/`.
- Does not rely on shell activation.
- Reports a missing `.venv/bin/python` instead of falling back to system Python.
- Makes at most two focused test-fix attempts before stopping and reporting the exact failure.

### LSP Disabled

Updated `/Users/pauleveritt/.config/opencode/opencode.jsonc` so configured LSP servers are disabled:

```json
"lsp": {
  "pyrefly": {
    "disabled": true
  },
  "pyright": {
    "disabled": true
  }
}
```

This prevents Pyrefly LSP diagnostics from participating in future OpenCode sessions while we debug the agent behavior.

## Current Working Theory

For Lesson 11 Phase 1, the most important fixes are:

- Keep the implementer focused on code generation rather than planning workflows.
- Force validation through the repo virtual environment.
- Limit repair loops so repeated failures are surfaced instead of converted into broad file rewrites.
- Disable LSP support during this debugging pass so diagnostics do not add confusing feedback loops.
- If the child model continues to resolve to `omlx/mellum2-thinking-mlx-q8`, inspect OpenCode agent resolution and config precedence before treating the run as an LM Studio/Mellum2 issue.

Latest Phase 1 telemetry also showed a path hygiene problem: the child repeatedly tried to access `/Users/pauveritt/PycharmProjects/dlai-local-ai-course` instead of the real workspace `/Users/pauleveritt/PycharmProjects/dlai-local-ai-course`. That typo caused `FileSystem.makeDirectory`, `read`, `glob`, and `bash` calls to fail against a nonexistent path, which explains why the run stalled after writing only `app.py`. This is a prompt/agent-path issue, not a need for extra permission.

After that, we moved the implementer to a harder boundary by denying `external_directory` at the agent level. The intent is to turn invented absolute paths into immediate failures instead of permission prompts, so the model gets clearer feedback when it drifts off the workspace.

The main lesson prompt should stay on repo-relative file names for the same reason. Absolute paths add more path-shaped tokens to the context and make it easier for Mellum2 to garble the workspace root when it constructs tool calls.

The newest Phase 1 child session also showed a different failure mode: it read the repo and then returned a prose-only "implementation" with no `write` or `edit` tool calls at all. The session summary shows `files: 0` and `additions: 0`, so the review text about `uvicron`/template contents was never grounded in actual files. That means the implementer prompt needs a harder "must create files before final response" rule, not just a reminder to be careful.

## Retry: Correct Main Agent Model

After correcting the main agent model, the newest observed parent session was:

- Parent session: `ses_0bcd30c50ffeG74tfBSVd2pLiF`
- Parent title: `Read and execute Lesson 11 prompt`
- Parent agent/model: `build`, `deepseek/deepseek-v4-flash`

That run did use the corrected main agent model, but the first required `task` call still failed because OpenCode resolved the implementer child to an unavailable `openrouter/deepseek-v4-flash` model:

```text
Model not found: openrouter/deepseek-v4-flash. Did you mean: deepseek/deepseek-v4-flash?
```

The failed intended child session was:

- Child session: `ses_0bcd290b1ffejo2VBwl7RE45nt`
- Child title: `Implement Phase 1 - Home Page (@implementer subagent)`
- Child agent/model: `implementer`, `openrouter/deepseek-v4-flash`
- Tokens: zero input, zero output, zero reasoning

This child only recorded the user prompt. It did not produce assistant output or run tools.

The main agent then retried with a `general` subagent:

- Child session: `ses_0bcd1e033ffes6OcfIIeLzFgh9`
- Child title: `Implement Phase 1 - Home Page (@general subagent)`
- Child agent/model: `general`, `deepseek/deepseek-v4-flash`

That fallback subagent created:

- `app.py`
- `templates/base.html`
- `templates/home.html`
- `tests/test_app.py`

It validated with:

```bash
/Users/pauleveritt/PycharmProjects/dlai-local-ai-course/.venv/bin/python -m pytest tests/test_app.py -v
```

The subagent test passed. It then updated `TemplateResponse` to the newer request-first call shape and reran the same test successfully.

The main agent also ran its own review commands afterward. One of those used `uv run pytest tests/test_app.py -v`, which failed with `ModuleNotFoundError: No module named 'app'`, while a workaround command using `uv run python -m pytest tests/test_app.py -v -c /dev/null` passed. This is separate from the subagent's validation, which used the virtual environment directly and passed.

### Retry Conclusion

The corrected main-agent model solved only one layer. The run still was not a valid Lesson 11 execution because:

- The required `@implementer` delegation failed before execution after resolving to `openrouter/deepseek-v4-flash`.
- The main agent delegated a second time to `@general`, violating the prompt's "delegate exactly once" requirement.
- The `@general` fallback produced working code, but it is not evidence that the configured `@implementer` path works.

### Corrected Interpretation

The implementer should not be DeepSeek Flash. The intended split is:

- Main agent: `deepseek/deepseek-v4-flash`
- Implementer subagent: `lmstudio/mellum2-12b-a2.5b-thinking`

The current `.opencode/agents/implementer.md` should therefore keep:

```yaml
model: lmstudio/mellum2-12b-a2.5b-thinking
```

The next valid retry should be a fresh Lesson 11 run where the main `build` agent uses `deepseek/deepseek-v4-flash` and the single `task` call creates an `@implementer` child using `lmstudio/mellum2-12b-a2.5b-thinking`.

If OpenCode still resolves the implementer child to `openrouter/deepseek-v4-flash`, the next root-cause target is agent resolution/config precedence rather than changing the implementer model to DeepSeek.

## Follow-up Prompt: Why OpenRouter?

The parent session later received this user prompt:

```text
Why did you choose `openrouter/deepseek-v4-flash`
```

This prompt appears in:

- Session: `ses_0bcd30c50ffeG74tfBSVd2pLiF`
- Message: `msg_f432df223001aVwi87kLJD9GOe`
- Time: `1783538512454`
- Parent agent/model: `build`, `deepseek/deepseek-v4-flash`

Telemetry after that prompt shows the main agent understood that `openrouter/deepseek-v4-flash` was not available and that the configured available model was `deepseek/deepseek-v4-flash`.

Its reasoning said, in effect:

- The old Lesson 9 setup text mentioned `openrouter/deepseek-v4-flash`.
- The task error said that model was not found.
- The configured available model was `deepseek/deepseek-v4-flash`.
- It should try again with the correct model.

However, the `task` tool call does not show a per-call model field. The only model-affecting control the main agent used was `subagent_type`. After the user prompt, it made this second task call:

```json
{
  "description": "Implement Phase 1 - Home Page",
  "subagent_type": "general"
}
```

That created:

- Child session: `ses_0bcd1e033ffes6OcfIIeLzFgh9`
- Child title: `Implement Phase 1 - Home Page (@general subagent)`
- Child agent/model: `general`, `deepseek/deepseek-v4-flash`

So after the prompt, the session did stay on the same model family as the chat itself, but only by switching from `@implementer` to `@general`. That was the wrong repair because Lesson 11 required exactly one delegation to `@implementer`.

### Follow-up Conclusion

The after-prompt failure was not continued use of OpenRouter. It was an overcorrection:

- Correct: it recognized `deepseek/deepseek-v4-flash` as the available main/chat model.
- Correct: the fallback child used `deepseek/deepseek-v4-flash`.
- Incorrect: it changed `subagent_type` from `implementer` to `general`.
- Incorrect: it performed a second delegation after the failed first delegation.
- Missing step: it did not inspect or resolve the project `@implementer` agent configuration before retrying.

The right behavior after the user asked why OpenRouter was used would have been to stop and report that `@implementer` was resolving to an unavailable model, not to silently substitute `@general`.

## LM Studio Log Reconciliation

LM Studio logs do show real Mellum2 traffic on July 8, but the timestamps align with the earlier `ses_0bcee48a8ffe37BS5AqvuxBmd9` run, not the later `Why did you choose openrouter/deepseek-v4-flash` follow-up.

OpenCode timestamp conversion:

```text
ses_0bcee48a8ffe37BS5AqvuxBmd9 parent start       2026-07-08 14:51:02 EDT
ses_0bcede68effe3CFwj9x1OaCt02 implementer start  2026-07-08 14:51:27 EDT
ses_0bcede68effe3CFwj9x1OaCt02 implementer end    2026-07-08 14:52:51 EDT
ses_0bcebb748ffeb8SODa3Qr7Jz5d implementer start  2026-07-08 14:53:50 EDT
ses_0bcebb748ffeb8SODa3Qr7Jz5d implementer end    2026-07-08 14:54:35 EDT
ses_0bcd30c50ffeG74tfBSVd2pLiF parent start       2026-07-08 15:20:47 EDT
Why OpenRouter prompt                                 2026-07-08 15:21:52 EDT
ses_0bcd1e033ffes6OcfIIeLzFgh9 general start       2026-07-08 15:22:04 EDT
ses_0bcd1e033ffes6OcfIIeLzFgh9 general end         2026-07-08 15:22:59 EDT
```

The LM Studio log at `/Users/pauleveritt/.lmstudio/server-logs/2026-07/2026-07-08.1.log` contains Mellum2 activity at the same time as the earlier implementer sessions:

```text
2026-07-08 14:51:27 mellum2-12b-a2.5b-thinking Running chat completion
2026-07-08 14:52:53 mellum2-12b-a2.5b-thinking Client disconnected / finished streaming
2026-07-08 14:53:50 mellum2-12b-a2.5b-thinking Running chat completion
2026-07-08 14:54:08 mellum2-12b-a2.5b-thinking Finished streaming response
```

That confirms:

- The earlier `@implementer` sessions really did hit LM Studio/Mellum2.
- The first earlier Mellum2 implementer session was the one with very high token counts and repeated requests.
- The later `Why OpenRouter?` session did not correspond to those LM Studio lines.

Important detail: the LM Studio log file's modification time was `2026-07-08 14:54:08`, before the later parent session started at `15:20:47`. Therefore, the LM Studio log cannot show requests from the later post-prompt retry unless there is another log file or LM Studio did not flush/update this one.

### Reconciled Interpretation

Both observations are true:

- LM Studio did receive Mellum2 requests during the earlier Lesson 11 attempt.
- The later post-prompt retry did not use Mellum2 according to OpenCode telemetry; it created a `@general` child using `deepseek/deepseek-v4-flash`.

So the bug shifted over time:

- Earlier run: `@implementer` used Mellum2, but behavior was bad and loop-like.
- Later run: main agent used DeepSeek Flash, then the intended `@implementer` call failed before execution due to `openrouter/deepseek-v4-flash`, and the main agent incorrectly substituted `@general`.

## Restarted Lesson 11 Run: Phase 2 Mellum2 Loop

After restarting OpenCode and sending:

```text
From @README.md read and execute the prompt in Lesson 11.

If the @implementer task fails to start, stop and report the exact error. Do not retry with @general or any other subagent.
```

the run finally used the intended model split:

- Parent session: `ses_0bcbcf9ebffeSZfaYb9My8VVfY`
- Parent title: `Execute Lesson 11 prompt from README`
- Parent agent/model: `build`, `deepseek/deepseek-v4-flash`
- Child session: `ses_0bcbc3f2affe3uAkc5Mw8F2WTM`
- Child title: `Implement Phase 2 Complaints (@implementer subagent)`
- Child agent/model: `implementer`, `lmstudio/mellum2-12b-a2.5b-thinking`
- Child tokens: `367053` input, `4752` output, `863` reasoning

This confirms the latest failure was not the old `openrouter/deepseek-v4-flash` model-resolution failure. The `@implementer` child started correctly and used LM Studio/Mellum2.

### Tool Pattern

The child session had:

- `26` reasoning parts
- `26` tool parts
- `11` patch parts
- `3` completed `bash` tool calls
- `9` completed `edit` calls
- `6` failed `edit` calls
- `1` failed `read` call
- `2` completed `write` calls

The initial implementation created or modified:

- `app.py`
- `models.py`
- `templates/complaints.html`
- `tests/test_app.py`

The first `ruff check .` did run, but OpenCode recorded it as a completed bash tool call even though the command output contained diagnostics.

Initial `ruff` diagnostics:

```text
app.py:18:1 E402 Module level import not at top of file: from models import complaints
app.py:19:1 E402 Module level import not at top of file: from fastapi import Form, RedirectResponse
app.py:20:1 E402 Module level import not at top of file: from datetime import datetime
app.py:20:22 F401 datetime imported but unused
app.py:24:23 F821 Complaint undefined
models.py:3:26 F401 Any imported but unused
```

Those diagnostics were legitimate. The first implementation put imports below route functions, imported an unused `datetime`, used `Complaint` without importing it in the relevant scope, and imported unused `Any`.

### How The Loop Formed

The loop formed during repair, not during initial implementation.

The implementer tried to fix `app.py` with incremental string edits. The first repair pass made the file worse by producing duplicate imports/routes and introducing typo-level damage:

- `TemplateRequest` instead of `TemplateResponse`
- `compaints` instead of `complaints`
- duplicate `GET /complaints`
- duplicate lower imports

After another `ruff check .`, diagnostics got worse:

```text
Complaint imported but unused
late imports still present
F811 redefinitions for complaints, Form, RedirectResponse, Complaint
Any still unused
```

After another attempted cleanup, the file was left with no top-level import for `complaints`, while both routes still referenced it:

```text
app.py:15:82 F821 complaints undefined
app.py:21:5 F821 complaints undefined
models.py:3:26 F401 Any imported but unused
```

At that point the implementer repeatedly attempted to remove a stale exact string:

```python
from models import complaints
from fastapi import Form, RedirectResponse
from datetime import datetime

@app.post("/complaints")
async def post_complaint(agent_name: str = Form(...), text: str = Form(...)):
    from models import Complaint
    complaints.append(Complaint(agent_name=agent_name, text=text))
    return RedirectResponse("/complaints", status_code=303)
```

but that string was no longer present in `app.py`, so the `edit` tool failed repeatedly with stale `oldString` context. The child then aborted with `MessageAbortedError` rather than returning a normal implementation summary.

Current observed file state after the abort:

- `app.py` references `complaints` but does not import `complaints`.
- `app.py` imports `Complaint` locally inside the POST route but not `complaints`.
- `app.py` imports `RedirectResponse` from `fastapi`, but the project environment raises `ImportError`; it should come from `fastapi.responses`.
- `models.py` imports unused `Any` and uses old-style `List`.
- `tests/test_app.py` contains code comments even though the task prompt said not to add comments.

### Revised Conclusion

The earlier high-level analysis was directionally right, but the precise root cause is narrower:

- This was not an `@implementer` model-resolution failure.
- This was not primarily a missing-venv pytest loop.
- This was a linter-triggered self-repair loop inside the Mellum2 implementer.

The failure sequence was:

1. The main agent correctly spawned one `@implementer` child.
2. The child correctly used `lmstudio/mellum2-12b-a2.5b-thinking`.
3. The child produced a plausible first implementation with several real lint/import mistakes.
4. The child ran bare `ruff check .`, not `.venv/bin/python -m ruff check .`.
5. The child tried to repair the lint failures through brittle exact-string edits.
6. The repair attempts changed the target file faster than the model re-grounded on it.
7. Repeated stale `oldString` edits created the loop and ended in an abort.

The current guardrail in `.opencode/agents/implementer.md` limits repeated test-fix attempts, but it does not yet address failed edit retries. A more targeted guardrail would be:

- After any failed `edit` caused by stale `oldString`, re-read the target file before retrying.
- After two failed edits against the same file or region, stop and report instead of trying a third edit.
- If a validation command is requested but is not available in `.venv`, report the environment mismatch instead of silently using a global tool.

### Venv / Ruff Nuance

The prompt told the implementer to use the virtual environment and also to run `ruff check`.

In this workspace, `.venv/bin/python -m ruff check .` currently fails because `ruff` is not installed in the virtual environment:

```text
No module named ruff
```

But bare `ruff check .` did run in the OpenCode child environment. That means there is a validation ambiguity:

- `pytest` should use `.venv/bin/python -m pytest`.
- `ruff check .` currently appears to rely on a global or tool-provided `ruff`, not the project virtual environment.

If the goal is reproducible agent validation, either install/configure `ruff` in the project environment or tell the implementer to report that `ruff` is unavailable in `.venv` instead of using bare global `ruff`.

### Current Local Validation

Running the project virtual environment test command now fails during test collection:

```bash
rtk .venv/bin/python -m pytest tests/
```

Observed error:

```text
ImportError: cannot import name 'RedirectResponse' from 'fastapi'
```

Running virtual-environment Ruff also fails because Ruff is not installed in `.venv`:

```bash
rtk .venv/bin/python -m ruff check .
```

Observed error:

```text
No module named ruff
```

Running bare Ruff does work, but reports the current lint state left by the aborted implementer:

```bash
rtk ruff check .
```

Observed diagnostics:

```text
app.py:15:82 F821 Undefined name `complaints`
app.py:21:5 F821 Undefined name `complaints`
models.py:3:26 F401 `typing.Any` imported but unused
```

## Course Toolchain Hardening

Course users should not be expected to have RTK, Ruff, ty, pyrefly, pyright, mypy, or other lint/type/LSP tools. The intended course validation path is pytest only:

```bash
.venv/bin/python -m pytest tests/
```

Applied hardening:

- Updated `README.md` Lesson 11 to say validation is pytest-only and to forbid lint/type/LSP tools.
- Updated `.opencode/agents/implementer.md` to forbid Ruff, ty, pyrefly, pyright, mypy, and other lint/type/LSP tools.
- Added a guardrail to avoid repeated skill loading during routine implementation.
- Added an edit-loop guardrail to `.opencode/agents/implementer.md`: re-read after stale edit failures, retry the same edit at most twice, then stop and report.
- Added a generic repair rule to `.opencode/agents/implementer.md`: fix the highest-signal validation or review issue first, using a narrow change that addresses the underlying pattern.
- Enforced `skill: false` in `.opencode/agents/implementer.md` so skills are disabled at the tool level, not just by instruction.
- Updated `/Users/pauleveritt/.config/opencode/opencode.jsonc` to set `lsp: false`.
- Updated `/Users/pauleveritt/.config/opencode/opencode.jsonc` to deny common lint/type/LSP shell commands while leaving the original broad permission setting commented for reference.
- Disabled the Superpowers plugin in `/Users/pauleveritt/.config/opencode/opencode.jsonc` so the `test-driven-development` skill is no longer available through the course runtime.

Validation:

```bash
rtk opencode debug config
rtk opencode debug agent implementer
```

OpenCode successfully parsed the config and resolved `implementer` with:

- `lsp: false`
- active bash deny rules for Ruff, ty, pyrefly, pyright, and mypy command patterns
- model `lmstudio/mellum2-12b-a2.5b-thinking`
- the updated pytest-only validation instructions
- a direct instruction not to load any skills during normal implementation

## Successful Lesson 11 Phase 1 Run

After disabling Superpowers and rerunning Lesson 11, the newest successful run was:

- Parent session: `ses_0bc9c2fcbffeG9wx2XD10h3T8o`
- Parent title: `Execute Lesson 11 prompt from README`
- Parent agent/model: `build`, `deepseek/deepseek-v4-flash`
- Child session: `ses_0bc9adfb0ffeqrK3r3UANQIVKi`
- Child title: `Implement Phase 1 Home Page (@implementer subagent)`
- Child agent/model: `implementer`, `lmstudio/mellum2-12b-a2.5b-thinking`

The flow was mostly correct:

- The parent used exactly one `task` call.
- The child used the intended Mellum2 LM Studio model.
- The child did not repeat the `test-driven-development` skill loop.
- The child did not run Ruff, ty, pyrefly, pyright, or mypy.
- The child validated with `.venv/bin/python -m pytest tests/`.
- The parent did not fix code after the subagent; it ran validation and reported review findings.

Child tool summary:

- `write`: 5 completed
- `bash`: 4 completed
- `read`: 3 completed
- `glob`: 2 completed
- `skill`: 1 completed

The one remaining telemetry oddity is that the child loaded the built-in `customize-opencode` skill once after pytest had already passed, then rewrote `templates/home.html` with identical content and reran pytest. This was not a loop, but it is unnecessary work and could be prevented by adding a stronger "do not invoke skills" instruction to the implementer.

Validation output from both child and parent:

```text
1 passed, 2 warnings
```

The warnings were:

- FastAPI/Starlette dependency warning about `asyncio.iscoroutinefunction`.
- Starlette `TemplateResponse` deprecation warning because `app.py` uses `TemplateResponse(name, {"request": request})` instead of `TemplateResponse(request, name)`.

The parent review correctly identified these code issues:

- `app.py` imports unused `RedirectResponse` and `os`.
- `app.py` uses deprecated `TemplateResponse` argument order.
- `tests/test_app.py` imports `TestClient` from `fastapi.testclient` instead of the roadmap-specified `starlette.testclient`.
- `templates/home.html` uses Bootstrap 5's removed `jumbotron` class.

Conclusion: the agent orchestration worked correctly enough for Lesson 11 Phase 1. The generated code passes the required smoke test, but it has small quality/spec deviations that are worth addressing in either the prompt or the implementer instructions before using this as a clean course exemplar.

## Built-in Implementer Claim

An OpenCode session later reported:

```text
Root cause: The built-in implementer subagent type resolves to openrouter/deepseek-v4-flash as its model...
```

Local runtime/source evidence does not support that as stated.

The local OpenCode source defines native agents in `packages/opencode/src/agent/agent.ts`. In that source, native built-in subagents include `general` and `explore`; there is no native `implementer` entry in the built-in `agents` map. Custom agents are then merged from config.

The active runtime agrees:

```bash
rtk opencode debug agent implementer
```

Resolved `implementer` as:

```json
{
  "name": "implementer",
  "mode": "subagent",
  "native": false,
  "model": {
    "providerID": "lmstudio",
    "modelID": "mellum2-12b-a2.5b-thinking"
  }
}
```

The task tool source also does not hardcode `implementer`. In `packages/opencode/src/tool/task.ts`, it resolves the requested subagent with:

```ts
const next = yield* agent.get(params.subagent_type)
```

and then chooses the model with:

```ts
const model = next.model ?? {
  modelID: msg.info.modelID,
  providerID: msg.info.providerID,
}
```

Therefore, if `task` sees the current project config, `subagent_type: "implementer"` should resolve to the project custom agent and use `lmstudio/mellum2-12b-a2.5b-thinking`.

### Updated Interpretation

The statement "built-in implementer subagent type resolves to openrouter/deepseek-v4-flash" is probably the model's inferred explanation, not established runtime fact.

The remaining possibilities are narrower:

- The failed session was running with stale agent config from before `.opencode/agents/implementer.md` was updated.
- The failed session was running from a different working directory or config scope.
- The OpenCode server/TUI needed a restart to reload project agent files.
- A plugin or older runtime version exposed an `implementer` agent differently from the local source now being inspected.

The current runtime state says `implementer` is a project custom agent, not a native built-in, and its resolved model is Mellum2.

## Latest Phase 1 Run: Lower Mellum Traffic, Remaining Guard Bug

Latest inspected Phase 1 run:

- Parent session: `ses_0bc77590dffehlwpoz3t6Va8ZP`
- Parent title: `Execute Lesson 11 prompt from README`
- Parent agent/model: `build`, `deepseek/deepseek-v4-flash`
- Child session: `ses_0bc76d5a6ffeQwsran0tNkogf1`
- Child title: `Implement Phase 1 - Home Page (@implementer subagent)`
- Child agent/model: `implementer`, `lmstudio/mellum2-12b-a2.5b-thinking`

Compared with the earlier successful Phase 1 child `ses_0bc9adfb0ffeqrK3r3UANQIVKi`, the latest child had lower Mellum traffic:

- Earlier Phase 1 child: `16` Mellum assistant calls, which LM Studio would show as a final conversation length of `32` messages.
- Latest Phase 1 child: `13` Mellum assistant calls, and LM Studio logs confirm `13` chat completions ending with `Running chat completion on conversation with 26 messages`.
- Earlier Phase 1 child tokens: `149783` input, `2132` output, `1423` reasoning.
- Latest Phase 1 child tokens: `136283` input, `1417` output, `1094` reasoning.
- Latest per-request context usage to Mellum averaged `10676.5` total tokens, with a maximum of `13011` total tokens. Input-only context averaged `10483.3` tokens, with a maximum of `12657`.

This is evidence that the implementer guardrails helped reduce extra turns. The specific improvements visible in telemetry are:

- No `skill` tool call in the latest child.
- No extra read pass after implementation.
- Fewer bash calls: `3` instead of `4`.
- Fewer write calls: `4` instead of `5`.
- Fewer total tool parts: `12` instead of `15`.

The latest child also correctly performed validation inside the subagent:

```bash
.venv/bin/python -m pytest tests/
```

That command passed inside the child before control returned to the parent. The parent then ran its own validation and review, but did not edit files after the subagent, which matches the Lesson 11 prompt.

However, the child wrote this incorrect guard to `app.py`:

```python
if __name__ == "main__":
```

The child's own final summary claimed it added the correct `if __name__ == "__main__"` block, but the write tool input and resulting file both contain `"main__"`. This means the problem originated in the model-generated write tool call, not in filesystem corruption after the write.

The parent review correctly identified this as the critical mistake:

```text
app.py:12 — Broken __name__ guard: Uses if __name__ == "main__": instead of if __name__ == "__main__".
```

The reason pytest missed it is that the smoke test imports `app`, which does not execute the `if __name__ == ...` block. The main agent caught the issue during review, but the prompt forbids post-subagent fixes, so the bad artifact remained.

Potential setup improvements:

- Add a Phase 1 smoke test that checks the exact `__main__` guard text or executes `python app.py` in a bounded way.
- Or remove the `__main__` block from the course task and run the app only with `uvicorn app:app --reload`.
- Ask the implementer to re-read any file containing sentinel literals such as `__main__` after writing it, before running tests.
- Ask the parent to include exact critical-review findings in the subagent prompt as validation expectations, since the parent cannot fix after delegation.

### Follow-up: Was This Context Pressure?

The exact delegated child prompt did include the correct roadmap line:

```text
Add a `if __name__ == "__main__"` block to run with `uvicorn.run("app:app", reload=True)`
```

The active Mellum2 model bundle has `llm.load.contextLength: 50000`, while the latest Phase 1 child peaked at `13011` total tokens in a single request. That makes context pressure an unlikely primary cause for this specific `__main__` corruption. The stronger current hypothesis is model brittleness around sentinel/code literals inside generated tool-call content.

A non-cheating validation improvement would be to test the requested behavior directly. A pytest test can run `app.py` as `__main__` while replacing `uvicorn` with a fake module, so it proves the guard calls `uvicorn.run("app:app", reload=True)` without starting a server. This would catch `if __name__ == "main__":` naturally because the fake `uvicorn.run` would never be called.

The current context budget appears large enough to keep pytest validation and up to two focused repairs inside the implementer. The bigger risk is not headroom; it is repair quality. Repairs should stay pytest-only, require a fresh read before editing after failures, and stop after bounded attempts.

## Combined Phase 1 + Phase 2 Run: Phase 2 Repair Drift

Latest combined run:

- Parent session: `ses_0bc46ac1affeAPuWYm319CKa4B`
- Parent title: `Execute Lesson 11 from README.md`
- Parent agent/model: `build`, `deepseek/deepseek-v4-flash`
- Phase 1 child: `ses_0bc45d69bffe00eoYhThp8F56D`, `implementer`, `lmstudio/mellum2-12b-a2.5b-thinking`
- Phase 2 child: `ses_0bc45530affedcqjqDEFwQZFTq`, `implementer`, `lmstudio/mellum2-12b-a2.5b-thinking`

The parent did create separate implementer children for Phase 1 and Phase 2. Phase 1 had a reasonable pytest-driven repair loop: it initially returned non-HTML JSON-ish content, then fixed the homepage output enough for the existing tests.

Phase 2 was much noisier:

- `21` Mellum assistant calls.
- `10` patch parts.
- `4` completed bash validation calls.
- `4` completed edit calls and `1` failed edit call.
- Multiple pytest collection failures caused by malformed `tests/test_app.py`.

Failure sequence:

1. Phase 2 started from a Phase 1 implementation that manually rendered Jinja strings instead of using FastAPI `Jinja2Templates`.
2. The implementer added Phase 2 files/routes/tests.
3. Its first pytest run failed during collection due to a corrupted test line:

   ```text
   assert "This is a test complaint" in response.text"uvicorn", fake_uvicorn)
   ```

4. It tried a narrow edit, hit a stale/no-op edit failure, re-read the test file, and continued.
5. It then produced another syntax error involving the entrypoint-test code fragment:

   ```text
   app_path = Path(__file__).resolve().parents[1] / "uvicorn", fake_uvicorn)
   ```

6. It eventually rewrote the full test file to recover, then hit an import error because `RedirectResponse` was imported from `fastapi` instead of `fastapi.responses`.
7. It fixed that import and finally got `5 passed`.

The final suite passed, but the generated app still returned rendered HTML strings as `application/json`, because tests asserted text content without asserting HTML content type. This means the tests were strong enough to force textual output but not strong enough to enforce the intended FastAPI/Jinja response pattern.

Opinion: running Phase 1 and Phase 2 together was probably too much for this setup. The main issue is not context headroom; the Phase 2 peak request was `15916` total tokens. The issue is that Phase 2 built on unreviewed Phase 1 choices and then rewrote a growing test file during repair. A better course workflow is to run Phase 1, review/fix or at least checkpoint it, then run Phase 2 against that known-good base.

Potential fixes:

- Add a test that asserts `GET /` and `GET /complaints` return `text/html`, not JSON.
- Tell the implementer to preserve existing tests and append new Phase 2 tests instead of rewriting the whole test file unless the file is syntactically unrecoverable.
- After pytest collection errors, require the implementer to repair only the syntax error line/region first, then rerun pytest before changing application code.
- Prefer separate Phase 1 and Phase 2 runs while debugging Mellum2 behavior.

## Sentinel Literal Corruption: The __name__ Guard Bug

### Finding

In session `ses_0bc76d5a6ffeQwsran0tNkogf1` (2026-07-08 17:01:30 UTC), the implementer generated:

```python
if __name__ == "main__":  # corrupted: should be "__main__"
    import uvicorn
    uvicorn.run("app:app", reload=True)
```

**Key observations:**

- The task prompt correctly quoted the literal: `` `if __name__ == "__main__"` ``
- The write tool call input contained the corruption: `"main__"` (one leading underscore missing)
- Pytest passed despite the bug (tests import app but never execute it as `__main__`)
- Context budget: peak 13,011 / 131,072 tokens available — NOT context pressure
- LM Studio logs show 13 chat completions in ~4 seconds, all streaming to 100%, no truncation
- The corruption occurred in the model's token generation, not in post-processing

**Root cause:** Small local models (Mellum2-12B) corrupt sentinel literals inside JSON tool-call payloads during generation. Self-review is ineffective because the model cannot perceive what it generated in tool calls after the fact.

**Why tests didn't catch it:** The `if __name__ == "main__":` guard is never reached during test execution (tests import the module; they don't run it as `__main__`). So `uvicorn.run()` is never called, and the syntax is never validated at runtime.

**Telemetry references:**
- OpenCode session export: `rtk opencode export ses_0bc76d5a6ffeQwsran0tNkogf1`
- Write tool call ID: `kDCFgpgW5a8YrHlPXvseuEjMkbZIc1uA`
- File written: `/Users/pauleveritt/PycharmProjects/dlai-local-ai-course/app.py` (line 12)
- LM Studio logs: `/Users/pauleveritt/.lmstudio/server-logs/2026-07/2026-07-08.1.log` lines 1702–1750

### Fix Applied

**Design doc:** `docs/superpowers/specs/2026-07-08-sentinel-literal-verification-design.md`

**Approach:** Add a sentinel-literal verification protocol to `.opencode/agents/implementer.md`. When a task requirement quotes exact code in backticks, the implementer must:

1. Copy the literal verbatim into the file
2. After writing, verify with `grep -F '<literal>' <file>` and trust only the exit status
3. If grep fails (non-zero), re-read the literal from the task text, re-copy it, and re-check

**Why this works:** `grep -F` returns ground truth as an exit code (0 = found, non-zero = missing). The model reacts to tool exit codes reliably. Corruption would need to occur identically in both the generated tool call *and* the grep pattern simultaneously — much less likely than a single stochastic slip.

**Why not alternatives:**
- **Direct-execution tests** (Approach B): Phase 2 telemetry showed entrypoint tests themselves were corrupted, making the problem worse with this model.
- **Requirements verification manifest** (Approach C): Too verbose for Mellum's instruction-following budget; adds multiple turns per phase.

**Validation:** Phase 1 runs should now complete with correct `if __name__ == "__main__":` and visible `grep -F` calls in session telemetry.

### Status

- [x] Finding verified against telemetry
- [x] Design spec written and approved
- [x] Implementation: add instruction block to `.opencode/agents/implementer.md`
- [ ] Validation: prove a Phase 1 run completes cleanly with visible `grep -F` calls in session telemetry

### Follow-up: Grep Gate Run Stalled Elsewhere

After adding the sentinel-literal verification block, Phase 1 was retried in:

- Parent session: `ses_0bba029b3ffeqlfYyMmD1OqLjz`
- Child session: `ses_0bb9fdc25ffeweh15wz5yx8ddn`
- Child model: `lmstudio/mellum2-12b-a2.5b-thinking`

Findings:

- The child resolved to LM Studio correctly, not `omlx`.
- The initial `app.py` write had the correct `if __name__ == "__main__":` guard.
- The child never ran the requested `grep -F` sentinel check, so the grep gate is not yet validated.
- The run drifted after pytest passed. It chased the remaining FastAPI `asyncio.iscoroutinefunction` deprecation warning, repeatedly reran pytest, and then ran `.venv/bin/python app.py`, which starts Uvicorn and waits until interrupted.
- LM Studio logs confirm the run reached conversations with 58, 60, and 62 messages. OpenCode stores the same run as 32 session messages / 133 parts with cumulative input tokens of `259999`.

Interpretation: the grep gate did not cause this stall directly. The stronger finding is that the implementer needs a hard stop after tests pass, and it must not validate a server entrypoint by running `python app.py` directly.

### Follow-up: Strip Implementer Prompt Back Down

The latest Phase 1 stall suggests prompt load is now part of the problem. A few commits earlier, Phase 1 usually completed in roughly 20 OpenCode messages with the recurring `__main__` literal as the main critical issue. After adding broader test-preservation, runtime-warning, repair-routing, and sentinel-verification instructions, the implementer reached a correct app state but continued into warning-chasing and eventually started the Uvicorn server with `.venv/bin/python app.py`.

Change applied: simplify `.opencode/agents/implementer.md` back toward the earlier reliable shape while keeping only high-signal guardrails:

- Validate only with `.venv/bin/python -m pytest tests/`.
- Stop immediately once pytest passes.
- Do not run `uvicorn` or `.venv/bin/python app.py`.
- Fix pytest failures using the traceback target file.
- Narrow `grep -F` literal verification to Python entrypoint sentinels such as `__main__` and `uvicorn.run("app:app", reload=True)`.

Working hypothesis: Mellum follows shorter, sharper instructions better than a long repair policy. Move nuanced validation strategy into the main agent/review loop, and keep the implementer focused on code generation plus bounded pytest repair.

## Prompt Placement Cleanup

The typed Lesson 11 prompt and README prompt were getting too large. The current placement rule is:

- Keep the typed kickoff prompt short: point OpenCode at Lesson 11 and name the requested roadmap phase.
- Keep `README.md` as the main-agent delegation contract: read the specs, delegate exactly once to `@implementer`, review afterward, and do not retry with another subagent.
- Keep `.opencode/agents/implementer.md` as the subagent behavior contract: read existing files before editing, validate only with `.venv/bin/python -m pytest tests/`, stop after passing tests, and avoid server/lint/type/LSP tools.
- Keep `specs/roadmap.md` product-facing. Do not put tool policy or repair-loop policy there unless it changes the app deliverable.

This also addresses the Phase 2 `oldString`/wrong-baseline failure more directly. The latest stopped Phase 2 run did not merely have concurrent file drift; the implementer appeared to edit `app.py` from an assumed Flask or stale baseline instead of the current FastAPI/Jinja file. The fix is not to bloat the typed prompt, but to have the main agent tell the subagent to adapt current files and have the implementer read existing files before editing.

The newer `models.py` doom-loop is the same family of problem. The implementer needs to re-read the current target file before each repair edit, not only after a stale edit failure, so it stops trying to reuse an old patch against a file that has already drifted.

## models.py No-Progress Repair Loop

### Session

- Child session: `ses_0bb7f4f28ffeLj71woUgagzo7s`
- Child title: `Implement Phase 2 (@implementer subagent)`
- Child model: `lmstudio/mellum2-12b-a2.5b-thinking`
- Started: 2026-07-08 18:31:52 EDT
- Tokens: `366949` input, `4476` output

### Anatomy

Tool telemetry shows seven consecutive `edit models.py` → pytest cycles (plus one initial cycle), ending in an edit error:

- `9` completed edit calls, `2` failed edit calls
- `8` pytest runs, all with the byte-identical error: `app.py:14: SyntaxError: unterminated string literal (detected at line 15)` (line 15 of `models.py`, reached through the `from models import complaints` import in `app.py`)
- All seven repair edits to `models.py` had **byte-identical `oldString` and `newString`** — the same edit re-submitted seven times, each reported `completed`

The precise failure:

1. The initial `write` of `models.py` contained two apostrophe-inside-single-quote bugs: line 15 (`'...doesn't match...'`, Analytic) and line 16 (`'I'm having trouble...'`, Visionary).
2. Python reports only the first SyntaxError: line 15.
3. The repair edit fixed only the wrong line — it double-quoted the Visionary line 16 and left line 15 unchanged in both `oldString` and `newString`.
4. The pytest error therefore stayed byte-identical. The model interpreted "same error" as "my fix didn't apply" and re-submitted the identical edit six more times rather than re-diagnosing.
5. Every edit reported `completed` (after the first application the replacement was an effective no-op that still matched and "succeeded"), so no tool-level failure ever interrupted the loop.
6. The run ended in an edit error, and the workspace was left with the line 15 bug still on disk: `.venv/bin/python -m pytest tests/` fails 1 of 2 (`test_complaints_page`).

### Why Existing Guards Did Not Fire

- The stale-`oldString` guard never triggered because every edit **succeeded** — nothing was stale.
- The "at most two focused fix attempts" instruction was in the prompt and the model made seven attempts. Instruction-level counters that require the model to count its own attempts do not hold for Mellum.
- The re-read-before-repair rule (added after this run) helps grounding but does not by itself stop the loop, because the model's misreading was of the *error*, not the file: it repaired a different line than the one the error named, then treated the unchanged error as an apply failure.

### Guard Applied

Added to `.opencode/agents/implementer.md`, keyed on observable evidence instead of self-counting:

> Never re-apply an edit you already made. If pytest reports the same error after your repair, the repair was wrong even though the edit reported success. Re-read the exact file and line named in the error and make a different change to that line. If the error is unchanged after two repairs, stop and report.

The three load-bearing triggers are all externally observable by the model: (1) an edit it has already submitted, (2) pytest output identical to the previous run, (3) the exact file:line named in the error. None require the model to maintain a count across turns.

### Open Lead

A cheap mechanical complement, if instruction-only guarding proves insufficient: after editing any `.py` file during repair, run `.venv/bin/python -m py_compile <file>`. That names the failing file and line directly (`models.py:15`) instead of routing the SyntaxError through the `app.py` import site, which is what misdirected the first repair. Stdlib-only, so it stays inside the course toolchain; the cost is one more instruction in the prompt.

## Phase 1 Termination Loop: Reasoning Complies, Emission Does Not

### Session

- Parent session: `ses_0bb6c36c2ffesnYOMQ39shLgha`
- Child session: `ses_0bb6bd392ffey2GIEnHGKmOBvB`
- Child model: `lmstudio/mellum2-12b-a2.5b-thinking`
- Started: 2026-07-08 18:53:09 EDT
- Tokens: `227139` input, `1483` output, `1079` reasoning, 20 message rows

### What Actually Happened

The initial read of this run was "warning-chasing after pytest passed." Telemetry shows something narrower and more important:

1. Steps 1–6: clean implementation (glob, four writes, glob).
2. Step 7: pytest → `1 passed, 2 warnings`.
3. Step 8: exactly one edit — the correct `TemplateResponse(request, "home.html")` fix, which removed the deprecation warning.
4. Steps 9–18: **ten consecutive identical `pytest` runs with zero edits between them**, every one returning `1 passed, 1 warning`.
5. Final message: `finish: stop`, the loop self-terminated.

There was no warning-chasing edit loop. The one edit was correct and warning-reducing.

### The Key Evidence

The reasoning text on every repeated turn was byte-near-identical and **explicitly compliant with the stop rule**:

```text
The tests are passing! There's just one deprecation warning from FastAPI about
`asyncio.iscoroutinefunction` being deprecated, but that's not something I can
fix directly - it's part of the FastAPI framework. The important thing is that
all tests pass...
```

The model decided to stop, every time — then emitted another pytest tool call anyway instead of a final text message. This is a **termination emission failure**, not an instruction-following failure. The existing "stop and report success" instruction won the argument in the model's reasoning; the failure is in the transition from reasoning to a tool-free final message. Small thinking models fall into this repetition attractor: each identical tool+result pair appended to context makes the next identical emission more likely.

Consequence: adding more or stronger "stop after pass" wording targets the wrong layer. The intent is already compliant.

### Why OpenCode's Built-in Doom-Loop Guard Did Not Fire

OpenCode has a native `doom_loop` permission (default `ask`). Source: `packages/opencode/src/session/processor.ts`, `DOOM_LOOP_THRESHOLD = 3`. The detector fires only when the last 3 parts **of the current assistant message** are identical tool calls. This run emitted one identical call per assistant message across ten messages — a shape the per-message detector cannot see. Cross-message repetition of identical tool calls is currently invisible to the built-in guard. (Possible upstream issue.)

### Mechanical Fix Available: `steps` Cap

The agent config schema supports `steps` (`packages/core/src/config/agent.ts:22`, positive integer, valid in agent markdown frontmatter). In `packages/opencode/src/session/prompt.ts`:

- `const maxSteps = agent.steps ?? Infinity` (line 1281)
- On the final step, OpenCode appends `MAX_STEPS_PROMPT`, which disables tools and forces exactly the emission this model cannot produce on its own: "Respond with text only... summary of what has been accomplished so far."

Baselines for choosing the cap: healthy Phase 1 runs take 13–16 steps; a Phase 2 run with legitimate repairs took ~21; the worst observed doom run (`ses_0bbbb9dc2ffesw9Xy2ARKRLFW3`) burned 1,247,857 input tokens, likely 40+ steps. A cap around 20–25 leaves repair headroom while converting unbounded doom tails into a forced clean text summary.

### Guards Applied

- Added `steps: 20` to `.opencode/agents/implementer.md` frontmatter — the platform-enforced bound; at the cap, OpenCode forces a tool-free text summary.
- Reworded the stop rule to target emission rather than intent: after pytest passes, the next message must be plain text with no tool calls — do not run pytest again to confirm.

## First Run Under the Steps Cap: Corruption at Birth, Cap Fires, Grep Gate 0-for-2

### Session

- Child session: `ses_0bb5ee314ffeacH7bGJUos5lCe`
- Child model: `lmstudio/mellum2-12b-a2.5b-thinking`
- Started: 2026-07-08 19:07:17 EDT
- Tokens: `230280` input, `1403` output, `622` reasoning
- Exactly `20` assistant messages — the configured `steps: 20` cap

### Corrected Read

The initial impression was "the subagent finished the work, then a review pass left behind a couple of bad final edits." Telemetry contradicts that:

- The malformed guard `if __name__ == "main__:":` and the request-less `home()` with `{"request": {}}` were both present in the **initial write** of `app.py` (tool call 5). Born bad, not damaged later.
- The only edit in the entire run (tool call 13) was a correct, pytest-driven, one-shot import repair: `from fastapi import FastAPI, Jinja2Templates` → separate `fastapi.templating` import, after a clean collection error. The repair loop worked exactly as intended this time.
- After pytest passed (tool call 14, `1 passed`), there were **zero edits** — the post-pass tail (calls 15–19) was read-only drift: four globs and a read of `app.py`, with reasoning like "check the content of app.py to see if it has the correct structure."
- The 20th step hit the cap. OpenCode injected `MAX_STEPS_PROMPT` (tools disabled, text-only), and the model emitted an **empty message** — no summary. The forced-summary mechanism bounds cost, but Mellum could not comply with even the forced text-only prompt.

### Findings

1. **Third `__main__` corruption, new variant.** `"main__:"` (missing leading underscores, colon inside the string) joins `"main__"` from `ses_0bc76d5a6`. Both occurred in initial `write` tool calls. This is single-shot generation corruption; no loop or repair restructuring can address it.
2. **The grep sentinel gate is 0-for-2.** The instruction is verifiably in the resolved agent prompt (`rtk opencode debug agent implementer`) and was not executed in either run since it was added. Instruction-level verification protocols inside the Mellum child are empirically not followed. If sentinel verification is to happen, it must run outside the child — e.g., the parent mechanically greps the sentinel literals after the child returns and re-delegates a scoped fix on a miss.
3. **The steps cap works as a bound.** It ended the post-pass drift at a known cost (~5 wasted read-only turns) instead of an open-ended tail. Cost: the child's final text was empty, so the parent received no summary from the task result.
4. **Tests pass while the app is structurally wrong.** `{"request": {}}` passes because `home.html` never dereferences `request`; the removed Bootstrap `jumbotron` class is cosmetic and untested. Both are generation-quality issues invisible to the current smoke test.
5. **Parent model drift explained.** The parent ran `deepseek/deepseek-v4-pro` because that is the global default in `opencode.jsonc` (`"model": "deepseek/deepseek-v4-pro"`). The README's "main agent should use deepseek/deepseek-v4-flash" is prose inside the prompt — it cannot switch the running session's model. Pick flash in the TUI or change the config default.

### Direction This Points

The loop-control problem is now bounded (cap) and the repair loop behaved correctly when the error was honest (import fix). The remaining failure surface is generation quality plus the child's non-compliance with in-prompt verification. Both push the same way as the pending restructuring decision: move verification (pytest and sentinel greps) to the parent, keep the child as close to write-only as practical, and re-delegate scoped fixes to fresh child sessions.

## Restructuring: Write-Only Implementer, Parent-Owned Validation

Both signals above point the same direction: validate/repair inside the Mellum child is where every loop formed (models.py, Phase 1 termination), and the in-prompt grep sentinel gate was never once executed by the child across two runs. Rather than continue patching the repair loop with more instructions, the responsibility was moved to the layer that reliably follows protocol — the DeepSeek parent.

### Changes Applied

**`.opencode/agents/implementer.md`** — reduced to a write-only contract:

- Removed all pytest execution, the repair-loop guardrails (re-read before repair, don't re-apply edits, two-attempt limit), and the in-child grep sentinel check — none of these ran reliably inside the Mellum child.
- Added: "Validation is not your job — the calling agent runs it after you finish."
- Added a single scoped-fix path: if the task names an exact error (traceback, file/line), make one edit and stop; no self-verification.
- Lowered `steps: 20` → `steps: 8`. A write-only child doing initial implementation completed in as few as 6 tool calls in the observed runs; a scoped one-line fix needs even less. The cap now guards against any residual drift, not against an expected-large repair budget.

**`README.md`** Lesson 11 prompt — the parent (`deepseek/deepseek-v4-flash`) now owns:

1. Running `.venv/bin/python -m pytest tests/` itself after the child reports back.
2. Grepping for any backtick-quoted literal the roadmap phase names, with `grep -F`.
3. On failure of either check, delegating exactly once more to a **fresh** `@implementer` child with the exact failing command, error, and file/line — never fixing it itself, never falling back to `@general`.
4. Repeating validate-and-redelegate at most twice before stopping and reporting.

### Rationale

- Fresh child per repair drains the accumulating context that caused both observed doom loops (the repetition attractor and the cross-turn attempt-miscounting share the same root: identical tool/result history piling up in one session).
- The parent is the layer telemetry shows following multi-step protocol reliably; moving pytest and grep checks there converts a Mellum instruction-compliance problem into a DeepSeek tool-use problem, which is not where the failures have been.
- What restructuring does **not** fix: single-shot generation corruption in the initial write (the `__main__` variants, the missing `Request` parameter). Those remain visible only through the parent's post-hoc validation and are the reason the grep-gate step exists at the parent layer at all — just relocated, not deleted.

### Not Yet Validated

This is a design change, not yet a confirmed fix. The next Phase 1 and Phase 2 runs under this contract are the validation step — specifically whether the parent actually performs the grep checks (rather than skipping straight to review), and whether the redelegation cycle terminates cleanly within two rounds.

### Reverted: Validate-and-Redelegate Removed

The redelegation cycle was tried and produced a broader finding (see "Does `oldString` Fail Beyond `__main__`?" below) before being reverted. `README.md` Lesson 11 is back to the same "do not fix anything after the subagent; do a review and report critical mistakes" pattern used by every other lesson (3, 4, 5, 7, 8, 9). `.opencode/agents/implementer.md` had its now-dead scoped-fix-and-report path (added to serve redelegation) removed, since it added prompt weight for a code path the parent no longer triggers.

This does not discard what the redelegation experiment found — it confirmed `oldString`-based `edit` is broadly unreliable with this model (see below) — it just stops the course from routing fixes back through the subagent to surface that.

## Does `oldString` Fail Beyond `__main__`?

A query across all `implementer`-agent sessions in this project's OpenCode database (not just ones inspected earlier in this doc) found 27 `oldString` edit-mismatch failures. Categorizing them shows the dunder-literal corruption is one slice of a broader problem, not a special case:

1. **Blind edits, no read first.** `ses_0bb8e6de4ffept7I5ZMqhyaLZx`'s first tool call was an `edit` targeting `from flask import Flask, render_template` before the session had read the file even once. The actual file was FastAPI. This is content hallucination from training-data priors, not corruption of known text.
2. **Guess-after-failure instead of re-read.** The same session, after one successful edit, alternated failing `edit` attempts between `TemplateResponse` and `TemplateRequest` — two plausible-sounding names — rather than re-reading the file after the first failure to check which was actually there. This directly bypasses the existing re-read-after-stale-failure guardrail.
3. **Whitespace/escaping fragility on multi-line blocks.** `ses_0bbbb9dc2ffesw9Xy2ARKRLFW3` failed matching a block containing a literal escaped `\n` where the file likely had a real newline — multi-line block matching is fragile independent of content correctness.
4. **Plain staleness.** Several ordinary-code mismatches (imports, route bodies) where the file had changed between read and edit — the class the existing re-read guard already targets.
5. **Late-session collapse.** Three edits in the tail of `ses_0bb520988ffe63zBbZNPsGV4Sr` (the second `__main__` retry) submitted a completely empty `oldString` — guaranteed to fail, no content involved.
6. **Doubled-character corruption.** The `__main__` cases, plus one `{{% block content %}}` (doubled brace) in a Jinja tag — a small, distinct class.

**Conclusion:** `edit`/`oldString` is broadly unreliable with this model across content types, not narrowly a dunder-literal problem. A mechanical fix scoped to `__main__` specifically (as first proposed) would leave categories 1–5 uncovered. If targeted repair is reintroduced later, prefer full-file `write` (which only requires correct *new* content, not accurate recall of *old* content) over `edit`, or apply small deterministic fixes outside the model entirely.
