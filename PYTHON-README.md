# Python Tooling Overview

## Runtime Session CLI

The runtime session CLI is now published as part of the `imagebbs` package.
Installing the project exposes a console script so the session runner can be
started without invoking the module by path.

### Installation

From the repository root, install the package into a virtual environment:

```bash
pip install .
```

For development work the editable mode keeps the installation pointed at your
working tree:

```bash
pip install -e .
```

The package declares an optional `runtime` extra that adds the `windows-curses`
wheel when installing on Windows:

```bash
pip install .[runtime]
```

### Usage

After installation, launch the runtime session from anywhere with:

```bash
imagebbs-runtime [OPTIONS]
```

The entry point invokes `imagebbs.runtime.cli:main`, mirroring the behaviour of
`python -m imagebbs.runtime.cli` while removing the need to reference the
module path explicitly.

### Options

- `--drive-config <path>`: Optional TOML file defining drive slot assignments
  via `load_drive_config`. If provided, the CLI merges the file into the default
  drive configuration exposed by `SetupDefaults.stub()`.
- `--messages-path <path>`: Optional path used to load and persist message store
  state for the session.
- `--listen <host:port>`: Accept inbound TCP connections and bridge them into
  the session runner using the Telnet transport.
- `--connect <host:port>`: Dial a remote TCP endpoint and bridge the resulting
  connection into the session runner.
- `--curses-ui` / `--console-ui`: Toggle between the curses sysop console and a
  plain stdout stream renderer. The curses UI is enabled by default.
- `--baud-limit <bps>`: Override the modem baud limit used when bridging
  sessions over TCP.

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
