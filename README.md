# Claude Code skills

Personal skills marketplace for [Claude Code](https://claude.com/claude-code).

## Install on a new machine

```
/plugin marketplace add johnfink8/skill-repo
/plugin install johnfink-skills@johnfink
```

(Replace the GitHub slug if you fork.)

Verify with `/plugin` — you should see the `johnfink-skills` plugin and its skills will appear in skill listings as `johnfink-skills:<skill-name>`.

## Skills

- **trial-data-discipline** — empirical trials, evals, fixtures: where to put data, how to separate capture from analysis.
- **commit-preferences** — terse, informal, hint-don't-restate commit messages. No trailers.
- **pytest-methodology** — how to write Python tests that stay useful.
- **e2e-testing** — when e2e is right, selector strategy, anti-flake discipline.
- **type-safety** — TypeScript / Python typing. The rules around `as` / `# type: ignore` / `any`.
- **formatting-standards** — formatter-as-source-of-truth, defaults per language.
- **agentic-llm** — building LLM-in-a-loop systems: queue inputs, bound the loop, errors-as-results, tool UX.
- **autonomy** — don't punt verification to the user; plan browser automation and CLI access from the first commit.
- **shell-discipline** — cache session state, avoid permission-prompt thrash, surface persistent env problems with a fix.

## Always-on rules (no skill triggering required)

A `SessionStart` hook injects [`plugins/johnfink-skills/rules/house-rules.md`](plugins/johnfink-skills/rules/house-rules.md) into context at the start of every session. These are the rules that apply regardless of task — transparency about shortcuts, comment hygiene, how to respond to "why did you do X this way?" — and live as a hook because their trigger condition is "always," not "matches description."

### Why a hook instead of CLAUDE.md?

CLAUDE.md isn't plugin-able. Marketplaces ship skills, hooks, agents, and commands — not CLAUDE.md content. Even if they could, CLAUDE.md often holds per-machine configuration that shouldn't be clobbered: things like *"you're in a Docker container, don't try to spawn Docker"*, *"pyright lives at this nonstandard path"*, or project-specific facts that don't belong in a portable marketplace. A `SessionStart` hook ships the always-on rules without touching CLAUDE.md, so portable guidance and local config coexist cleanly.

## Hook-enforced anti-patterns

A `PreToolUse` hook on the `Bash` tool injects a warning into Claude's context (model-visible via `additionalContext`, non-blocking) when it spots a *string-as-code* anti-pattern — a script piped into a language interpreter instead of being written to a real file:

- A heredoc piped to a language interpreter (`python <<EOF`, `node <<EOF`, `ruby <<-EOF`, `perl <<EOF`, `php <<EOF`) when the command runs 30+ newlines. Smaller heredocs are tolerated. Heredocs into non-interpreters (`cat`, `psql`, `tee`, `bash`) are always fine at any length.
- An inline `-c` / `-e` script in a language interpreter (`python -c`, `node -e`, etc.) with substantial content (multi-line or >120 chars).

The warning carries a transferable *why* — the piped script skips your formatter and linter, isn't somewhere you (or the user) can diff or re-run — and each form cross-references the other so the natural pivot ("just use `-c` instead") is preempted. The remedy is always: use the `Write` tool to create a real script file and invoke that.

This is the **enforcement** half of a rule that lives advisorily in the `autonomy` and `trial-data-discipline` skills. Skills tell Claude what should happen; hooks catch when it doesn't.

Lives at [`plugins/johnfink-skills/hooks/bash-anti-patterns.py`](plugins/johnfink-skills/hooks/bash-anti-patterns.py); test cases in [`test_bash_anti_patterns.py`](plugins/johnfink-skills/hooks/test_bash_anti_patterns.py).

## Updating

Edit the `SKILL.md` files in `plugins/johnfink-skills/skills/`, commit, push. Bump `version` in `plugins/johnfink-skills/.claude-plugin/plugin.json` for meaningful changes.

On other machines:

1. `/plugin marketplace update johnfink` — refresh the marketplace listing.
2. Then update the installed plugin. There's no one-shot CLI for this:
   - Easiest: open `/plugin`, go to the **Installed** tab, update from there.
   - Or: `/plugin uninstall johnfink-skills@johnfink` then `/plugin install johnfink-skills@johnfink`.
   - Or: enable auto-update on the marketplace (`/plugin` → **Marketplaces** tab) so future versions pull at startup.

## Layout

```
.claude-plugin/marketplace.json   # marketplace manifest
plugins/johnfink-skills/
  .claude-plugin/plugin.json      # plugin manifest
  skills/<skill-name>/SKILL.md    # one skill per dir (lazy-loaded)
  hooks/hooks.json                # SessionStart + PreToolUse hook config
  hooks/bash-anti-patterns.py     # PreToolUse: warn on ephemeral scripts
  rules/house-rules.md            # always-on rules injected by SessionStart
```
