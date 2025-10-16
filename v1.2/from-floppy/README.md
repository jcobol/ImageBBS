# Recovered ImageBBS 1.2B Overlays

This directory mirrors raw PRG images pulled from an original ImageBBS 1.2B
floppy alongside PETCAT listings for quick inspection.

## Available assets

| PRG      | Load address | Bytes | Notes |
|----------|--------------|-------|-------|
| `setup`  | `$1c01`       | 6,749 | BASIC overlay that dimensions runtime variables, reads configuration records, and launches the main dispatcher. |
| `ml.extra` | `$1000`    | 6,877 | Machine-language extension that populates ampersand verbs, lightbar flags, and macro/colour tables. |

The load addresses derive from the PRG headers and confirm the overlays align
with the expectations documented in the BASIC and machine-language stubs under
`v1.2/core/setup.stub.txt` and `v1.2/source/ml_extra_stub.asm`.

## Text listings

The `.txt` companions were generated with VICE PETCAT to make the tokenised
BASIC/machine-language streams visible in the repository:

```
/Applications/vice-arm64-gtk3-3.9/bin/petcat -text -o FILENAME.txt -- FILENAME
```

Re-running the command against the PRG assets will refresh the listings if new
disks or cleanups are sourced in the future. When VICE tooling is not available,
`scripts/decode_basic_prg.py` provides an equivalent pure-Python pipeline:

```
python scripts/decode_basic_prg.py v1.2/from-floppy/setup -o v1.2/source/setup.bas
```

The helper walks the token stream, expands keywords, and preserves PETSCII
control bytes as `{${hex}}` escapes so round-tripping through the repository
remains lossless.
