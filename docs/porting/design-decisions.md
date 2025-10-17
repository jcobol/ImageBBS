# Design Decisions

## Preservation of experience
- Maintain the original look and feel for both callers and the system operator when interacting with the port.
- Ensure the system remains moddable in the same spirit as the original Image BBS, including support for customization hooks.
- Preserve parity for key subsystems in the initial release, with the sysop console, message boards, and file transfers treated as must-have experiences.
- Match the original colour palette so interface elements appear identical to the Commodore 64 release.

## Storage configuration
- Support configuring drive numbers that map to paths on the host filesystem via a configuration file.
- When persisting data to files, keep the original filenames; confirm any required storage-format deviations with the project maintainer before landing changes.

## Character set fidelity
- Render Commodore 64 character glyphs so that existing artwork and PETSCII layouts display identically to the original system.
- Maintain PETSCII behaviour and rendering as close to original fidelity as possible.

## Runtime strategy
- We will not be running the ported system under an emulator.
- Runtime execution speed does not need artificial throttling; the host can run at native pace.
- BAUD rate must remain configurable and should cap network throughput to simulate the original communication limits.
