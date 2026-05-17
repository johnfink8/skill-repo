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
  hooks/hooks.json                # SessionStart hook config
  rules/house-rules.md            # always-on rules injected by the hook
```
