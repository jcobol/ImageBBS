#!/bin/bash
set -euo pipefail

# Why: Expand user-provided paths so overrides can use shell-style tilde notation.
expand_path() {
  local path="$1"
  case "$path" in
    "~")
      printf '%s\n' "$HOME"
      ;;
    "~/"*)
      printf '%s\n' "${HOME}${path:1}"
      ;;
    *)
      printf '%s\n' "$path"
      ;;
  esac
}

# Why: Convert verified file system entries into absolute paths so the VICE invocation never receives relative references.
absolute_path() {
  local path="$1"
  if command -v realpath >/dev/null 2>&1; then
    realpath "$path"
  else
    if [[ -d "$path" ]]; then
      (cd "$path" && pwd)
    else
      local dir
      dir=$(cd "$(dirname "$path")" && pwd)
      printf '%s/%s\n' "$dir" "$(basename "$path")"
    fi
  fi
}

default_basedir="${HOME}/c64/Image BBS/v2"

if [[ $# -ge 1 ]]; then
  raw_basedir="$1"
elif [[ -n "${BBS_BASEDIR:-}" ]]; then
  raw_basedir="$BBS_BASEDIR"
else
  raw_basedir="$default_basedir"
fi

raw_basedir=$(expand_path "$raw_basedir")

if [[ ! -d "$raw_basedir" ]]; then
  echo "Error: Base directory not found: $raw_basedir" >&2
  exit 1
fi

basedir=$(absolute_path "$raw_basedir")

default_boot_image="${basedir}/image 2_0 boot-e.d81"
default_support_image="${basedir}/image 2_0 s-nm.d81"

if [[ $# -ge 2 ]]; then
  raw_boot_image="$2"
elif [[ -n "${BBS_BOOT_IMAGE:-}" ]]; then
  raw_boot_image="$BBS_BOOT_IMAGE"
else
  raw_boot_image="$default_boot_image"
fi

if [[ $# -ge 3 ]]; then
  raw_support_image="$3"
elif [[ -n "${BBS_SUPPORT_IMAGE:-}" ]]; then
  raw_support_image="$BBS_SUPPORT_IMAGE"
else
  raw_support_image="$default_support_image"
fi

boot_image=$(expand_path "$raw_boot_image")
support_image=$(expand_path "$raw_support_image")

if [[ "$boot_image" != /* ]]; then
  boot_image="${basedir%/}/$boot_image"
fi

if [[ "$support_image" != /* ]]; then
  support_image="${basedir%/}/$support_image"
fi

if [[ ! -f "$boot_image" ]]; then
  echo "Error: Boot disk image not found: $boot_image" >&2
  exit 1
fi

if [[ ! -f "$support_image" ]]; then
  echo "Error: Support disk image not found: $support_image" >&2
  exit 1
fi

boot_image=$(absolute_path "$boot_image")
support_image=$(absolute_path "$support_image")

# tcpser is in ~/bin

# test Image 1.3 in VICE 3.1 at 2400 bps on user port
# +acia         disable ACIA emulation
# -rsdev1       define device, address:port for tcpser to connect to
# -rsuser       enable user port RS232 emulation
# -drive10type  1581
# -10           attach disk image

x64 -verbose \
+acia \
-rsdev1 0 \
# -rsuserdev1 \|nc\ -p\ 3064\ 127.0.0.1\ 25232
-rsuser \
-rsdev1baud 2400 \
-drive10type 1581 -10 "$boot_image" \
-drive11type 1581 -11 "$support_image"
