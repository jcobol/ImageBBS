# Iteration 42 – Runtime ampersand overrides

## Goals
- [x] Provide Python handlers for the `&,52`, `&,8`, and `&,3` hooks so the prototype runtime can mirror ImageBBS side effects while the real machine-language routines are catalogued.

## Findings

### Built-in override mapping
- `handle_chkflags` mirrors `chkflags` (`&,52`) by toggling the pause/abort indicators through `ConsoleService`, letting the host observe the lightbar state changes that the assembly routine performs when it updates the lightbar bitmap and underline colour.【F:scripts/prototypes/runtime/ampersand_overrides.py†L22-L87】【F:v1.2/source/ml-1_2-y2k.asm†L3210-L3283】
- `handle_dskdir` maps to `dskdir` (`&,8`), preserving the default macro rendering while accepting fallback text supplied by the caller payload so directory prompts behave like the original helper that streams device listings via the kernal channel stack.【F:scripts/prototypes/runtime/ampersand_overrides.py†L89-L108】【F:v1.2/source/ml-1_2-y2k.asm†L2141-L2168】
- The override now requests directory listings from the device context's cached DOS `$` responses, which bootstrap preloads by opening command channels for each registered filesystem drive, letting the host mirror Commodore directory prompts when no fallback text is supplied.【F:scripts/prototypes/device_context.py†L1204-L1244】【F:scripts/prototypes/runtime/ampersand_overrides.py†L92-L121】
- `handle_read0` reproduces `read0` (`&,3`) by staging the active editor buffer into the shared message store before returning the base macro result, matching the overlay's convention of funnelling BASIC buffers into machine-language record writers.【F:scripts/prototypes/runtime/ampersand_overrides.py†L110-L162】【F:v1.2/source/ml-1_2-y2k.asm†L4633-L4651】

### Kernel integration and validation
- `SessionKernel` now seeds `AmpersandRegistry` with the runtime overrides while still merging any TOML-provided entries, ensuring host configuration continues to take precedence when explicit imports are supplied.【F:scripts/prototypes/session_kernel.py†L9-L40】
- The new `tests/test_ampersand_overrides.py` exercises each handler through `AmpersandDispatcher.dispatch`, confirming indicator writes, message-store persistence, and payload-controlled fallback text, giving us executable parity checks for the host implementations.【F:tests/test_ampersand_overrides.py†L1-L88】
