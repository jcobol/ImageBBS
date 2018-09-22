#!/bin/bash
# C64List .lbl linter -- fix some issues with .prg -> .lbl conversion

output_file="$1"
cat $output_file | \

# echo <<EOFstring
# string="{\$c1}{\$c2}{\$c3}{\$c4}\nifwhateverthenstop\ngosub1001:goto1001\n"
# EOFstring

# Desired output:
# {A}{B}{C}{D}
#  ifwhateverthen stop
#  gosub 1001:goto 1001

# echo -e $string | \
sed s/\$c1/A/g | \
sed s/\$c2/B/g | \
sed s/\$c3/C/g | \
sed s/\$c4/D/g | \
sed s/\$c5/E/g | \
sed s/\$c6/F/g | \
sed s/\$c7/G/g | \
sed s/\$c8/H/g | \
sed s/\$c9/I/g | \
sed s/\$ca/J/g | \
sed s/\$cb/K/g | \
sed s/\$cc/L/g | \
sed s/\$cd/M/g | \
sed s/\$ce/N/g | \
sed s/\$cf/O/g | \
sed s/\$d0/P/g | \
sed s/\$d1/Q/g | \
sed s/\$d2/R/g | \
sed s/\$d3/S/g | \
sed s/\$d4/T/g | \
sed s/\$d5/U/g | \
sed s/\$d6/V/g | \
sed s/\$d7/W/g | \
sed s/\$d8/X/g | \
sed s/\$d9/Y/g | \
sed s/\$da/Z/g | \

# change "then<condition>" to "then <condition>"
sed -E s/then\[\^\ \]/then\ /g | \

# change "go(to|sub)<xxxx>" to "go(to|sub) <xxxx>"
sed -E s/\(goto\|gosub\)\[\^\ \]/\\1\ /g # "goto 1000"