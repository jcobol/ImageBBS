# Shell Test Suite

This directory contains shell-based tests that exercise the conversion and linting scripts.

## Available tests

- `tests/test-translate.sh` verifies the filename translation helpers behave consistently.
- `tests/test-c64list-linter.sh` ensures `scripts/c64list-linter.sh` rewrites PETSCII placeholders and normalizes BASIC keywords without altering quoted strings.

## Running the tests

Run all shell tests with:

```bash
./tests/run-all.sh
```

Each test script is also executable on its own if you prefer to focus on a specific scenario.
