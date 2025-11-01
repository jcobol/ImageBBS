#!/bin/bash
set -euo pipefail

quiet=0
use_slashes=1
verbose=0

# Why: Provide user guidance when invocation parameters are invalid.
print_usage() {
        cat <<'USAGE'
Usage: test-translate.sh [options] <input_lbl> <disk_image>

Options:
  -s, --no-slash    Replace occurrences of "slash" with "-" instead of "/".
  -q, --quiet       Suppress non-essential informational output.
  -v, --verbose     Emit debug details while translating filenames.
  -h, --help        Show this help message and exit.
USAGE
}

# Why: Emit optional informational messages without breaking quiet mode semantics.
log_info() {
        local message="$1"
        if (( quiet == 0 )); then
                printf '%s\n' "$message"
        fi
}

# Why: Perform the Commodore filename translation used across tooling.
translate_filename() {
        local input="$1"
        local result="$input"

        if (( verbose )); then
                printf 'Input : %s\n' "$input" >&2
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

while getopts ':sqvh-:' opt; do
        case "$opt" in
        s)
                use_slashes=0
                ;;
        q)
                quiet=1
                ;;
        v)
                verbose=1
                ;;
        h)
                print_usage
                exit 0
                ;;
        -)
                case "$OPTARG" in
                no-slash)
                        use_slashes=0
                        ;;
                quiet)
                        quiet=1
                        ;;
                verbose)
                        verbose=1
                        ;;
                help)
                        print_usage
                        exit 0
                        ;;
                *)
                        print_usage >&2
                        exit 1
                        ;;
                esac
                ;;
        :)
                print_usage >&2
                exit 1
                ;;
        *)
                print_usage >&2
                exit 1
                ;;
        esac
done
shift $((OPTIND - 1))

if (( $# != 2 )); then
        print_usage >&2
        exit 1
fi

input_lbl="$1"
disk_image="$2"
input_prg="${input_lbl//.lbl/.prg}"
translated_lbl="$(translate_filename "$input_lbl")"
C64_FILE="${translated_lbl//.lbl/}"

if (( quiet == 0 )); then
        log_info "input_lbl=$input_lbl"
        log_info "translated_lbl=$translated_lbl"
        log_info "C64_FILE=$C64_FILE"
        log_info "wine c64list3_05.exe \"$input_lbl\" -prg -ovr"
        log_info "c1541 \"$disk_image\""
        log_info "    -del \"$C64_FILE\""
        log_info "    -write \"$input_prg\" \"$C64_FILE\""
fi

wine c64list3_05.exe "$input_lbl" -prg -ovr
c1541 "$disk_image" \
        -del "$C64_FILE" \
        -write "$input_prg" "$C64_FILE"
