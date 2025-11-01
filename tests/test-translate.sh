#!/bin/bash
set -euo pipefail

# Expectations:
# - "plusplus 2.prg" becomes "++ 2.prg" when slash translation is enabled.
# - "plusslashMM_load.lbl" becomes "+/MM.load.lbl" when slash translation is enabled.
# - "slashslashslash_" becomes "---." when slash translation is disabled.

use_slashes=1

# Why: Provide consistent translation logic reused by tests to validate scenario outputs.
translate_filename() {
        local stringZ="$1"
        local result="${stringZ//plus/+}"
        if [[ "$use_slashes" == "1" ]]; then
                result="${result//slash/\/}"
        else
                result="${result//slash/-}"
        fi
        result="${result//_/.}"
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

printf 'All translate tests passed.\n'
