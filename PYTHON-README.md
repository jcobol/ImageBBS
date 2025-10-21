# Python Tooling Overview

## Runtime Session CLI

The runtime session CLI lives at `scripts/prototypes/runtime/cli.py`. It can be
invoked directly to exercise the prototype runtime stack that wires the
`SessionRunner`, default configuration, and the main menu module.

### Usage

```bash
python -m imagebbs.runtime.cli [OPTIONS]
```

### Options

- `--drive-config <path>`: Optional TOML file defining drive slot assignments
  via `load_drive_config`. If provided, the CLI merges the file into the default
  drive configuration exposed by `SetupDefaults.stub()`.
- `--message-store-load <path>`: Optional file path to load message store state
  before the session begins.
- `--message-store-save <path>`: Optional file path used to persist message
  store state when the session exits.

### Example Drive Configuration

The repository ships `docs/examples/runtime-drives.toml` as a starting template
for the `--drive-config` option. Update the `[slots]` paths to match local
directories that mirror the ImageBBS drive layout and remove or adjust the
`[ampersand_overrides]` table if you do not need custom ampersand handlers.

### Interactive Loop

The CLI runs a synchronous loop that streams console output to stdout, accepts
keyboard input line-by-line, and forwards it to the session runner. The loop
terminates once the session reaches `SessionState.EXIT`, making it possible to
script command sequences—for example, piping `EX` to exit immediately.

### Testing

Automated coverage for the CLI lives in `tests/test_runtime_cli.py`. The tests
validate configuration overrides, optional message store persistence hints, and
an `EX` exit sequence using in-memory `io.StringIO` streams.
