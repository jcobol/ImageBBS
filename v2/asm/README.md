# README

Some handy regexes to format source code in Kate:

`(:)(\S) -> \n\t\2` Search for : not followed by whitespace, replace with newline and tab

## Label files

Vice can also load label files created by the Acme assembler. Their syntax is e.g.
`labelname = $1234 ; Maybe a comment`. A dot will be added automatically
to label names assigned in this way to fit to the Vice label syntax.

Pipe the `.sym` file generated by `wine casm.exe <file.lbl> -sym | dos2unix` to fix line endings for Linux VICE.