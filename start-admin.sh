#!/usr/bin/env bash
# start-admin.sh: Convenience launcher for the ImageBBS admin console.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_DRIVE_CONFIG="${ROOT_DIR}/docs/examples/runtime-drives.toml"
DEFAULT_MESSAGES_PATH="${ROOT_DIR}/var/runtime/messages.json"

# resolve_path normalises relative paths so the admin launcher works from anywhere.
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

DRIVE_CONFIG="${IMAGEBBS_DRIVE_CONFIG:-$DEFAULT_DRIVE_CONFIG}"
MESSAGES_PATH="${IMAGEBBS_MESSAGES_PATH:-$DEFAULT_MESSAGES_PATH}"

if [[ -n "${DRIVE_CONFIG}" ]]; then
    DRIVE_CONFIG="$(resolve_path "${DRIVE_CONFIG}")"
fi
if [[ -n "${MESSAGES_PATH}" ]]; then
    MESSAGES_PATH="$(resolve_path "${MESSAGES_PATH}")"
fi

if [[ -n "${MESSAGES_PATH}" ]]; then
    mkdir -p "$(dirname "${MESSAGES_PATH}")"
fi

CLI_ARGS=("$@")

if [[ -n "${DRIVE_CONFIG}" ]]; then
    if [[ "${DRIVE_CONFIG}" != "${DEFAULT_DRIVE_CONFIG}" && ! -f "${DRIVE_CONFIG}" ]]; then
        echo "error: IMAGEBBS_DRIVE_CONFIG points to a missing file: ${DRIVE_CONFIG}" >&2
        exit 1
    fi
    if [[ -f "${DRIVE_CONFIG}" ]]; then
        CLI_ARGS=("--drive-config" "${DRIVE_CONFIG}" "${CLI_ARGS[@]}")
    fi
fi

if [[ -n "${MESSAGES_PATH}" ]]; then
    CLI_ARGS=("--messages-path" "${MESSAGES_PATH}" "${CLI_ARGS[@]}")
fi

exec python -m imagebbs.runtime.cli "${CLI_ARGS[@]}"
