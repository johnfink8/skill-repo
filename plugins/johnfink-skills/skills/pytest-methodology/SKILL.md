---
name: pytest-methodology
description: Use when (a) creating a new test file or test case, (b) making a test DESIGN decision (parametrize vs. duplicate, fixture vs. inline, what to mock vs. integrate, splitting a test that asserts multiple behaviors), (c) writing a failing test to reproduce a reported bug, or (d) reviewing tests for quality smells (over-mocking, framework testing, hidden indirection through fixtures). NOT needed for minor edits to existing well-shaped tests — load only when a test-design decision is actually on the table.
---

# Pytest methodology

> **Draft — first poke.** Edit the rules below to match what you actually want.

A handful of principles that keep a test suite useful instead of a tax.

## 1. Tests describe behavior, not implementation

A test name should answer "what does this guarantee?" — `test_invite_email_is_sent_when_user_signs_up`, not `test_send_email_called_once`. If the implementation changes but behavior doesn't, the test should still pass. Tests that break on refactor-without-behavior-change are noise.

## 2. Arrange-Act-Assert, visibly

Three blank-line-separated chunks per test. If the arrange section is more than ~5 lines, lift it into a fixture. If you can't see all three chunks on screen at once, the test is too long.

## 3. Parametrize over duplication

Three tests that differ only in input → one `@pytest.mark.parametrize`. Tests that share *some* setup but assert different things → separate tests, shared fixture. Don't parametrize when the cases need different assertions; that's a readability trap.

## 4. Fixtures for state, not for indirection

Fixtures are great for "give me a logged-in user" or "give me a temp DB". They are bad for hiding the actual thing under test. If a reader has to chase three fixtures to figure out what's being tested, the test is over-fixtured.

## 5. One logical assertion per test

Multiple `assert` lines are fine when they all describe the same behavior (`assert response.status == 200; assert response.json["id"] == user.id`). But two unrelated behaviors in one test means a failure in one masks the other. Split.

## 6. Don't test the framework

No tests for `assert User.objects.create(name="x").name == "x"`. No tests that exercise only the ORM, the HTTP library, or pydantic's validators. Test *your* logic — the place where you made a decision.

## 7. Pick a mock strategy on purpose

Mocking is a tool with a cost. Default: mock external services (network, third-party APIs, the clock). Don't default-mock your own code — that produces tests that pass while production is broken. Integration tests against a real DB / real Redis / real filesystem catch the bugs unit tests miss.

## 8. Fast feedback or you won't run them

If the unit suite takes more than ~30s, people stop running it before pushing. Split slow tests behind a marker (`@pytest.mark.slow` or `@pytest.mark.integration`) and exclude by default; run them in CI and pre-merge.

## 9. Failing test before fix

For any reported bug: write the test that reproduces it, watch it fail, then fix. This proves the test actually catches the bug. Skipping this step is how you end up with a "fix" that never gets exercised.

## 10. Don't catch exceptions to silence them

`pytest.raises` is for *expected* exceptions you want to assert on. A bare `try/except` in a test is almost always wrong — it converts a test failure into a test pass.
