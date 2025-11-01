#!/bin/bash
set -euo pipefail

quiet=0
use_slashes=1
verbose=0

# Why: Provide user guidance when invocation parameters are invalid.
print_usage() {
        cat <<'USAGE'
Usage: github-rename.sh [options] <path> [<path> ...]

Options:
  -s, --no-slash    Replace occurrences of "slash" with "-" instead of "/".
  -q, --quiet       Suppress non-essential informational output.
  -v, --verbose     Emit debug details while translating filenames.
  -h, --help        Show this help message and exit.

Each <path> may be a file or directory. Directories are searched for *.lbl files.
USAGE
}

# Why: Emit optional informational messages without breaking quiet mode semantics.
log_info() {
        local message="$1"
        if (( quiet == 0 )); then
                printf '%s\n' "$message"
        fi
}

# Why: Perform the Commodore filename translation used across rename workflows.
translate_filename() {
        local input="$1"
        local basename_only
        basename_only=$(basename -- "$input")
        local result="$basename_only"

        if (( verbose )); then
                printf 'Input : %s\n' "$basename_only" >&2
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

# Why: Translate a single .lbl file name and print the rename action when needed.
process_lbl_file() {
        local full_path="$1"
        local dir name_without_ext translated translated_with_ext

        dir=$(dirname -- "$full_path")
        name_without_ext="$(basename -- "$full_path" .lbl)"
        translated="$(translate_filename "$name_without_ext")"
        translated_with_ext="$translated.lbl"

        if [[ "$translated_with_ext" == "$(basename -- "$full_path")" ]]; then
                log_info "$full_path: No transformation required"
        else
                log_info "git mv '$full_path' '$dir/$translated_with_ext'"
        fi
}

# Why: Dispatch processing for files or directories passed on the command line.
process_path() {
        local target="$1"
        if [[ -d "$target" ]]; then
                while IFS= read -r file; do
                        process_lbl_file "$file"
                done < <(find "$target" -type f -name '*.lbl' -print | sort)
        else
                if [[ "$target" == *.lbl && -f "$target" ]]; then
                        process_lbl_file "$target"
                else
                        log_info "Skipping unsupported path: $target"
                fi
        fi
}

# Parse options.
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

if (( $# == 0 )); then
        print_usage >&2
        exit 1
fi

for path in "$@"; do
        process_path "$path"
done
