#!/bin/bash
set -euo pipefail

# Usage: start-bbs.sh [--vice-bin PATH] [--baud RATE] [--rsdev TARGET] [BASEDIR [BOOT_IMAGE [SUPPORT_IMAGE]]]
#
# Examples:
#   start-bbs.sh
#   start-bbs.sh --vice-bin /usr/bin/x64sc --baud 9600
#   start-bbs.sh "~/c64/Image BBS/v2" "custom boot.d81" "custom support.d81"

# Why: Provide quick-reference documentation so operators can discover new runtime flags without consulting external docs.
print_usage() {
  cat <<'EOF'
Usage: start-bbs.sh [--vice-bin PATH] [--baud RATE] [--rsdev TARGET] [BASEDIR [BOOT_IMAGE [SUPPORT_IMAGE]]]

Options:
  --vice-bin PATH   Path to the VICE x64 binary to invoke (default: x64)
  --baud RATE       Baud rate configured for the RS232 user port (default: 2400)
  --rsdev TARGET    tcpser connection target passed to -rsdev1 (default: 0)

Positional arguments retain their previous meaning and may be combined with the new flags.
EOF
}

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

vice_bin="x64"
baud="2400"
rsdev="0"

declare -a positional_args=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --vice-bin)
      if [[ $# -lt 2 ]]; then
        echo "Error: --vice-bin requires a value" >&2
        print_usage
        exit 1
      fi
      vice_bin="$2"
      shift 2
      ;;
    --vice-bin=*)
      vice_bin="${1#*=}"
      shift
      ;;
    --baud)
      if [[ $# -lt 2 ]]; then
        echo "Error: --baud requires a value" >&2
        print_usage
        exit 1
      fi
      baud="$2"
      shift 2
      ;;
    --baud=*)
      baud="${1#*=}"
      shift
      ;;
    --rsdev)
      if [[ $# -lt 2 ]]; then
        echo "Error: --rsdev requires a value" >&2
        print_usage
        exit 1
      fi
      rsdev="$2"
      shift 2
      ;;
    --rsdev=*)
      rsdev="${1#*=}"
      shift
      ;;
    --help)
      print_usage
      exit 0
      ;;
    --)
      shift
      while [[ $# -gt 0 ]]; do
        positional_args+=("$1")
        shift
      done
      ;;
    -*)
      echo "Error: Unknown option: $1" >&2
      print_usage
      exit 1
      ;;
    *)
      positional_args+=("$1")
      shift
      ;;
  esac
done

set -- "${positional_args[@]:+${positional_args[@]}}"

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

# -rsuserdev1 \|nc\ -p\ 3064\ 127.0.0.1\ 25232

# Why: Build the VICE command as an array so user-provided paths and overrides are preserved without additional quoting gymnastics.
vice_cmd=("$vice_bin" "-verbose" "+acia" "-rsdev1" "$rsdev" "-rsuser" "-rsdev1baud" "$baud" "-drive10type" "1581" "-10" "$boot_image" "-drive11type" "1581" "-11" "$support_image")

"${vice_cmd[@]}"
