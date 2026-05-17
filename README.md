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

## Updating

Edit the `SKILL.md` files in `plugins/johnfink-skills/skills/`, commit, push. Bump `version` in `plugins/johnfink-skills/.claude-plugin/plugin.json` for meaningful changes.

On other machines: `/plugin marketplace update johnfink` then `/plugin update johnfink-skills@johnfink`.

## Layout

```
.claude-plugin/marketplace.json   # marketplace manifest
plugins/johnfink-skills/
  .claude-plugin/plugin.json      # plugin manifest
  skills/<skill-name>/SKILL.md    # one skill per dir
```
