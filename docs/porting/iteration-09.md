# Iteration 09 – Prototype Host Dispatcher and Editor State Machine

## Goals
- Exercise a thin device-context prototype that mirrors the `SETLFS`/`PRINT#`
  workflow used during overlay loads so the planned DOS command helper has
  concrete behaviours to validate.
- Validate a state-machine sketch for the message editor overlay using the
  dispatcher patterns noted in the BASIC sources.

## Device-Context Prototype
- The prototype registers disk, console, and modem devices under the same
  logical numbering scheme ImageBBS uses when opening files and command
  channels.【F:scripts/prototypes/device_context.py†L88-L110】
- The `DiskDrive` adapter preloads the command channel with a canned status
  line and responds to the `I`, `$`, and `S` verbs, letting us simulate
  directory reads and scratch operations without the Commodore DOS ROM.【F:scripts/prototypes/device_context.py†L54-L81】
- `DeviceContext.issue_command` mirrors the BASIC pattern of sending a raw
  string to the command channel and caching the response for later GOSUBs that
  expect to reuse the status text.【F:scripts/prototypes/device_context.py†L115-L141】
- A simple directory cache hangs off the context so future overlay loaders can
  reuse listings without reissuing `$` commands, matching the memoised device
  switching observed around `GOSUB1009` in the BASIC dispatcher.【F:scripts/prototypes/device_context.py†L143-L151】【F:v1.2/core/im.txt†L90-L118】

## Message-Editor State Machine
- `MessageEditor` models each high-level BASIC menu as an explicit state and
  routes events through handlers that emit the same prompts the original UI
  prints through `PRINT#` or modem writes.【F:scripts/prototypes/message_editor.py†L11-L99】【F:v1.2/core/im.txt†L120-L183】
- The context object caches modem output and draft metadata so host-side tests
  can assert on the side effects that the BASIC globals (`AN$`, `KD$`, etc.)
  previously carried.【F:scripts/prototypes/message_editor.py†L27-L99】【F:v1.2/core/im.txt†L120-L183】
- Error paths raise `TransitionError` when an event arrives out of sequence,
  mirroring how the BASIC code relied on `ON...GOTO` tables that only accepted
  a subset of inputs for each menu.【F:scripts/prototypes/message_editor.py†L69-L99】【F:v1.2/core/im.txt†L90-L118】

## Follow-Ups
- Flesh out the DOS command helper by scripting scenarios that combine the
  device dispatcher with real overlay assets once the missing PRGs are
  recovered.
- Expand the state machine with concrete transitions from the `ml.extra`
  overlays when their ampersand handlers are documented.
- Draft unit tests that drive the prototypes with captured BASIC transcripts so
  the eventual host implementation can share fixtures with the documentation.
