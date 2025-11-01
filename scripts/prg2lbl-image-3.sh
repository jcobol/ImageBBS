#!/bin/bash
# 2020/01/24 - rns
# c64list4.00 puts [] around unknown label #s
# to quell these issues, assign line numbers to those labels
# with preface file to {assign:Label=line #}

E_NOARGS=85
E_NOTFOUND=86
E_NOTPRG=87

if [ $# -eq 0 ]
        then # no command params
                printf 'Usage: %s <.prg_file> [<.lbl_file>]\n' "$(basename "$0")"
cat <<endofhelp

De-tokenize a C64 binary .prg file into C64List 4.0 .lbl file.
Invokes WINE, calls C64List 4.0. Uses Image BBS 3.0
{assign:}s to reduce "unknown label" errors.

If <.lbl_file> is not specified, the base name of <.prg_file> is
used for output, but with a .lbl extension.
endofhelp
exit $E_NOARGS
fi

if [ $# -eq 1 ] # 1 param: input_prg_file. output_lbl_file will be input_prg_file.lbl
then
	input_prg_file=$1
	output_lbl_file=${input_prg_file%.*}.lbl # cut .prg extension, replace with .lbl
	printf 'Converting %s to %s\n' "$input_prg_file" "$output_lbl_file"
	wine_args=("c64list4_00.exe" "$input_prg_file" -verbose "-lbl:$output_lbl_file" -ovr -keycase -varcase -crunch:off -alpha:alt -pref:image-3_0-assigns.lbl)
	wine "${wine_args[@]}"
	exit $?
fi

if [ $# -eq 2 ]
then # 2 params: input_prg_file and output_lbl_file
	input_prg_file="$1"
	output_lbl_file="$2"
	if [ ! -f "$input_prg_file" ]
	then
		printf 'File %s not found!\n' "$input_prg_file" >&2
		exit $E_NOTFOUND
	fi

	if [ "${input_prg_file##*.}" != "prg" ]
	# use braces in variable substitution
	then
		printf 'File %s is not a .prg file!\n' "$input_prg_file" >&2
		exit $E_NOTPRG
	fi

	if [ "${output_lbl_file##*.}" != "lbl" ]
	# use braces in variable substitution
	then
		printf 'File %s is not a .lbl file!\n' "$output_lbl_file" >&2
		exit $E_NOTPRG
	fi

	# Rotate numbered .bak backups (default depth is 5 or PRG2LBL_BACKUP_DEPTH).
	if [ -f "$output_lbl_file" ]
	then
		backup_depth=${PRG2LBL_BACKUP_DEPTH:-5}
		if [[ "$backup_depth" =~ ^[0-9]+$ ]] && (( backup_depth > 0 ))
		then
			if [ -f "${output_lbl_file}.bak.${backup_depth}" ]
			then
				rm -f -- "${output_lbl_file}.bak.${backup_depth}"
			fi
			if [ -f "${output_lbl_file}.bak" ]
			then
				mv -f -- "${output_lbl_file}.bak" "${output_lbl_file}.bak.1"
			fi
			for ((i=backup_depth; i>=2; i--))
			do
				prev=$((i-1))
				if [ -f "${output_lbl_file}.bak.${prev}" ]
				then
					mv -f -- "${output_lbl_file}.bak.${prev}" "${output_lbl_file}.bak.${i}"
				fi
			done
			cp -- "$output_lbl_file" "${output_lbl_file}.bak.1"
			printf 'Backed up %s to %s.bak.1 (depth %s)\n' "$output_lbl_file" "$output_lbl_file" "$backup_depth"
		else
			printf 'Skipping backup rotation for %s because depth "%s" is not a positive integer.\n' "$output_lbl_file" "$backup_depth"
		fi
	fi

	printf 'Converting %s to %s\n' "$input_prg_file" "$output_lbl_file"
	wine_args=("c64list4_00.exe" "$input_prg_file" -verbose "-lbl:$output_lbl_file" -keycase -varcase -crunch:off -alpha:alt -pref:image-3_0-assigns.lbl)
	wine "${wine_args[@]}"
	wine_status=$?

#    -d64:$d64file::`echo {$2}|tr `;
fi

exit ${wine_status:-$?}
