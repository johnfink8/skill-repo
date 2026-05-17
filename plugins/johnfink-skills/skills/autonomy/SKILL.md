---
name: autonomy
description: Use whenever you're about to ask the user to manually click, refresh, reproduce, or paste output — and when starting any new project, to plan verification infrastructure up front. Don't punt verification to the user when tools exist that let you do it yourself. Triggers on debugging from a user-reported error, building frontend features, 'could you check whether' moments, and anytime you're tempted to outsource a verification step. Especially relevant for frontend work where browser automation (Playwright, Claude in Chrome, Puppeteer MCP) eliminates most 'could you click and tell me what you see' handoffs.
---

# Autonomy

You are not the user's QA tester, and the user is not yours. When the user gives you an engineering task, your job is to do it **and verify it** — not to do it and then ask the user to click around and tell you what they see.

This shows up most painfully in frontend work, where it's easy to slide into "please open the page and report what happens." There's a time and place for that, but **"error reported by the engineer" isn't that.** The user has already done the manual-testing work — they reported the error. Asking them to do it again is wasting their time on a job that's yours.

## 1. Don't ask the user to be your test rig

When the user reports a bug, they've already done the diagnostic legwork. Your sequence is:

1. **Reproduce** it yourself, with the tools available.
2. **Fix** it.
3. **Verify** the fix yourself.
4. **Report** what you did and how you verified it.

Bad responses:
- "Could you open the app and click submit and tell me what you see?"
- "Try refreshing the page and let me know if the error still appears."
- "Can you check whether the API call is going through?"

These are all jobs that browser automation, `curl`, log tailing, or a repro script could do. Asking the user gains no signal beyond what their original report contained — and it costs them another context switch.

Good responses:
- "Reproducing now. *[runs script / opens browser / hits endpoint]* — confirmed, the issue is X."
- "Fixed. Verified by *[specific action]*. Output: *[observable result]*."
- "Reproduced; the root cause is Y; here's the fix; I've verified the fix produces *[observable result]*."

### Write reproducers as real files, not as ephemeral stdin

When you build a reproduction script, write it as **a file in the project** (or in `trials/<probe>/<ts>/` per the trial-data-discipline skill). Don't pipe Python through `bash -c`, don't use shell heredocs, don't quote a 40-line script into a single shell argument. Those ephemera are:

- Hard to debug — you can't step through, you can't re-run with `-v`, you can't add a print statement without re-typing the whole thing.
- Hard to share — "the script that produced this output" needs to exist somewhere.
- Prone to quoting hell — every nested quote and backslash is a new failure mode.
- Lost the moment the shell scrolls.

A repro as a file: re-runnable, diffable, extendable, survives the session. Cost: one extra `Write` call. Benefit: every subsequent iteration is cheaper.

## 2. Plan for autonomy from the first commit

This is the principle that matters most: **the time to build verification infrastructure is before you need it, not when you're already stuck.**

When starting a new project — *especially* anything with a UI — set up:

- **A dev server you can start and inspect.** Predictable port, log file at a known path you can `tail -F`, a health endpoint you can hit.
- **Browser automation, installed and verified.** Playwright (with or without MCP), Puppeteer MCP, Claude in Chrome — pick one, install it, drive it against a hello-world page to confirm it works. Do this *before* writing the actual UI.
- **CLI access to every flow.** If the UI has a "create item" button, there should be an API endpoint or CLI command that does the same thing. Use the CLI for testing; reserve clicking for the UI work itself.
- **Seed scripts.** Create the test state you need (logged-in user, populated DB, queued job) from the command line. No "first you have to sign up and confirm your email."
- **Introspection paths.** Read logs, query the database, check queue depth, dump the current state — whatever the system has, ensure Claude has a CLI or API path to it.

If you skip this setup, the rest of the project is full of "could you check..." messages. That's the most expensive kind of debt: every iteration costs a human roundtrip.

A useful question at project kickoff: *"If I find a bug in two weeks, what's the loop I'll use to reproduce, fix, and verify it without involving the user?"* If you can't answer concretely, build the answer now.

## 3. Distinguish "I genuinely need a human" from "I'm offloading my job"

Some asks of the user are legitimate:

- **Subjective judgment.** "Does this animation feel snappy?" "Is this copy clear?" "Does this match what you want visually?"
- **Credentials you can't safely hold.** "I need you to do this OAuth flow once and paste the token."
- **Physical hardware.** "Plug in your device so I can see what shows up." (Even here, often a `lsusb` is what's needed, not the user's eyes.)
- **External / production state.** "Can you confirm the deploy actually rolled out to your account?"

Asks that are NOT legitimate:

- **"Does the button work?"** — Drive it with browser automation.
- **"Is the error gone?"** — Re-run the repro.
- **"What does the API return?"** — `curl` it.
- **"Did the dev server start?"** — Check the port / read the log.
- **"What's in the network tab?"** — Add logging or use browser automation to capture it.
- **"Can you paste the error message?"** — Tail the log file yourself.

Test: would a human engineer in your position have to ask the user this? If no, you shouldn't either.

## 4. When you must ask, name what you can't do and scope the ask

Don't ask "can you check?". Report what you verified, name the specific thing you couldn't, and give the user a tightly-scoped task.

Bad: "Can you check if it works now?"

Good: "I fixed the validation bug; my repro script confirms the form accepts the input and rejects bad emails. The thing I can't verify is whether the transition animation feels right — could you click through the form once and tell me if it feels smooth?"

The second version: (a) reports what was verified, (b) names what wasn't and why, (c) gives the user a 5-second task instead of an open-ended one.

## 5. Frontend specifically: browser automation before pixel one

The most common autonomy failure is frontend work without a browser tool. If you're about to start frontend work, install the tooling **first**:

1. Install Playwright / Puppeteer MCP / Claude in Chrome — pick one based on what the host environment supports.
2. Run a hello-world automation against `localhost:3000` (or whatever the dev server is) to confirm clicks, navigation, screenshots, and console capture all work.
3. *Then* start writing the actual UI.

The signal you got this wrong: you've written 200 lines of React, asked the user to click through it three times, and you're about to ask again. The expensive thing isn't the React — it's the verification roundtrip. Fix the roundtrip before continuing.

For UI/UX changes, the verification loop should be: make change → screenshot via automation → check the screenshot → either it's right or iterate. The user doesn't enter the loop until the visible result is something worth their judgment.

## 6. Build the system so you can read its state

Many "could you tell me what you see" questions evaporate if the system logs what's happening:

- Structured logs at appropriate levels — `INFO` for happy path, `DEBUG` for diagnostic detail, errors with context.
- Logs written to a known file path you can `tail -F`, not just stdout that disappears.
- Errors that name the cause, not `500 Internal Server Error`.
- Request/response logging at every API boundary the agent touches.
- A `--verbose` or `DEBUG=1` mode that turns on the noisy paths when needed.

If a question would be answered by reading a log, set up the log instead of asking.

## Failure modes

| Symptom | Fix |
|---|---|
| "Could you click X and tell me?" mid-task | Use browser automation |
| Asking the user to reproduce a bug they just reported | Reproduce it yourself from the report |
| Pasting code without running it | Start the dev server and verify |
| Three "let me try this" cycles with no verification | Build a repro script first |
| Frontend work started with no browser tool installed | Install Playwright/Puppeteer/Claude in Chrome before writing UI |
| User pasting error messages by hand | Set up a log file you can tail |
| "Can you check if it works now?" with no specifics | Report what you verified, name what you can't, scope the ask |
| Open-ended "give it a try" hand-off | Verify yourself; only ask the user for things only humans can judge |
