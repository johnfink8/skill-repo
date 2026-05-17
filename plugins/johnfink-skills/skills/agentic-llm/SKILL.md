---
name: agentic-llm
description: Use whenever the user is building, debugging, or extending code that puts an LLM in a loop — calling tools, taking multi-step actions, deciding what to do next. Triggers include words like "agent", "agentic", "tool use", "tool calling", "ReAct", "autonomous", and code that loops over `messages.create` / `responses.create` / similar SDK calls. Apply when wiring webhooks/events/queues to an LLM, when an agent is misbehaving (looping, flailing, blowing context, spawning too many subagents), and when planning a new agent. Do NOT apply for one-shot prompting — only when the LLM has tools and decides its own next step.
---

# Agentic LLM systems

Most "first-pass agent" code is one of two things: a 30-line ReAct loop calling an LLM with a tool list, or an event handler that fires off an LLM call per inbound webhook. Both work in a demo. Both crater in production. The principles below are what separates a real agentic system from a demo.

## 1. Don't reach for an agent first

The escalation ladder for "I need an LLM to do X":

1. **No model at all.** Can deterministic code, regex, SQL, or a rules-based router solve this? If yes, stop.
2. **Embeddings, not generation.** If the task is *classification into N buckets*, *similarity search*, *clustering*, *deduplication*, *routing to one of K handlers*, or *finding the closest match* — you want an embedding model + cosine similarity / k-NN / a tiny classifier head. Not an LLM in a loop.

   **This is the speed point. Embeddings are orders of magnitude faster than an agent.** A cosine-similarity classifier against 12 bucket centroids returns in single-digit milliseconds, deterministically, for fractional-cent cost. An agent doing the same job: seconds of latency, dollars per thousand calls, non-deterministic outputs, and a tool-call budget you have to bound. "Categorize this ticket," "route this query to the right backend," "find similar items in the catalog," "is this near-duplicate of something we've seen?" — these are embedding problems, not agent problems.

   Embed once at ingest, store the vectors, compare at query time. That's the whole system.
3. **Single optimized LLM call.** One tight prompt, one model call, structured output. Most problems people give to agents end here.
4. **Workflow.** Prompt chaining, routing, parallelization, orchestrator-workers, evaluator-optimizer. Predefined control flow with model-directed branches at the named decision points.
5. **Autonomous agent.** Last resort.

Reach for a full autonomous loop only when:
- The number of steps genuinely can't be enumerated up front.
- The decisions between steps depend on observations only the model can interpret.
- You've already tried the workflow version and identified what it can't do.

Agents trade reliability, latency, and cost for flexibility — and "flexibility" is rarely what the actual problem needs. Most production "agents" are really workflows with one or two model-directed branches.

### And when you do build an agent: pre-load what you know it will need

Every tool call is a roundtrip: latency, tokens, and a chance for the model to choose wrong. So before exposing a tool, ask: *will the model need this information on essentially every run?* If yes, **put it in the prompt up front.** Don't make the model ask.

Examples of things to pre-load, not tool-fetch:

- Current date/time, timezone, locale.
- The user's persistent profile / preferences / role.
- The routing table, the catalog summary, the list of valid bucket names.
- Recent context the model needs to reason about ("the last three things this user did").
- Anything the workflow's first decision depends on.

Examples of things to leave behind a tool:

- The full body of a record when only one out of millions might be needed.
- Search results — the query depends on what the model decides.
- Anything large that's only sometimes relevant.

The rule: **pre-load high-confidence, small context; JIT-fetch low-confidence or large context.** A first-pass agent that builds `get_current_date`, `get_user_timezone`, `get_routing_table` as tools is doing extra work that costs latency on every run. Just put those in the system prompt.

## 2. Decouple input I/O from the agent loop with a queue

**This is the single biggest mistake in first-pass agentic code, and it's the one principle here not borrowed from the canonical agent essays — it's classical producer/consumer queueing applied to agent invocation.** Don't let inbound events spawn agent invocations directly.

Bad:
```python
@app.post("/webhook")
async def webhook(req: Request):
    return await run_agent(req.json())   # fans out per event, unbounded
```

A burst of 500 events spawns 500 concurrent agent loops, each chewing tokens, each racing for the same downstream resources, none cancellable.

Good — events enqueue, workers dequeue:
```python
@app.post("/webhook")
async def webhook(req: Request):
    await queue.put(req.json())          # cheap, bounded
    return {"status": "queued"}

# elsewhere, N workers (N = chosen concurrency)
async def worker():
    while True:
        msg = await queue.get()
        await run_agent(msg)
```

The queue can be Redis, SQS, an `asyncio.Queue`, a DB table polled by workers, an APScheduler jobstore — anything that gives you (a) a place to land work without doing it, and (b) a bounded set of consumers. The point isn't the technology; the point is **the agent's concurrency is set by the worker pool, not by the inbound traffic.**

