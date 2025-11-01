#!/bin/bash
# C64List .lbl linter -- fix some issues with .prg -> .lbl conversion
# Keyword normalization ensures BASIC keywords remain lowercase while
# preserving the original casing inside quoted strings for readability.

# 2019/02/22: C64List 3.50 handles uppercase characters in listings now;
# removed e.g. "A" -> "{A}" abstraction, is now just "A" in output file

# https://unix.stackexchange.com/questions/95939/how-exactly-do-i-create-a-sed-script-and-use-it-to-edit-a-file

output_file="$1"

if [[ -z "$output_file" ]]; then
  echo "Usage: $0 <output_file>" >&2
  exit 1
fi

if [[ ! -f "$output_file" ]]; then
  echo "Error: output file '$output_file' does not exist" >&2
  exit 1
fi

# echo <<EOFstring
# string='PRINT"{\$c1}{\$c2}{\$c3}{\$c4}" \
# ifwhateverthenstop\ngosub{:1001}:goto1001\n"
# EOFstring

# Desired output:
# PRINT "ABCD"
#  IF whatever THEN STOP
#  GOSUB {:1001}:GOTO 1001

# Lowercase BASIC keywords while leaving quoted strings untouched.

# convert C64List 3.05's "{alpha:upper}" to 3.50's "{alpha:alt}"
# this results in infinitely more readable quoted strings

if ! sed -i '
s/{alpha:upper}/{alpha:alt}/g
s/{\$a0}/ /g # shift-space -> space

s/{\$c1}/A/g
s/{\$c2}/B/g
s/{\$c3}/C/g
s/{\$c4}/D/g
s/{\$c5}/E/g
s/{\$c6}/F/g
s/{\$c7}/G/g
s/{\$c8}/H/g
s/{\$c9}/I/g
s/{\$ca}/J/g
s/{\$cb}/K/g
s/{\$cc}/L/g
s/{\$cd}/M/g
s/{\$ce}/N/g
s/{\$cf}/O/g
s/{\$d0}/P/g
s/{\$d1}/Q/g
s/{\$d2}/R/g
s/{\$d3}/S/g
s/{\$d4}/T/g
s/{\$d5}/U/g
s/{\$d6}/V/g
s/{\$d7}/W/g
s/{\$d8}/X/g
s/{\$d9}/Y/g
s/{\$da}/Z/g
' "$output_file"; then
  echo "Error: failed to normalize PETSCII placeholders with sed" >&2
  exit 1
fi

tmp_file="$(mktemp)"

if ! awk '
BEGIN {
  split("PRINT GOTO GOSUB IF THEN STOP", keywords, " ");
  for (i in keywords) {
    keyword_map[keywords[i]] = tolower(keywords[i]);
  }
}
# Normalize BASIC tokens outside of quoted strings so the listing matches
# modern conventions without disturbing literal output text.
function normalize_segment(segment,    keyword, pattern) {
  for (keyword in keyword_map) {
    pattern = "\\<" keyword "\\>";
    gsub(pattern, keyword_map[keyword], segment);
  }
  return segment;
}
{
  line = $0;
  result = "";
  while (match(line, /"([^"]*)"/)) {
    prefix = substr(line, 1, RSTART - 1);
    quoted = substr(line, RSTART, RLENGTH);
    result = result normalize_segment(prefix) quoted;
    line = substr(line, RSTART + RLENGTH);
  }
  result = result normalize_segment(line);
  print result;
}
' "$output_file" > "$tmp_file"; then
  echo "Error: failed to lowercase BASIC keywords" >&2
  rm -f "$tmp_file"
  exit 1
fi

if ! mv "$tmp_file" "$output_file"; then
  echo "Error: unable to update output file" >&2
  rm -f "$tmp_file"
  exit 1
fi

# change "(if|then)<condition>" to "(if|then) <condition>"
# sed -E s/then\[\^\ \]/then\ /g | \

# change "go(to|sub)<xxxx>" to "go(to|sub) <xxxx>"
# "\^\ " = 'not followed by a space"
# sed -E s/\(goto\|gosub\)\[\^\ \]/\\1\ /g # "goto 1000"
