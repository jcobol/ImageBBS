#!/usr/bin/env bash
# start-admin.sh: Convenience launcher for the ImageBBS admin console.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_DRIVE_CONFIG="${ROOT_DIR}/docs/examples/runtime-drives.toml"
DEFAULT_MESSAGES_PATH="${ROOT_DIR}/var/runtime/messages.json"

# resolve_path exists so the admin launcher can accept relative inputs regardless of the caller's working directory.
resolve_path() {
    local input_path="${1:-}"
    if [[ -z "${input_path}" ]]; then
        return 0
    fi
    if [[ "${input_path}" == /* ]]; then
        printf '%s\n' "${input_path}"
    else
        printf '%s\n' "${ROOT_DIR}/${input_path}"
    fi
}

# print_usage exists so unexpected command line arguments produce actionable feedback instead of silent failure.
print_usage() {
    cat <<'EOF'
Usage: start-admin.sh [--drive-config PATH] [--messages-path PATH]
                       [--help]

Launch the ImageBBS admin console with the configured drive and message paths.

Options:
  --drive-config PATH   Override the drive configuration file.
  --messages-path PATH  Override the message store path.
  -h, --help            Show this help message and exit.

start-admin.sh does not forward additional command line arguments to the admin console.
EOF
}

DRIVE_CONFIG="$DEFAULT_DRIVE_CONFIG"
MESSAGES_PATH="$DEFAULT_MESSAGES_PATH"

while (($# > 0)); do
    case "$1" in
        -h|--help)
            print_usage
            exit 0
            ;;
        --drive-config)
            if (($# < 2)); then
                echo "error: --drive-config requires a value" >&2
                print_usage >&2
                exit 1
            fi
            DRIVE_CONFIG="$2"
            shift 2
            ;;
        --messages-path)
            if (($# < 2)); then
                echo "error: --messages-path requires a value" >&2
                print_usage >&2
                exit 1
            fi
            MESSAGES_PATH="$2"
            shift 2
            ;;
        *)
            echo "error: unexpected argument: $1" >&2
            print_usage >&2
            exit 1
            ;;
    esac
done

if [[ -n "${DRIVE_CONFIG}" ]]; then
    DRIVE_CONFIG="$(resolve_path "${DRIVE_CONFIG}")"
fi
if [[ -n "${MESSAGES_PATH}" ]]; then
    MESSAGES_PATH="$(resolve_path "${MESSAGES_PATH}")"
fi

if [[ -n "${MESSAGES_PATH}" ]]; then
    mkdir -p "$(dirname "${MESSAGES_PATH}")"
fi

CLI_ARGS=()

if [[ -n "${DRIVE_CONFIG}" ]]; then
    if [[ "${DRIVE_CONFIG}" != "${DEFAULT_DRIVE_CONFIG}" && ! -f "${DRIVE_CONFIG}" ]]; then
        echo "error: --drive-config path does not exist: ${DRIVE_CONFIG}" >&2
        exit 1
    fi
    if [[ -f "${DRIVE_CONFIG}" ]]; then
        CLI_ARGS+=("--drive-config" "${DRIVE_CONFIG}")
    fi
fi

if [[ -n "${MESSAGES_PATH}" ]]; then
    CLI_ARGS+=("--messages-path" "${MESSAGES_PATH}")
fi

exec python -m imagebbs.runtime.cli "${CLI_ARGS[@]}"
