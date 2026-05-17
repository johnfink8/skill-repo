---
name: e2e-testing
description: Use when (a) authoring a new e2e/browser test (selector choice, set-up strategy, what to assert), (b) investigating a flaky test, (c) deciding whether e2e is the right tier for a behavior (vs. unit/integration), (d) reviewing existing e2e tests for design issues, or (e) anyone is about to reach for `sleep` / `waitForTimeout` / `--retries=3` (which is always wrong). NOT needed for minor edits to existing well-shaped e2e tests — load only when an e2e design decision or flake investigation is on the table.
---

# E2E testing

> **Draft — first poke.** Edit the rules below to match what you actually want.

E2E tests are the most valuable tests when they pass and the most expensive tests when they fail. Discipline matters more here than in any other tier.

## 1. E2E is the wrong tool for most things

The pyramid is real. E2E covers the seams between layers — auth flow, payment flow, the single critical user journey. It does NOT cover "every form validates correctly" — that's a unit/integration test. If you find yourself writing the 7th e2e test for a CRUD page, stop.

Default: a small e2e suite (single digits of tests for a small app, low double-digits for a big one) covering the journeys you'd ship-block on.

## 2. Selectors: data-testid > role > text > CSS

In priority order:
1. `data-testid="checkout-submit"` — stable, intentional, survives styling changes.
2. `getByRole("button", { name: "Check out" })` — accessible, semi-stable.
3. `getByText("Check out")` — readable but breaks on copy changes.
4. CSS / XPath selectors — last resort, breaks constantly.

If you reach for a CSS selector, first ask: should this element have a testid?

## 3. No `sleep`, ever

`page.waitForTimeout(2000)` is always wrong. It's either too long (slow tests) or too short (flake). Use the framework's auto-waiting (`expect(locator).toBeVisible()`, `waitForResponse`, `waitForURL`). If something *truly* has no observable change to wait for, that's a product bug — fix the product, not the test.

## 4. Each test owns its data

Don't share user accounts, fixtures, or DB state across tests. Each test creates what it needs (via API, not UI — see #5) and uses a unique identifier. Otherwise: test order matters → flake → suite-wide pin.

## 5. Set up via API, exercise via UI

E2E tests are slow. Don't burn 30 seconds clicking through signup + onboarding just to test the dashboard. Hit the API to create the user in a logged-in state, then `goto("/dashboard")` and start exercising.

The only thing you should test through the UI is the thing under test.

## 6. Flake budget is zero

A flaky test is worse than no test — it teaches the team to ignore failures. When a test flakes:
1. Reproduce locally with `--repeat-each=20`.
2. Find the actual race / order dependency / dirty state.
3. Fix it.

Never `--retries=3` to hide a flake. Never skip a flaky test "for now." Either fix it or delete it.

## 7. Test names describe the journey

`test_user_can_complete_checkout_with_saved_card`, not `test_checkout_3`. The name should let an oncall page-reader know what broke without opening the file.

## 8. Headed mode for debugging, headless for CI

Run in headed mode (with the browser visible) when authoring or debugging — you see what the test sees. Run headless in CI. If a test passes headless and fails headed (or vice versa), that's a real signal, not a quirk to work around.

## 9. Screenshots and traces on failure

Configure the runner to capture screenshot + trace + video on failure. The "it failed in CI but I can't reproduce" loop ends when you can replay the failed run.
