# Lessons for Helping Small Local Coding Models

These lessons came from repeated OpenCode runs, session telemetry, generated
code, and validation results. They are ranked by demonstrated impact. Treat
them as controls for a system, not as claims about a model's character: the
same model can look capable or unreliable depending on scope, tools, context,
and stopping conditions.

## 1. Remove decisions from the SLM

Small local models do best at routine, bounded work, not open-ended
"galaxy-brain" problem solving. Give them a complete implementation packet:
the one phase, files they may change, exact behavior to preserve, acceptance
checks, and one validation command. Let stronger reasoning, human judgment, or
the broader community's training work handle novelty.

The durable strategy is to remove decisions from the model, not to add another
prompt rule. A rule such as "repair at most twice" still relies on the SLM to
count its own loop; a mechanical stop or fresh repair packet does not.

This is the "structure beats strings" principle. A model should not be expected
to remember that a call site matches a signature three files away, a registration
string matches a module path, or an edit anchor matches the file byte-for-byte.
Represent and enforce those relationships with codebase structure, deterministic
tools, and explicit handoff data.

## 2. Treat telemetry and validation as the source of truth

Nothing matters except evidence. An agent's report is not reliable evidence: it
can claim success while missing a contract requirement, or give a plausible
explanation for slowness that the trace disproves. Hunches about local AI are
usually wrong until session records, tool outputs, and validation results agree.

After every meaningful run, inspect parent and child telemetry, tool outputs,
and the actual diff. Use the repository's
[OpenCode telemetry skill](.codex/skills/opencode-telemetry/SKILL.md) to read
the OpenCode database without changing it, follow nested sessions, identify
context risks, and report evidence-based metrics.

Live local runs also showed that generation throughput can fall sharply as a
conversation grows: one model fell from about 60 tokens/second at turn zero to
38-42 by turn four. Measure both turn count and per-turn speed; multi-turn
prefill cost compounds, so a long context is a latency problem even when it
still fits the model window.

## 3. Use spec-driven development with small, isolated phases

Turn a feature into small phase contracts, then hand each contract from a
big-brain planner to a little-brain implementer. The largest gains came from a
fresh child responsible for one phase, with only the named files, exact
user-visible strings, preservation requirements, and validation command.

Do not send the full roadmap, prior summaries, or unrelated repair history
unless the child actually needs them. Phase 2 is especially sensitive to packet
size: broad context and growing test files repeatedly turned ordinary
implementation into long repair loops.

## 4. Separate orchestration, implementation, and verification

Give each role a small, inspectable responsibility. The orchestrator prepares
the packet, keeps context lean, evaluates acceptance criteria, and issues at
most one focused repair packet. The implementer writes only the requested
change. A verifier runs deterministic checks and compares the result with the
phase contract.

For a modest workflow, the parent agent can be the orchestrator and verifier;
adding a separate orchestrator subagent otherwise creates another reasoning hop
and another chance for context drift. In a repeatable production system, a
dedicated orchestrator and mechanical verifier are worthwhile because they move
loop control outside the SLM.

A 12B or 27B orchestrator should still be procedural rather than deliberative.
It has enough headroom to read named files, construct a packet, run a fixed test
command, compare the changed-file set, and check literal requirements. Do not
ask it to invent architecture, perform an open-ended semantic review, or repair
application code itself. Start a fresh orchestrator chat for each phase when
phase-to-phase context isolation matters; a persistent orchestrator isolates
its children but continues accumulating its own history.

Independent verification is foundational. A live Gemma run wrote an edit with
an unresolvable name and still shipped it. Even direct diagnostic feedback does
not guarantee repair: observed self-correction engaged with only half of the
flagged files on the following turn. Let the model author; let a type checker,
test suite, LSP, Pyrefly overlay, or other verifier establish whether it worked.

## 5. Orient the model with structure, not repository-wide exploration

Small models do not have structural awareness of this codebase or its local
house style. Without external orientation, they grep, guess, and use trial and
error for import paths, naming, registration wiring, and ownership boundaries.
That wastes context and does not reliably converge.

The orchestrator should provide the relevant symbols, module paths, conventions,
and complete change surface in the handoff packet. A structural index such as an
LSP, CST/AST transform, or a "model starts, deterministic tooling finishes"
write path can enforce relationships that a prompt merely describes.

## 6. Keep the SLM out of responsibilities owned by better tools

SLMs are not replacements for developers or an IDE. Keep Git operations,
refactors, diagnostics, test execution, code navigation, and deterministic
transformations in the tools that already do them well. Ask the model to make a
specified code change, not to own every decision around it.