Benefits:
- Backpressure for free. Queue depth surfaces overload before you discover it via OpenAI 429s.
- Idempotency and retry are tractable — failures stay in the queue, succeed-once semantics is a worker concern.
- A misbehaving agent can be paused (stop the workers) without losing inflight work.
- Sessions can serialize their own runs (DB-row-as-queue: one row per session, status gate prevents two cycles in parallel).
- One leader can hold a named lock so only one node in a cluster runs the workers — no thundering herd.

For UI-driven cases, the "fire-and-forget" variant works too: the action inserts a row and returns a session ID immediately; a background task runs the cycle and streams events via SSE/WebSocket. The frontend never blocks on agent execution.

## 3. Bound every loop with hard stops outside the model

The model will always try one more thing. Enforcement lives in the harness, not the prompt. Required limits, per run:

- **Max turns** (e.g. 6–16). After this, fail with a structured error.
- **Max tool calls** (e.g. 16–32). Per run, not per turn.
- **Wall-clock timeout** (e.g. 60–120s). Drive via `AbortController` / cancellation token, not a sleep watchdog.
- **Token / context budget**. Pre-flight check on assembled messages — if you're already at 80% of the model's window, bail before the call instead of getting a 400.
- **Stuck detection**. Same tool name + near-identical args N times in a row → abort. The model is flailing.
- **Concurrent-subagent cap** if the parent agent spawns workers. Anthropic's research system caps simultaneous subagents at 3–5.

Every limit gets a clean failure path that returns a structured result (`{success: false, reason, turns, tool_calls}`), not a thrown exception. The caller needs to know *why* it stopped.

## 4. Tool errors are tool results, not exceptions

When a tool call fails, the agent loop should:
1. Catch the exception inside the tool boundary.
2. Return a `ToolResult` whose `output` describes the error in natural language.
3. Feed it back to the model as a normal tool result on the next turn.

The model can read "ENOENT: file not found at /x/y" and retry with a corrected path. It cannot read a Python stack trace that crashed the loop. Unknown tool name? Same — return `{"error": "unknown tool: foo"}` to the model, don't 500.

This is the difference between an agent that gracefully recovers and one that the engineer has to babysit.

## 5. Tool design is the agent's UX

Tools are how the model perceives and acts on your system. Treat their design with the care you'd give a public API consumed by a junior engineer.

- **Workflow-shaped, not CRUD-shaped.** `schedule_meeting(when, with, topic)` beats three calls to `find_user`, `find_slot`, `create_event`.
- **Names that disambiguate.** `search_recent_emails` vs `search_archived_emails`, not two `search` tools that the model has to guess between.
- **Descriptions that read like onboarding docs.** Tell the model when to use this tool, when *not* to, and what good inputs look like. The description is prompt territory — invest in it.
- **Identifiers the model can speak.** Slugs and paths over UUIDs. The model produces UUIDs unreliably.
- **Paginate and truncate by default.** A tool that can return 10MB will, eventually, blow your context.
- **Errors that point at the fix.** Not `"validation failed"` — `"validation failed: 'when' must be ISO8601, got '2026-13-01'"`.

Test tools by reading the description cold: can you tell what the tool does, when to use it, and what inputs are valid? If not, the model can't either.

## 6. Context is a tradeoff — tune to the task

The tradeoff runs in a direction that's easy to get backward:

- **Tool calls cost latency but buy accuracy.** Every call is a roundtrip — slow. But the model gets exactly what it asked for, fresh, in response to its own decision. The relevant info lands at the end of the context window where attention is sharpest, and the model already knows why it asked.
- **Front-loaded context saves latency but often costs accuracy.** No roundtrips — fast. But the model has to find the relevant bits in a longer prompt, and as prompts grow, attention quality degrades ("lost in the middle"). The right answer might be on page 4 of the system prompt; the model might never look there.

The small, high-confidence pre-loads from §1 (date, user profile, routing table) are the case where front-loading is good for *both* axes — small enough not to crush attention, always-needed enough that the model expects to use them. The "often costs accuracy" caveat kicks in when you start front-loading **large** or **speculative** material to avoid tool calls.

Pick the axis before tuning:

- **Accuracy matters far more than latency** — code review, medical reasoning, irreversible action, anything where a missed fact is the dominant failure mode. **Prefer tool calls.** Let the model fetch what it needs when it needs it instead of drowning it in pre-loaded context. A 5-second correct answer beats a 500ms wrong one.
- **Latency matters far more than accuracy** — voice agent turn, real-time UI completion, high-volume classification pass. **Front-load aggressively.** Eliminate roundtrips. Pre-loaded context is what ships; tools are reserved for things you genuinely can't anticipate. Accept the attention tax as the cost of being fast.
- **Most things** sit in between. Tools for large/speculative info; pre-loading for small/always-needed info. Then watch the evals (see §10) to see which side of the dial actually moves the needle for your task.

The mechanics below apply regardless; the dials get set differently:

