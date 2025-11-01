#!/bin/bash
set -euo pipefail

use_slashes=1
verbose=0

# Why: Perform the Commodore filename translation for validation scenarios.
translate_filename() {
        local stringZ="$1"
        local result="$stringZ"

        if (( verbose )); then
                printf 'Input : %s\n' "$stringZ" >&2
        fi

        result="${result//plus/+}"
        if (( verbose )); then
                printf 'Step 1: %s\n' "$result" >&2
        fi

        if (( use_slashes )); then
                result="${result//slash/\/}"
        else
                result="${result//slash/-}"
        fi
        if (( verbose )); then
                printf 'Step 2: %s\n' "$result" >&2
        fi

        result="${result//_/.}"
        if (( verbose )); then
                printf 'Step 3: %s\n' "$result" >&2
        fi

        printf '%s' "$result"
}

# Why: Fail fast on mismatched expectation to keep automated tests reliable.
assert_equals() {
        local expected="$1"
        local actual="$2"
        local message="$3"
        if [[ "$actual" == "$expected" ]]; then
                printf 'PASS: %s -> %s\n' "$message" "$actual"
        else
                printf 'FAIL: %s (expected %s, got %s)\n' "$message" "$expected" "$actual" >&2
                exit 1
        fi
}

result=$(translate_filename "plusplus 2.prg")
assert_equals "++ 2.prg" "$result" "translate plusplus 2.prg with slashes"

result=$(translate_filename "plusslashMM_load.lbl")
assert_equals "+/MM.load.lbl" "$result" "translate plusslashMM_load.lbl with slashes"

printf 'Setting use_slashes to 0 for final assertion.\n'
use_slashes=0
result=$(translate_filename "slashslashslash_")
assert_equals "---." "$result" "translate slashslashslash_ without slashes"

printf 'Checking verbose debug output emission.\n'
use_slashes=1
verbose=0
debug_output=$( { translate_filename "plusslashfile_" 1>/dev/null; } 2>&1 )
assert_equals "" "$debug_output" "no verbose output by default"
verbose=1
verbose_output=$( { translate_filename "plusslashfile_" 1>/dev/null; } 2>&1 )
assert_equals $'Input : plusslashfile_\nStep 1: +slashfile_\nStep 2: +/file_\nStep 3: +/file.' "$verbose_output" "verbose output emitted"

result=$(translate_filename "plusslashfile_" 2>/dev/null)
assert_equals "+/file." "$result" "translate plusslashfile_ while verbose"

printf 'All translate tests passed.\n'
