#!/bin/bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

test_scripts=(
  "tests/test-translate.sh"
  "tests/test-c64list-linter.sh"
)

for test_script in "${test_scripts[@]}"; do
  echo "Running ${test_script}..."
  bash "$repo_root/$test_script"
  echo

done

echo "All shell-based tests passed."
