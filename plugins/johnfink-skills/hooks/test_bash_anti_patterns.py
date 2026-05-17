#!/usr/bin/env python3
"""Tests for bash-anti-patterns.py.

Runs the hook as a subprocess with realistic PreToolUse JSON inputs and
asserts whether a warning is emitted. Run directly::

    python3 test_bash_anti_patterns.py
"""

import json
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).parent / "bash-anti-patterns.py"


def run_hook(payload: dict) -> dict:
    """Pipe payload as JSON to the hook, return parsed output (or {} if empty)."""
    result = subprocess.run(
        ["python3", str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Hook exited {result.returncode}: {result.stderr}")
    stdout = result.stdout.strip()
    return json.loads(stdout) if stdout else {}


CASES = [
    # (label, command, expect_warning, expected_substring_in_message)
    ("simple ls", "ls -la", False, None),
    # Heredocs into NON-interpreters: always fine (bootstrapping, SQL, etc.)
    (
        "cat heredoc bootstrap env file",
        "cat <<EOF > .env\nDB_HOST=localhost\nDB_PORT=5432\nDB_USER=admin\nDB_PASS=secret\nEOF",
        False,
        None,
    ),
    (
        "psql heredoc for SQL",
        "psql -d obviously_fake_db <<EOF\nselect 1;\nselect 2;\nselect 3;\nEOF",
        False,
        None,
    ),
    (
        "tee heredoc to multiple files",
        "tee a.txt b.txt <<EOF\nshared header\nshared body\nshared footer\nEOF",
        False,
        None,
    ),
    (
        "tiny cat heredoc",
        "cat <<EOF > f.txt\nhello\nworld\nEOF",
        False,
        None,
    ),
    # Small heredocs into interpreters: tolerated (under 30-line threshold).
    (
        "python3 heredoc single-line ignored",
        "python3 <<EOF\nprint('hello')\nEOF",
        False,
        None,
    ),
    (
        "python3 heredoc 5-line ignored",
        "python3 <<EOF\nimport sys\nfor x in range(10):\n    print(x)\nEOF",
        False,
        None,
    ),
    (
        "node heredoc 5-line ignored",
        "node <<EOF\nconst x = 1;\nconsole.log(x);\nconsole.log(x + 1);\nEOF",
        False,
        None,
    ),
    # Large heredoc into interpreter: warns.
    (
        "python3 heredoc 30+ lines warns",
        "python3 <<EOF\n"
        + "\n".join(f"var_{i} = {i}" for i in range(32))
        + "\nprint(sum(locals().values() if isinstance(_, int) else 0))\nEOF",
        True,
        "string-as-code",
    ),
    # Inline -c / -e: warn on substantial content
    ("trivial python -c", 'python3 -c "print(2+2)"', False, None),
    (
        "multi-line python -c",
        'python3 -c "import sys\nfor x in range(10):\n    print(x)"',
        True,
        "Inline",
    ),
    (
        "long single-line python -c (>120 chars)",
        'python3 -c "this is a fairly long inline script that goes well '
        "over the 120 character threshold we set to catch substantial "
        'inline payloads, like really long"',
        True,
        "Inline",
    ),
    (
        "node -e multi-line",
        'node -e "const x = 1;\nconsole.log(x);\nconsole.log(x+1);"',
        True,
        "Inline",
    ),
    # Bash / sh ARE allowed — shell-in-shell is normal
    ("bash -c short", 'bash -c "echo hello"', False, None),
    (
        "bash -c multi-line still fine",
        'bash -c "echo hello\necho world\necho foo"',
        False,
        None,
    ),
    (
        "bash heredoc still fine",
        "bash <<EOF\nset -euo pipefail\ncd /tmp\nls -la\nEOF",
        False,
        None,
    ),
    # Non-Bash tool: ignored
    ("non-Bash tool ignored", None, False, None),
]


def main() -> int:
    failures: list[str] = []
    for label, command, expect_warning, expected_substring in CASES:
        if label == "non-Bash tool ignored":
            payload = {"tool_name": "Read", "tool_input": {"file_path": "/x"}}
        else:
            payload = {"tool_name": "Bash", "tool_input": {"command": command}}

        output = run_hook(payload)
        context = output.get("hookSpecificOutput", {}).get("additionalContext", "")
        got_warning = bool(context)

        if got_warning != expect_warning:
            failures.append(
                f"  [{label}] expected warning={expect_warning}, "
                f"got {got_warning}\n    output: {output}"
            )
            print(f"FAIL {label}")
            continue

        if expected_substring and expected_substring.lower() not in context.lower():
            failures.append(
                f"  [{label}] expected context to contain {expected_substring!r}\n"
                f"    got: {context}"
            )
            print(f"FAIL {label}")
            continue

        print(f"PASS {label}")

    print()
    if failures:
        print(f"{len(failures)} failure(s):")
        for f in failures:
            print(f)
        return 1
    print(f"All {len(CASES)} cases passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