This also means stopping after the acceptance command answers the question.
Do not let a small model chase framework warnings, invent adjacent features, or
keep editing after success. Warning cleanup is a separate task unless it is an
explicit acceptance criterion.

## 7. Build a codebase that is easy to constrain and verify

Modular code, useful type hints, mature frameworks, and focused tests reduce
the amount of reasoning delegated to the model. Resist the "god-box" seduction
of asking an agent to invent dependencies or architecture when a mature
framework already supplies known behavior.

Tests and reviews must check the actual phase contract. Several runs passed a
smoke test while silently changing branding, the favicon, navigation, imports,
or required strings. Assert exact user-visible behavior and preservation of
earlier phases; do not accept a vague "no critical issues" review.

## 8. Enforce tool-output limits; do not rely on a prompt reminder

A single `ls -R` traversed `.venv`, produced tens of thousands of characters,
and inflated every following request. The model's initial choice was stochastic;
the context explosion after that choice was deterministic.

Reject recursive listings and protected-directory traversal at the Bash-tool
layer. Allow narrow discovery such as `rg --files`, named-file reads, and the
project's validation command. Prompt guidance is useful, but an enforced tool
policy is what removes this failure mode.

## 9. Keep context deliberately small and clean

A new parent chat is not magic: when every phase already has a fresh child, the
packet shape matters more than the parent's conversation history. Keep routine
SLM work near a 32K input budget and work hard to ensure the phase, tool output,
and validation evidence fit within it.

The coding profile used `context: 40960`, `input: 32768`, and `output: 2048` to
avoid compaction pressure while bounding oversized completions and repair tails.
The goal is not maximum context. It is enough room for a small, clean task plus
validation, with a budget that makes a bad tool choice visible and bounded.

## 10. Choose the exact model and tune it for the role

Model identity and tool training matter. Similar Gemma names, fine-tunes, and
backends can behave very differently: one coder-oriented Gemma variant emitted
a `task` call as prose or stopped after its first tool result, while another
handled multi-step tool trajectories more reliably. Verify the resolved model
through configuration, session telemetry, and backend logs; a configured name
is not proof that it received the request.

For Gemma 4 routine implementation, low sampling entropy reduced chattiness,
speculative plans, and unnecessary tool use: `temperature: 0.2`, `top_p: 0.9`,
and `top_k: 64`. Reserve broader sampling for work that genuinely needs
divergent ideas.

## 11. Give the implementer one job and put validation at one layer

In the minimum workflow, the implementer generates code, reads only named
files, runs the project's explicit validation command once, and stops whether
it passes or fails. This exposes a result without opening a child repair loop,
but it is not independent verification.

In the medium workflow, the implementer is write-only. The orchestrator runs
`.venv/bin/python -m pytest tests/`, compares the changed files with the packet,
and checks exact contract strings after the child returns. Do not make both
roles own repair. Disable planning/design skills for routine implementation and
avoid opportunistic linters, type checkers, or shell activation.

If the child needs more information, the orchestrator should provide a narrower
packet rather than asking the child to explore the entire repository. Use a hard
step cap as a circuit breaker, not as a solution: it bounds a runaway run but
does not fix a bad packet, stale edit anchor, or semantic trap.

The recorded doom loops were not hypothetical. One child exhausted all 20
steps in edit retries, another was cancelled after 100 messages, and another
ran pytest ten times after it had already passed. In the last case the model's
reasoning repeatedly decided to stop but emitted another tool call. OpenCode's
built-in doom-loop guard did not catch repetition spread across separate
assistant messages. A platform-enforced step cap bounded the cost but sometimes
forced an empty final response, so the orchestrator must judge the files and
validation evidence rather than depend on a perfect child summary.

Time budgets are a second circuit breaker. Live runs showed that many prompts
past the first could not converge within 120 seconds. Treat a timeout as
workflow evidence, not an invitation to keep extending the same unbounded
conversation: narrow the packet, use a fresh repair turn, or change the tool
protocol.

## 12. Make edits deterministic and preserve file ownership

For a small file the child has completely read and whose final state belongs to
the current phase, a whole-file write is more reliable than repeated
anchor-based edits. Gemma repeatedly used stale or empty `oldString` values,
producing edit retries that consumed turns without making the intended change.

This was a broad failure mode, not one malformed `__main__` literal: the session
record contained 27 `oldString` mismatches across blind edits, stale content,
whitespace and escaping differences, empty anchors, and late-session collapse.
A repair packet should provide the current file contents and required final
state. When the packet grants complete ownership of a small file, ask a fresh
child for a full-file write; do not ask it to apply an `oldString` patch.

