#!/usr/bin/env python3
"""PreToolUse hook: catch ephemeral-script anti-patterns in Bash commands.

Warns (does not block) when a Bash command contains:

- A substantial heredoc piped to a language interpreter (``python <<EOF``,
  ``node <<EOF``, etc.) — 30+ newlines in the command, ≈ 30-line script
  body. Smaller heredocs are tolerated. Heredocs into non-interpreters —
  ``cat`` to bootstrap a config file, ``psql`` for SQL, ``tee`` to fan out,
  ``bash`` to run shell — are fine at any length.
- An inline ``-c`` / ``-e`` script in a language interpreter with
  substantial content (multi-line or > 120 chars).

The warning nudges the model to promote the content to a real file via the
``Write`` tool and invoke that file. The rationale lives in the ``autonomy``
and ``trial-data-discipline`` skills.

Input:  JSON on stdin (Claude Code PreToolUse format).
Output: JSON on stdout with ``systemMessage`` if any pattern matched.
Always exits 0 — never block a tool call due to detector errors.
"""

import json
import re
import sys

# Language interpreters whose embedded scripts we want to discourage.
# Excludes ``bash``/``sh`` (heredocs into shell are a normal pattern) and
# data tools (``cat``, ``psql``, ``mysql``, ``sqlite3``, ``tee``, etc.).
INTERPRETERS = r"python3?|node|nodejs|ruby|perl|php"

# Interpreter command, followed by anything-not-a-redirect, then a heredoc
# marker. Catches ``python <<EOF``, ``python3 -u <<-'EOF'``, etc.
INTERPRETER_HEREDOC_PATTERN = re.compile(rf"\b({INTERPRETERS})\b[^<]*<<-?\s*['\"]?\w+")

# Interpreter ``-c`` or ``-e`` flag for an inline script.
INLINE_SCRIPT_PATTERN = re.compile(rf"\b({INTERPRETERS})\s+-[ce]\b")

HEREDOC_WARNING = (
    "Heredoc piped to an interpreter is string-as-code: skips your formatter "
    "and linter, isn't a file you (or the user) can diff or re-run. Pivoting "
    "to `-c` / `-e` has the same problem — don't. Use the Write tool to "
    "create a real script file."
)
INLINE_SCRIPT_WARNING = (
    "Substantial inline `-c` / `-e` is string-as-code: skips your formatter "
    "and linter, lost from history, isn't a file you (or the user) can diff "
    "or re-run. Heredoc into an interpreter has the same problem. Use the "
    "Write tool — a real script file."
)


def main() -> None:
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    if input_data.get("tool_name") != "Bash":
        sys.exit(0)

    command = input_data.get("tool_input", {}).get("command", "")
    if not command:
        sys.exit(0)

    warnings: list[str] = []

    # Heredoc into a language interpreter, but only when egregious.
    # A 3-line heredoc into python is forgivable; a 30+ line script
    # piped in deserves to be a real file. Threshold is total newlines
    # in the command (≈ heredoc body length).
    if INTERPRETER_HEREDOC_PATTERN.search(command) and command.count("\n") >= 30:
        warnings.append(HEREDOC_WARNING)

    # Inline ``-c`` / ``-e`` with substantial content.
    inline_match = INLINE_SCRIPT_PATTERN.search(command)
    if inline_match:
        after = command[inline_match.end() :].lstrip()
        if "\n" in after or len(after) > 120:
            warnings.append(INLINE_SCRIPT_WARNING)

    if warnings:
        # `additionalContext` is the documented model-visible field for
        # PreToolUse. `systemMessage` would only show a user-facing banner;
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": "\n".join(warnings),
            }
        }
        print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()
