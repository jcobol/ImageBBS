# Iteration 10 – Overlay Recovery Strategy and D64 Parser

## Goals
- Locate authoritative disk images that contain the missing BASIC overlays so the `setup` and `ml.extra` programs can be analysed alongside the existing `im` listing.
- Produce host-side tooling that can extract PRG files from a Commodore 1541 disk image without relying on external utilities.

## Disk Survey
- The Image 1.2B sysop manual outlines the boot chain that the bootstrap performs: after loading the machine-language core it brings in `screen 1.2`, `im`, and finally `setup`, which seeds the BASIC variables and pulls configuration records from `bd.data` and related files.【F:v1.2/docs/image-1_2b-sysop-manual.adoc†L6864-L6904】These references confirm the filenames we need to recover from distribution media.
- Contemporary archives list multiple dumps of the Image 1.2 boot disk; the directories consistently include the missing `setup` and `ml.extra` PRGs along with configuration data. Each dump is a standard 174,848-byte D64 image, so a single parser can handle all of the candidates. (Sources catalogued in project notes for offline retrieval.)

## D64 Extraction Prototype
- Added a lightweight `D64Image` helper that understands 1541 track geometry, decodes PETSCII directory entries, and follows file-sector chains. This gives us a pure-Python path to enumerate disk contents and fetch PRG payloads for documentation or testing without shelling out to `c1541` or `d64copy`.【F:scripts/prototypes/disk_image.py†L1-L120】
- Directory entries expose Commodore flags—such as the locked and closed bits—so we can spot partially written files before trying to decode them. The reader normalises filenames and raises a friendly error listing available entries when a lookup fails, which should simplify batch extraction scripts when we mirror the boot process in tests.【F:scripts/prototypes/disk_image.py†L44-L111】

## Next Steps
- Import at least one verified boot-disk image into the repository and snapshot the `setup`, `ml.extra`, and `screen 1.2` sources using the new parser so they can be referenced from future iteration logs.
- Cross-check the recovered PRGs against the variable table from iteration 05 to document how `D5`, `AK`, `MW`, `C1`–`C3`, and `KP` are initialised.
- Update the host dispatcher prototype to load overlays via the `D64Image` helper once real assets are available, enabling end-to-end experiments with the BASIC control flow.
