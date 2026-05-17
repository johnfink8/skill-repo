---
name: formatting-standards
description: Use when (a) setting up a new project and choosing/configuring a formatter, (b) someone is proposing a manual formatting override or arguing about style, (c) reformatting legacy code or deciding whether to bundle reformatting with unrelated changes, (d) deciding line-length / import-order / quote-style / trailing-comma config, or (e) adding pre-commit hooks or editor config (`.editorconfig`). NOT needed for ordinary code edits — modern formatters already handle those, and the principle is "let the formatter decide" which only matters when a decision is actually being made.
---

# Formatting standards

> **Draft — first poke.** Edit the rules below to match what you actually want.

Formatting is a solved problem. The only correct amount of time to spend thinking about it is zero.

## 1. The formatter is the source of truth

If a file has a configured formatter (`ruff`, `black`, `prettier`, `gofmt`, `rustfmt`, etc.), the formatter decides. Not your aesthetic preference, not the surrounding code's style, not "what looks cleaner here." Run the formatter and commit what it produces.

If the formatter and your taste disagree, the formatter wins.

## 2. Defaults per language

Pick one per language and stick with it:

- **Python**: `ruff format` (also handles linting via `ruff check`). Replaces black + isort + flake8.
- **TypeScript / JavaScript**: `prettier` for formatting, `eslint` for linting. Keep them in separate concerns.
- **Go**: `gofmt` / `goimports`. No discussion.
- **Rust**: `rustfmt` with defaults.
- **Shell**: `shfmt -i 2`.
- **Markdown / JSON / YAML**: `prettier`.

For any new project: install the formatter, add the config file, wire it to pre-commit and editor-on-save. Day one.

## 3. Line length: 100

- Python: `ruff` line-length 100.
- TS/JS: `prettier` printWidth 100.
- Go: doesn't care, don't argue.

88 (black default) is too narrow for modern monitors. 120 is too wide for side-by-side diffs. 100 is the right answer.

## 4. Imports: sorted, grouped, no manual ordering

- Python: `ruff` sorts imports (`I` rule), three groups (stdlib / third-party / first-party).
- TypeScript: prettier + an import sort plugin or eslint rule.

Never reorder imports by hand. If the tool's order is "wrong," the tool is right.

## 5. Trailing commas, always

Multi-line literals/arguments get trailing commas. They make diffs cleaner (adding an item touches one line instead of two) and they prevent merge conflicts. Every modern formatter does this by default — don't disable it.

## 6. Don't reformat unrelated code

When editing a file with inconsistent legacy formatting, format only the lines you're already touching, OR run the formatter on the whole file as a *separate* commit. Mixing "fix bug" with "reformat 400 lines" makes the diff unreviewable.

## 7. EditorConfig in every repo

A `.editorconfig` at the repo root covers indentation, line endings, trailing whitespace, and final newlines for all the editors in the world without needing per-editor config. Cheap insurance.

```
root = true

[*]
indent_style = space
indent_size = 2
end_of_line = lf
charset = utf-8
trim_trailing_whitespace = true
insert_final_newline = true

[*.py]
indent_size = 4

[Makefile]
indent_style = tab
```

## 8. Pre-commit, not pre-push

Format-on-save catches 95%. Pre-commit hook catches the rest. Pre-push is too late — by then the unformatted code is in your history. CI as the final backstop.

## 9. What NOT to argue about

These are settled — do not relitigate per-project:
- Tabs vs spaces (spaces, except where convention demands tabs — Go, Makefiles).
- Quote style (whatever the formatter picks).
- Semicolons in JS (whatever the formatter picks).
- Function brace style (whatever the formatter picks).

If someone wants to argue, point them at the formatter config.
