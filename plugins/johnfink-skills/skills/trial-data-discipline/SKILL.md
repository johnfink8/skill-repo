---
name: trial-data-discipline
description: Use whenever the user is designing, running, or iterating on empirical trials — probes, evals, A/B tests, fixtures, recording rigs, or any code that captures human-in-the-loop data (mic recordings, screen captures, prompted-response sequences). Apply this skill even when the user doesn't say "trial" or "eval" but is clearly about to record themselves, prompt themselves through a test sequence, or set up a "let's see what happens" probe that will be re-run later as the system evolves. Codifies five practices that prevent data loss and enable cheap re-analysis when methodology changes.
---

# Trial data discipline

Empirical work has a characteristic shape: run a probe, look at the data, change something, run again. Small process choices compound over many iterations. These five principles eliminate the most common failure modes — losing data to `/tmp`, losing context when scripts crash, re-prompting humans needlessly.

If you find yourself about to write a "record user audio + analyze + report" script, or wire up a fixture that walks the user through a sequence of stimuli, pause and apply the principles below before writing code.

## 1. Trial data lives with the project, never in /tmp

Default location: `<project>/trials/<probe-name>/<YYYYMMDD-HHMMSS>/`. Gitignore the parent (`trials/`). Even "throwaway" trial data belongs here, because the moment methodology changes, you'll want to re-analyze what you already collected.

`/tmp` is the wrong choice for trial data:
- It evaporates on reboot.
- macOS, systemd-tmpfiles, and many CI environments aggressively clean recent files.
- "I just ran the probe an hour ago" + "I rebooted for a system update" = lost recordings + needing to re-prompt the human, which is rude.

Project-local also makes the data discoverable later. Someone (you, future-you, a teammate) will want to find "the recordings from when we tested threshold 0.6" — having them at a predictable project path is the difference between a 10-second answer and an archaeology dig.

## 2. Separate capture from analysis into different scripts

Two scripts, not one:

- `capture.py` — opens devices, prompts the user (if applicable), records, writes raw data and a manifest to disk. Stops there.
- `analyze.py` — reads the trial directory, runs all the processing (VAD, ASR, scoring, plotting, whatever), produces a report.

Do not bundle "play stimulus → record → process → grade → report" into a single script. A bug in any step after the recording forces re-recording. With separation:

- Analysis bug? Fix it and re-run analysis. The human goes about their day.
- New scoring metric? Re-run analysis. New data not needed.
- Methodology question ("what would happen at threshold 0.7"?) Re-run analysis with different params.

The capture script's only job is to land bytes plus context on disk, durably, then exit. Everything fancy belongs in analysis.

### Where the scripts live: in the trial directory itself

`capture.py`, `analyze.py`, and any other run/grade scripts for a trial belong **inside that trial's timestamped directory**, next to the data they produce or consume. Not in `.scratch/`, not in `scripts/`, not at the project root.

```
trials/<probe>/20260516-070112/
  capture.py        ← the code that produced the data, frozen at run time
  analyze.py        ← reads ./manifest.json, ./*.wav, writes ./analysis_report.md
  manifest.json
  NOTES.md
  capture.wav
  analysis_report.md
```

Why colocate:

- **Reproducibility for free.** Six months later, "the code that produced this data" is literally next to the data. No git archaeology to figure out which version of `capture_probe.py` was running on a given day.
- **Methodology changes get their own folder.** If you tweak the script — added a cell, changed a stimulus, raised a gain — that's a new trial (new timestamp, new scripts). Diff `trials/<probe>/<ts-A>/capture.py trials/<probe>/<ts-B>/capture.py` to see exactly what changed between runs.
- **Self-contained handoff.** Sharing or archiving a trial means zipping one directory. No "and also grab this script from `.scratch/`."
- **`.scratch/` is for throwaway exploration.** Once you're capturing real data, you're not throwing it away — promote the script into the trial dir.

The small cost (a few KB of duplicated Python across runs) is dwarfed by the reproducibility win. Refactor common helpers into a `trials/<probe>/_common.py` only when you have 3+ trials and the duplication actually hurts.

## 3. Always write a manifest sidecar

Alongside the raw data files, write a `manifest.json` (or `manifest.jsonl` if you prefer streaming append) that records:

- **What was being tested** — stimulus text, prompt content, fixture name
- **In what order** — sequence index for each event
- **Parameters used** — model versions, thresholds, gains, anything tunable
- **Wall-clock timestamps** — when each event fired, relative to recording start
- **Expected outcomes** (if any) — for probes with ground truth (barge prompts, A/B labels)

Without a manifest, raw bytes go stale fast. Six months from now, `recording.wav` is just bits; with `manifest.json` next to it, you know "this is the 2026-05-16 barge probe, the segment from 4.2s-4.8s corresponds to the 'stop' prompt at index 0."

**Append events as they fire, not in one dump at the end.** If the capture script crashes mid-session, the manifest should reflect what *actually* got captured, not the original plan. JSONL with one event per line, fsync after each, is reasonable for human-in-the-loop sessions where stakes are higher than write speed.

## 3a. Pair the manifest with a NOTES.md (what / why / how)

