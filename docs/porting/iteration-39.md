# Iteration 39 – Console address helper surface

## Goals
- [x] Extend the console device with address-aware helpers that mirror the overlay's direct screen and colour RAM writes.
- [x] Document how the helpers cover the pause/abort toggles, chat buffer swaps, and sysop pane restores mapped out in iteration 38.

## Implementation
- Added `Console.poke_screen_byte`, `Console.poke_colour_byte`, and `Console.poke_block`, along with matching proxies on `ConsoleService`, so host code can mirror `$0400/$d800` writes without routing through the line-oriented `write()` path.【F:scripts/prototypes/device_context.py†L182-L221】【F:scripts/prototypes/device_context.py†L470-L495】
- The helpers accept raw C64 addresses and iterable payloads, letting callers stream status-line or buffer blocks exactly as the machine-language routines expect while leaving the transcript buffer untouched.【F:scripts/prototypes/device_context.py†L192-L221】

### Routine mapping
| Routine | Screen RAM touch points | Colour RAM touch points | Helper invocation |
| --- | --- | --- | --- |
| `gotoa722` / `skipa739` | `$041e-$0420` indicator cells updated with single `STA` stores.【F:v1.2/source/ml-1_2-y2k.asm†L1504-L1526】 | — | `console_service.poke_screen_byte(0x041e, value)` for pause/abort toggles. |
| `sub_b0c3` | `$0428-$0517` swapped against `$4100-$41ef` using 240-byte indexed stores.【F:v1.2/source/ml-1_2-y2k.asm†L2899-L2916】 | `$d828-$d917` swapped with `tempcol`.【F:v1.2/source/ml-1_2-y2k.asm†L2899-L2916】 | `console_service.poke_block(screen_address=0x0428, screen_bytes=payload, colour_address=0xD828, colour_bytes=colours)` to exchange chat/lightbar regions. |
| `loopb94e` | `$0770-$0797` restored from `tempbott` via descending copy.【F:v1.2/source/ml-1_2-y2k.asm†L4094-L4107】 | `$db70-$db97` restored from `$4050`.【F:v1.2/source/ml-1_2-y2k.asm†L4094-L4107】 | `console_service.poke_block(screen_address=0x0770, screen_bytes=buffer, colour_address=0xDB70, colour_bytes=colours)` to replay the masked sysop pane overlay. |

### Example usage
```python
console_service.poke_screen_byte(0x041f, 0xD0)      # Flash the pause indicator.
console_service.poke_block(
    screen_address=0x0428,
    screen_bytes=saved_chat_bytes,
    colour_address=0xD828,
    colour_bytes=saved_chat_colours,
)
```

