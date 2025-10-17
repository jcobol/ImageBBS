# Design Decisions

## Preservation of experience
- Maintain the original look and feel for both callers and the system operator when interacting with the port.
- Ensure the system remains moddable in the same spirit as the original Image BBS, including support for customization hooks.
- Preserve parity for key subsystems in the initial release, with the sysop console, message boards, and file transfers treated as must-have experiences.
- Match the original colour palette so interface elements appear identical to the Commodore 64 release.

## Storage configuration
- Support configuring drive numbers that map to paths on the host filesystem via a configuration file.
- When persisting data to files, keep the original filenames; confirm any required storage-format deviations with the project maintainer before landing changes.

### Host drive mapping schema (draft)
- Configuration should live alongside the port runtime so deployments can review and adjust drive mappings without touching code.
- Use a TOML document with a dedicated `[storage]` table.
- Represent each Commodore device drive using an array of tables under `[[storage.drives]]` so we can record the drive number, host directory, and access policy.
- Preserve filenames exactly as supplied by ImageBBS. Validation may reject names that introduce path separators or illegal host characters, but the runtime must not silently rename files.

Example configuration:

```toml
[storage]
default_drive = 8

[[storage.drives]]
drive = 8
path = "~/imagebbs/data/system"

[[storage.drives]]
drive = 9
path = "~/imagebbs/data/uploads"
read_only = false

[[storage.drives]]
drive = 10
path = "~/imagebbs/data/mail"
read_only = true
```

Runtime expectations:
- `default_drive` must reference one of the configured entries and becomes the implicit target for operations that omit a drive number.
- Drive roots are resolved relative to the configuration file location when they are not absolute paths.
- Host directories must exist (or be creatable by deployment tooling) before invoking load/save operations.
- Read-only drives should reject save requests but remain available for loading assets.
- All Commodore filenames, including PETSCII casing and punctuation, must be preserved verbatim when reading or writing host files.

## Character set fidelity
- Render Commodore 64 character glyphs so that existing artwork and PETSCII layouts display identically to the original system.
- Maintain PETSCII behaviour and rendering as close to original fidelity as possible.

## Runtime strategy
- We will not be running the ported system under an emulator.
- Runtime execution speed does not need artificial throttling; the host can run at native pace.
- BAUD rate must remain configurable and should cap network throughput to simulate the original communication limits.
