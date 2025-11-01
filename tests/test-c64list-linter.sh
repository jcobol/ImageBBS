#!/bin/bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

input_file="$tmp_dir/original.lbl"
cat <<'INPUT' > "$input_file"
10 PRINT "{alpha:upper}{$c1}{$c2}{$a0}{$c3}"
20 IF X=10 THEN GOTO 100
30 GOSUB 200 : STOP
40 PRINT "KEEP IF THEN GOTO STOP"
INPUT

expected_file="$tmp_dir/expected.lbl"
cat <<'EXPECTED' > "$expected_file"
10 print "{alpha:alt}AB C"
20 if X=10 then goto 100
30 gosub 200 : stop
40 print "KEEP IF THEN GOTO STOP"
EXPECTED

"$repo_root/scripts/c64list-linter.sh" "$input_file"

diff_output="$tmp_dir/diff.txt"
if diff -u "$expected_file" "$input_file" > "$diff_output"; then
  echo "PASS: c64list linter rewrites PETSCII placeholders and keywords."
else
  cat "$diff_output"
  echo "FAIL: c64list linter output did not match expected normalization." >&2
  exit 1
fi