- Pre-load context the model needs to make every decision (see §1: dates, profile, routing table, etc.). For everything else — large payloads, low-confidence lookups, search results — keep messages lightweight (IDs, paths, summaries) and fetch via tools when the model decides it needs them.
- Compact or drop large tool results once they've served their purpose. A 50KB search result the model already extracted what it needed from is dead weight on turn 7.
- Cache the system prompt and tool definitions with ephemeral cache markers (Anthropic SDK: `cacheControl: { type: "ephemeral" }` on the system message). Multi-turn conversations within the 5-min TTL get drastic cost/latency wins.
- For long sessions, write a compaction step: take the last N turns, distill to "what we've learned + outstanding actions", restart the conversation from that summary plus the next user turn.

## 7. Decompose — don't make one prompt do planning, reasoning, and acting

Success probability decays exponentially in the number of things one prompt is trying to do. Three specialized prompts that chain are almost always better than one mega-prompt that tries to plan + research + act + format.

Common decomposition: a **planner** produces a structured plan (deterministic, schema-validated), an **executor** runs the plan step by step (possibly with the model's help on each step), an **evaluator** scores the result. Each role has a focused prompt and a small tool set.

Bonus: each role is independently testable. Mega-prompts are not.

## 8. Parallelize within a step; serialize across them

When the model issues multiple tool calls in a single turn, run them concurrently (`asyncio.gather`, `Promise.all`). This is free latency reduction — they were already independent or the model wouldn't have batched them.

Do NOT parallelize *across* turns. Turn N+1's prompt depends on turn N's tool results; trying to overlap them is racing with yourself. The agent loop is fundamentally sequential per run.

## 9. Multi-agent is ~15× the tokens of a single conversation — earn it

Anthropic's published numbers: multi-agent research systems burn ~15× the tokens of single-turn chat. The 80% of quality variance came from total token spend, not architectural cleverness. The architecture is worth it when the task is parallelizable and breadth-first (research, scouting, brainstorming). It is NOT worth it for coding, anything that needs shared state across workers, or anything that needs tight coordination.

Heuristic: if you'd struggle to describe what each subagent is doing in one sentence each, you don't need subagents — you need a single agent with better tools.

## 10. No evals, no agent

Agents are non-deterministic and stateful. You cannot ship one without a way to know it's getting better or worse over time.

- Start with ~20 real queries with known good outcomes. Not a perfect benchmark — just enough to detect regressions.
- LLM-as-judge with pairwise comparison ("which response is better?") gives more signal than Likert scoring.
- Look at the actual traces. Read what your agent did on 10 random runs every week. Surprises live in the traces, not the aggregate metrics.

If you don't have evals yet, that's the next thing to build — before more tools, before more capability, before scaling.

## 11. Observability and checkpoints from day one

Agents fail in ways that one-shot LLM calls do not: mid-loop crashes, deploys landing during a long-running session, identical inputs producing divergent traces. Build for it.

- **Log every LLM call** with model, message count, token estimate, turn number.
- **Log every tool call** with name, args, duration, output size or preview, success/failure.
- **Persist state per run** — turns so far, tool-call history, current plan. Make resume possible.
- **Trace by decision pattern, not by raw conversation** — the conversations are too long to scan; the decision tree is what you need to debug.
- **Rainbow deploys for long-running agents** — don't kill an in-progress run by deploying. Drain workers first.
- **Reproduce before fixing.** When an agent misbehaves, replay the failed run from logs/state before patching anything. Don't "fix" based on a one-line bug description when the trace is sitting in the logs. Same rule as unit tests and frontend bugs: reproduce → diagnose → fix → verify, in that order.

## Security: the "Rule of Two"

For any agent touching untrusted input (user content, web pages, third-party tool outputs), pick **at most two** of:
1. Processes untrusted input.
2. Accesses sensitive data or systems.
3. Takes state-changing or external-comms actions.

All three together is the lethal trifecta — a prompt injection in the untrusted input steers the agent to exfiltrate the sensitive data via the action it can take. Mitigations exist (sandboxing, allowlists, human-in-the-loop) but prompt injection is unsolved; design the agent so a successful injection can't reach all three corners.

## Common failure modes and which principle catches each

| Failure | Principle |
|---|---|
| Webhook storm spawns 500 parallel agents | 2 (queue) |
| Agent loops forever on the same broken tool call | 3 (bounds) + 4 (errors as results) |
| Context window blows up at turn 7 | 3 (token budget) + 6 (compaction) |
| Tool returns 10MB; next call 400s | 5 (paginate/truncate) |
| Model confuses two similar tools | 5 (naming + descriptions) |
| 15 subagents spawned for a one-shot lookup | 3 (concurrency cap) + 9 (earn it) |
| Mega-prompt accuracy is 60% | 1 (workflow first) + 7 (decompose) |
| Prompt injection exfiltrates customer data | Rule of Two |
| "It used to work" but no one knows when it broke | 10 (evals) + 11 (observability) |