Whole-file writes are unsafe when another phase owns part of the file: they can
erase routes, imports, or behavior that must survive. Use one only when the
packet supplies the complete desired content or the phase owns the complete
file state. Otherwise use a constrained structural or deterministic transform;
if an anchor fails, re-read before retrying.

## 13. Put framework semantics in the packet and the tests

Some failures were semantic, not implementation failures. `TestClient` follows
redirects by default, so a test for a 303 response must use
`follow_redirects=False`. Likewise, a test that only makes a request will not
exercise a script entrypoint or prove that a deprecation warning was removed.

Put known semantic traps in the phase packet, and add focused behavior tests for
paths that ordinary request tests do not cover.

For medium, encode the few known, phase-relevant facts directly in the packet.
Do not attach general framework documentation to every run. Context7 or another
documentation retriever belongs in maximum: the orchestrator should consult it
only for a real API uncertainty, then compress the answer into one concrete rule
for the implementer. This preserves the benefit without paying the full context
cost in both agent roles.

## 14. Interpret context and cache metrics correctly

LM Studio and oMLX do not report prompt reuse the same way. oMLX exposes
`cache_read` tokens, so compare effective per-request context as
`fresh input + cache read`, while reporting the two values separately.

Nonzero cache reads prove prefix reuse, not a wall-clock speedup. Parent
lifetime can include idle time and nested child time, so report active message
span, parent time, and implementer time separately instead of adding nested
durations together.

## Workflow levels

### Minimum

Minimum uses one fresh parent chat and one fresh `@implementer1` for a single
roadmap phase. The parent turns the phase into a small packet containing allowed
files, exact behavior, preservation requirements, and one validation command.
The child implements, runs that command once, and reports; the parent reviews
without repairing. Its deliberate limitation is that validation is
self-reported rather than independent.

### Medium

Medium moves the stable protocol into a phase-local `orchestrator2` primary
agent so the kickoff can be as small as `Run Phase N from @specs/roadmap.md`.
The design must remain workable on Gemma 4 12B, though a 27B model provides more
margin. The orchestrator:

1. Reads the mission, stack, requested phase, and current target files.
2. Records the existing changed-file baseline and constructs a compact packet.
3. Starts a fresh, write-only `@implementer2` without a task ID.
4. Runs pytest, compares changed files, and checks exact required and preserved
   strings itself.
5. On failure, may send one exact repair packet to one new child, validate once
   more, and then stop.

The repair child receives the failing command or contract check, exact output,
current allowed file contents, and required final state. It never inherits the
first child's tool history. This single repair is the best-case design to test,
not an established guarantee: earlier validate-and-redelegate experiments were
reverted after edit-anchor failures. If telemetry shows the orchestrator cannot
reliably stop after one repair, medium should report the failure instead and
leave automatic repair for maximum.

OpenCode does not provide a per-agent "one repair task" counter. The one-repair
rule still depends on the orchestrator remembering it; the 16-step agent cap is
the only mechanical bound in medium. Measure this explicitly rather than
describing the prompt rule as enforced loop control.

Because this course uses small files and `oldString` failures were severe,
`implementer2` is instructed to read each named existing file completely and
write its complete final content, preserving all shared content named by the
packet. Current OpenCode maps both `edit` and `write` to the same `edit`
permission, so medium cannot mechanically expose `write` while denying
exact-match edits. Treat compliance as an experiment to measure. Maximum should
replace this prompt rule with a tool policy or deterministic structural
transform, especially for larger or concurrently owned files.

Do not force a scout agent to read one or two known files. Prior experiments
ignored that rule across eight phases because direct reads were cheaper. A
read-only scout is useful only for genuine cross-file searches or convention
discovery.

### Maximum boundary

Maximum adds controls whose setup or context cost is too high for the teaching
baseline: mechanically enforced tool-output limits, structural navigation or
LSP checks, deterministic transforms, on-demand Context7 research, richer
contract tests, telemetry-driven model verification, and externally enforced
repair budgets. These belong outside the small implementer's prompt whenever a
tool can own them more reliably.

## Evidence sources

- [Lesson 11 OpenCode debug notes](docs/lesson-11-opencode-debug.md) preserve
  the original session evidence and the first set of workflow changes.
- [Model configuration](README.md#model-config) records the native LM Studio
  baseline and the selected coding profile.
- [Telemetry workflow](README.md#telemetry-workflow) explains how to collect,
  inspect, and report each OpenCode run.
