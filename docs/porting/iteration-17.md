# Iteration 17 – Surfacing caller statistics from the setup stub

## Goals
- Clarify how the Stage 4 `setup` placeholder mirrors the caller metadata
  described in the sysop manual so future ports can keep the persisted
  statistics in sync with the recovered BASIC program.【F:v1.2/core/setup.stub.txt†L46-L55】【F:v1.2/docs/image-1_2b-sysop-manual.adoc†L6898-L7004】
- Expose a structured view of those statistics to Python prototypes so host
  tooling can inspect the same counters, last-caller fields, and password-sub
  password that the BASIC program would preload from `e.data`/`e.stats` without
  reparsing the listing.【F:scripts/prototypes/setup_defaults.py†L98-L168】

## `setup` Stub Updates
- Documented how the Stage 4 `DATA` record feeds the BAR counters, last caller,
  total call count, and password-sub credential outlined in the manual so the
  placeholder reflects the sequencing and intent of the original program.【F:v1.2/core/setup.stub.txt†L46-L55】【F:v1.2/docs/image-1_2b-sysop-manual.adoc†L6898-L7004】

## Host Defaults Helper
- Added a `BoardStatistics` dataclass that captures the stubbed BAR counters,
  total call tally, last-caller metadata, and password-sub password while
  providing a convenience flag for detecting recorded activity.【F:scripts/prototypes/setup_defaults.py†L98-L132】
- Updated `SetupDefaults` to return a `BoardStatistics` instance, preserving the
  original convenience accessors for the last caller, statistics banner, and
  last-logon timestamp alongside a new accessor for the password-sub
  credential.【F:scripts/prototypes/setup_defaults.py†L134-L188】
- Re-exported `BoardStatistics` from the prototypes package so downstream tools
  can import the enriched statistics snapshot from the shared namespace.【F:scripts/prototypes/__init__.py†L20-L45】

## Follow-ups
- Once authentic `e.data` and `e.stats` dumps are available, confirm the exact
  semantics of the first four BAR counters and populate the statistics banner so
  both the BASIC stub and Python helper reflect the live system defaults.
