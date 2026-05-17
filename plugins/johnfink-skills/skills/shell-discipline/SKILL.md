---
name: shell-discipline
description: Use when (a) you've re-derived session state more than once (sourcing a venv twice, re-reading an env file, re-running `pwd`/`git status` for info you already have), (b) the same permission prompt has come up more than once for one tool (`sed`, etc.), (c) you've worked around an env-level problem at least once and might hit it again (missing tool, wrong PATH, broken venv), or (d) you have multiple independent shell commands you're about to run sequentially when they could be parallel. NOT needed for ordinary one-off shell commands — load this skill only when one of those patterns is actually present.
---

# Shell discipline

The user's time is the scarcest resource in the loop, and the small frictions compound. Re-sourcing the venv on every command, re-reading the same file, asking the user to approve the same `sed` invocation 20 times in a session — each one is small, together they make the session feel like wading through mud.

## 1. Cache session state — don't re-derive it on every command

When you've activated a venv, read an env file, learned a config value, or otherwise established state, **treat it as known for the rest of the session.** Don't re-do the work.

- You sourced `.env` once → the variables are known. Don't `cat .env` on the next command to "double-check."
- You activated a venv / `uv run` / `mise` environment → subsequent commands run in it until you decide otherwise.
- You read a config file or schema → it's in context. Don't re-read to check the same field.
- You ran `pwd`/`git status`/`ls` 30 seconds ago → don't re-run to confirm what you already saw.

If the state genuinely might have changed (you ran a command that mutates it, or a long time has passed), re-check. Otherwise, trust your context.

## 2. Avoid tools that trigger repeated permission prompts when an equivalent exists

When the user's harness gates a tool and you need that tool 10 times in a row, **switch tools, don't keep prompting.** A user who has to approve `sed` 20 times will eventually quit the session.

- **Text edits**: use the `Edit` tool, or `ruff format` / `prettier`, or write a Python/Node script. Reserve `sed` for genuine one-shots.
- **Multiple file moves/renames**: write a small script and run that one command.
- **Repeated commands of the same shape**: wrap in a script the user approves once instead of N approvals for N near-identical commands.

The principle: **the user approves once, the work runs many times** — not the other way around.

## 3. A permission grant is usually session-wide intent

If the user approved `npm install` once, they didn't mean "this one time only." They meant "this category of command is fine." Don't re-prompt for the next install in the same session.

Read the room: a permission grant signals scope. Idempotent or read-only commands rarely need re-approval. Destructive ones (anything irreversible, anything cross-machine) do.

## 4. Run independent commands in parallel

Multiple Bash calls with no dependency on each other → issue them in the same tool block. `git status` + `git diff` + `git log` is one tool block, not three. Same for checking multiple paths, running multiple linters, hitting multiple endpoints.

Sequential calls that could be parallel are wasted wall-clock time, and over a session they add up.

## 5. Don't re-read files you already have in context

You read the file. You have it. Work from that.

Exceptions: you (or a tool) just modified it; or you genuinely don't remember enough of the content to act. Otherwise, re-reading is noise — it costs a tool call, a permission check, and reader attention, in exchange for information you already had.

## 6. Surface persistent env problems — don't silently work around them

**This is the load-bearing principle.** If you find yourself working around the same env-level problem more than once — `pyright` not on PATH, a missing tool, a venv that won't activate, a config value defaulting to the wrong thing — **stop working around it and tell the user.**

Bad pattern:
- `pytest` fails because `pyright` isn't on PATH.
- You work around it with the full path: `~/.local/bin/pyright`.
- The same thing comes up 20 minutes later in the same session. You silently use the full path again.
- Next session: same thing. The user never finds out their env is broken.

Good pattern:
- `pytest` fails because `pyright` isn't on PATH.
- *"Heads up — `pyright` isn't on your PATH. I'll use `~/.local/bin/pyright` for now, but you'll probably want to add `~/.local/bin` to PATH or `mise use python@3.12 pyright` so this just works going forward. Want me to make that change now?"*

The rule:

- **Once**: work around silently is fine.
- **Twice in a session**: surface explicitly, propose a fix, ask whether to apply it.
- **Three times**: you've already failed to surface it. Stop and surface now.

The user almost always wants to fix the env once and never see this again. Don't deprive them of that option by absorbing the friction yourself.

## Failure modes

| Symptom | Fix |
|---|---|
| Sourcing the venv on every command | Source once, treat as session state |
| Re-reading `.env` for every shell call | Read once, carry variables forward |
| `sed` prompting 5 times in a row | Switch to Edit / a script / a different tool |
| User approving `npm install` four times in one session | First approval covers the category |
| Same workaround applied 3+ times in a session | Surface the underlying problem + propose a fix |
| Re-reading a file you read 30 seconds ago | Trust your context |
| Three sequential bash calls that could be parallel | One tool block, three calls |