The manifest captures **structured** parameters (sizes, paths, thresholds). The notes capture the **narrative** — three sections, one paragraph each:

- **What** — what the trial measured. The hypothesis or question. One or two sentences.
- **Why** — what motivated this trial. What had we just learned that made this the next question? What would the answer unblock?
- **How** — the methodology. What was varied, what was held constant, what was the eval target. Anything non-obvious about the setup that someone re-reading wouldn't infer from manifest + analysis_report alone.

```
trials/
  <probe>/
    20260516-070112/
      manifest.json           ← structured (what, when, with what params)
      NOTES.md                ← prose (what we were trying to learn, why, how)
      capture.wav             ← the data
      analysis_report.md      ← results
```

Why both: the manifest is for tooling (re-running the analysis, indexing, diffing). NOTES.md is for *humans coming back to this trial* — including future-you who has forgotten why this experiment existed. The structured field "question" alone in a manifest tends to be too terse; a paragraph of motivation pays off when you're trying to remember the larger investigation a trial fit into.

A good NOTES.md template:

```markdown
## What
One or two sentences on the hypothesis / question.

## Why
What did we just learn that made this the next thing to check? What
investigation does this trial sit inside? What would the answer let us do?

## How
Brief methodology. What was varied. What was the eval target. Anything
non-obvious about the protocol or trade-offs.

## Findings (optional)
A two or three sentence executive summary so you don't have to re-read
analysis_report.md to remember the conclusion.
```

## 4. Analysis must be re-runnable on saved data alone

`uv run trials/<probe>/<ts>/analyze.py` is the canonical interface — `analyze.py` lives next to the data and reads from its own directory by default (no required CLI arg pointing at the trial dir). The analysis script needs:

- The saved trial dir (its own dir; `Path(__file__).parent`)
- Access to whatever inference services it always needed (ASR, classifiers, etc.)
- Configuration (thresholds, etc.) — ideally as CLI args or config file, not hardcoded

It must **not** require:

- A live audio device
- The human to press Enter
- A device to be in a particular state
- Anything that wasn't true when the data was captured

The test for this: after the human has gone home for the day, can you re-run analysis with a different threshold and get a comparable result? If yes, you're good. If no, the script is doing too much.

## 5. Timestamped run directories

`trials/<probe>/<YYYYMMDD-HHMMSS>/` per capture. Don't overwrite. Don't re-use the same path for "this run" and "the last run."

Benefits:
- The latest is easy to find (`ls -t trials/<probe>/ | head -1`).
- Old runs remain available for comparison.
- Reproducibility — when someone says "what changed between runs?", you can diff manifests and re-run analysis on both.

Many codebases already do this for batch evals (`out/<timestamp>/`, `out-asr/<timestamp>/`). Extend the convention to all trial work, including ad-hoc probes.

## Putting it all together — the canonical layout

```
trials/
  <probe-name>/
    20260516-070112/
      capture.py             ← the code that produced the data
      analyze.py             ← the code that reads it
      NOTES.md               ← what / why / how
      manifest.json          ← structured params + per-event log
      capture.wav            (or capture.caf, capture.npz, ...)
      analysis_report.md     ← written by analyze.py, kept with the capture
    20260516-091445/
      capture.py             ← may differ from the prior run — that's the point
      analyze.py
      NOTES.md
      manifest.json
      capture.wav
      analysis_report.md
```

The capture script writes everything up to (and including) `manifest.json` and `capture.wav`. The analysis script reads those and writes `analysis_report.md` (or `.json`) into the same directory. Multiple analysis runs against the same capture? Write `analysis_<config-name>.md` etc.

Each timestamped trial dir is self-contained: zipping it captures the code, the data, the methodology, and the results in one bundle.

## When this skill applies

- Designing or running any probe, eval, A/B test, fixture, repeatable trial.
- About to write code that records the user (mic, screen, keystrokes) or prompts them through a sequence.
- Setting up "let me compare this run to the previous one" workflows.
- Building eval rigs for models / services where methodology is likely to evolve.

## When this skill does not apply

- One-shot scripts where the output **is** the answer — "compute the SHA of this file", "show me what's in this PDF". The methodology is the request itself.
- Unit tests — the test harness IS the methodology and is reproducible by definition. (But a test fixture that records a video of a UI flow for a-snapshot comparison? That's a trial — applies.)
- Pure refactors / bug fixes with no measurement component.

## Common slips to watch for

- **"I'll move it out of /tmp later."** You won't. Write it to the right place the first time.
- **"This is just a quick probe."** Quick probes are the ones most likely to get re-run after a small parameter change.
- **"I'll add a manifest if I need it."** You'll need it. Write it from the start.
- **One script that records AND analyzes "to keep it simple."** This is a trap. The simplicity is illusory once you change the analysis.
- **Overwriting `latest.wav` each run.** You will want yesterday's `latest.wav` exactly when you've overwritten it.
- **Leaving the capture script in `.scratch/`** while the data lives in `trials/<probe>/<ts>/`. The code and the data drift apart; later you can't tell which version of the script produced which capture. Promote the script into the trial dir the moment you're capturing real data.
