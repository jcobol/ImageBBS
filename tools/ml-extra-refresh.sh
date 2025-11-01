#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"
BASELINE_PATH="${REPO_ROOT}/docs/porting/artifacts/ml-extra-overlay-metadata.json"

cmd=("ml-extra-refresh")

have_baseline=0
have_metadata=0
have_if_changed=0
for arg in "$@"; do
  if [[ "${arg}" == "--baseline" ]]; then
    have_baseline=1
  elif [[ "${arg}" == "--metadata-json" ]]; then
    have_metadata=1
  elif [[ "${arg}" == "--if-changed" ]]; then
    have_if_changed=1
  fi
done

if [[ ${have_baseline} -eq 0 ]]; then
  cmd+=("--baseline" "${BASELINE_PATH}")
fi
if [[ ${have_metadata} -eq 0 ]]; then
  cmd+=("--metadata-json" "${BASELINE_PATH}")
fi
if [[ ${have_if_changed} -eq 0 ]]; then
  cmd+=("--if-changed")
fi

cmd+=("$@")

exec "${cmd[@]}"
