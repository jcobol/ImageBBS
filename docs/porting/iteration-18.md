# Iteration 18 – Mirroring chat mode prompts from the setup stub

## Goals
- Capture the chat mode banners that the manual attributes to `setup` so the
  placeholder advertises the same text the original program staged during
  boot.【F:v1.2/docs/image-1_2b-sysop-manual.adoc†L2399-L2444】
- Expose those banners through the Python defaults helper so host prototypes can
  reuse the same prompts when emulating sysop chat flows without reparsing the
  BASIC listing.【F:scripts/prototypes/setup_defaults.py†L105-L188】

## `setup` Stub Updates
- The Stage 3 comment now calls out that the chat mode strings follow the
  manual's "Entering/Exiting/Returning" prompts and the placeholder initializes
  each string with the colorised banner text observed in the documentation, so
  recovered overlays can rely on deterministic defaults.【F:v1.2/core/setup.stub.txt†L261-L282】【F:v1.2/docs/image-1_2b-sysop-manual.adoc†L2399-L2444】

## Host Defaults Helper
- Added a `ChatModeMessages` dataclass plus convenience properties on
  `SetupDefaults` so Python tooling can read the same entering, exiting, and
  return-to-editor banners that the BASIC stub stages during startup, keeping the
  host-side view aligned with the documented boot process.【F:scripts/prototypes/setup_defaults.py†L105-L188】【F:scripts/prototypes/__init__.py†L17-L63】

## Follow-ups
- Once an authentic `setup` overlay or runtime trace is recovered, confirm
  whether additional chat prompts (e.g., paging reasons or siren indicators) are
  staged alongside these banners so the helper can surface them as well.
