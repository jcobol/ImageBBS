# Agent Notes for ImageBBS Repository

## Entry Point Information
- The BASIC loader sets the main-loop vector to the `stack` routine in `v1.2/source/image12.asm`. When the program loads, execution begins in this routine, which clears the screen, prints the Image 1.2 banner, loads the `ml 1.2` machine-language module, and then jumps to `$c000`.
- Within the machine-language module, the initialization entry point is label `lbl_c000` in `v1.2/source/ml-1_2-y2k.asm`. It immediately jumps to `gotoc00b`, which completes the startup sequence by configuring loader parameters and continuing system initialization.

