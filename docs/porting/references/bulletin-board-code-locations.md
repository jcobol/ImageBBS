# Bulletin Board Code Locations

- The main BASIC host program `v1.2/core/im.txt` handles the bulletin-board subsystem. It dispatches the `SB` verb (sub-boards), presenting the message-base menus and editor entry points, and defines the editor UI text along with the `&,54` overlay hooks.
- The user-facing text editor invoked from the message bases is implemented by the machine-language overlay `ml.editor`, disassembled in `v1.2/source/ml_editor-converting.asm`. This overlay provides the editor command loop and manages the handset and memory routines.
