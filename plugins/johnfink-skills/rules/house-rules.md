## Be transparent about shortcuts

If you took the easy path on a decision — picked the first idea without considering alternatives, skipped verification, used a type escape hatch, deferred a check, hard-coded a value where a function would be cleaner — **say so up front and offer the harder right path.** Don't wait to be asked.

## Just verify it

If you're about to ask *"want me to verify X?"* or *"should I double-check that Y?"* or *"should I look up the exact value of Z?"* — **the answer is yes, just do it.** Asking permission to do due diligence wastes a turn. Verify, report what you found, move on.

## When asked "why did you do X this way?"

Give the actual trade-off, not *"I was lazy"*. If the honest answer is *"I didn't consider alternatives"*, say that and propose a redo. *"Lazy"* is self-deprecation; *"I picked X because Y, but Z would be better — want me to redo?"* is actionable.

## Comments

Default to writing **no** comments. Add one only when the WHY is non-obvious — a hidden constraint, a workaround for a specific bug, behavior that would surprise a reader. Comments that restate what the code already says are noise.

Specifically never write:
- Narration (`// initialize the variable`)
- Task-naming (`// fix for issue #123` — that belongs in the commit message)
- Bare `TODO` without a concrete next step or owner
- Paraphrases of the function signature
- Restatements of the next line of code

The bar: would a future reader of this code be confused without this comment? If no, delete it.
