---
name: commit-preferences
description: Use whenever writing a git commit message, drafting a PR title, or generating release notes. Enforces a terse, informal commit-message style — hints at the diff rather than restating it, no trailers. Apply on every commit, including auto-generated ones after edits.
---

# Commit preferences

## The rule

**One terse, informal sentence. Hint at what's in the diff — don't restate it. No `Co-Authored-By` trailers.**

That's the whole rule. Everything below is just clarification.

## What "terse and informal" looks like

Good:
- `pull the retry loop out into its own helper`
- `fix the off-by-one in the pagination guard`
- `bump pydantic, mostly type stubs churn`
- `kill the unused websocket fallback`

Bad (too formal / restates the diff):
- `Refactor: extract retry logic into separate helper function`
- `Fix off-by-one error in pagination boundary check by adjusting comparison operator`
- `chore(deps): bump pydantic from 2.5.0 to 2.6.1`

Lowercase first letter is fine. No period at the end is fine. Conventional Commits prefixes (`feat:`, `fix:`, `chore:`) are NOT wanted unless the repo already uses them.

## "Hint at the diff, don't restate it"

The diff is right there — anyone reading the commit will see what changed. The message should answer *what was the move*, not *what lines changed*. If the message reads like a description of the patch, it's too literal.

- Restates the diff: `add null check to user.email access in send_invite`
- Hints at the move: `guard send_invite against the no-email case`

## No trailers

Do not append:
- `Co-Authored-By: Claude <...>`
- `🤖 Generated with Claude Code`
- `Signed-off-by:` (unless the repo's CI requires it — check first)

If a default template wants to add one, strip it.

## Multi-line commits

Default to single-line. Use a body only when the *why* genuinely won't fit in one sentence and isn't obvious from the diff — e.g. "we tried X first and it deadlocked, so this is Y instead." Even then, keep the body short.

## PR titles and descriptions

Same rule applies, with a small allowance for PR bodies: they can be **a little** more verbose than a commit message, but the principle is unchanged — **let the code stand for itself, don't list every detail.**

- **PR title**: same as a commit message. One terse, informal sentence that hints at the move.
- **PR body**: a short paragraph or a few bullets covering *why* and *anything the reviewer needs to know that isn't in the diff* (motivation, trade-offs considered, follow-ups left out). Not a line-by-line tour of the patch.

Bad PR body (restates the diff):
> This PR adds a new `RetryPolicy` class with `max_attempts` and `backoff` parameters. It updates `HttpClient.__init__` to accept a `retry_policy` argument. It modifies the `send` method to use the new policy. It also updates the tests in `test_http.py` to cover the new behavior.

Good PR body:
> Pulls retry logic out of `HttpClient` into a `RetryPolicy` so callers can swap strategies. Left exponential backoff as the default since that's what we use everywhere — easy to override per-call when we need to.

If the PR description template demands a list-of-changes section, fill it tersely; never use it as an excuse to re-narrate the diff.

## When the user explicitly overrides

If the user asks for a longer message, conventional commits, a specific trailer, etc. for a particular commit, follow that. The rule above is the default, not a hard constraint.
