; ----------------------------------------------------------------------
; ImageBBS 1.2B "ml.extra" overlay (stub)
; ----------------------------------------------------------------------
; The original machine-language overlay loaded after "im" has not been
; recovered.  The bootstrap swaps the binary into $2000/$d000 and the BASIC
; dispatcher relies on it for additional ampersand verbs, user-flag lookups,
; and colour/macro tables.  This file documents the expected entry points and
; provides deterministic placeholders so host-side ports have something to
; interrogate until the real asset is available.
; ----------------------------------------------------------------------
;
; Enhancements in this revision:
;   * Seed the lightbar bitfields that `chkflags` consumes so the left/right
;     check marks default to a coherent state during startup.
;   * Describe each of the 32 flag slots documented in the sysop manual so
;     host ports can surface meaningful labels while the real overlay is
;     missing.
;   * Capture the known "little modem" module names so tooling has parity
;     with the BASIC stub.
;
; References:
;   - Lightbar behaviour: Image 1.2B Sysop Manual §§“The Lightbar” and
;     “Lightbar functions, page 2”.
;   - Machine-language dispatcher: v1.2/source/ml-1_2-y2k.asm around $b24f.
;
; ----------------------------------------------------------------------
; Kernel-visible addresses expected by ml-1_2-y2k.asm
; ----------------------------------------------------------------------

chk_left        = $07f4     ; left-column lightbar flags (page 1)
chk_right       = $07f5     ; right-column lightbar flags (page 1)
lightbar_p2_l   = $42e5     ; left-column flags (page 2)
lightbar_p2_r   = $42e6     ; right-column flags (page 2)
undchr          = $42e7
undcol          = $42e8

; ----------------------------------------------------------------------
; Flag indices used by BASIC ampersand calls (&,52)
; ----------------------------------------------------------------------

FLAG_SYS_LEFT   = 0
FLAG_SYS_RIGHT  = 1
FLAG_ACS_LEFT   = 2
FLAG_ACS_RIGHT  = 3
FLAG_LOC_LEFT   = 4
FLAG_LOC_RIGHT  = 5
FLAG_TSR_LEFT   = 6
FLAG_TSR_RIGHT  = 7
FLAG_CHT_LEFT   = 8
FLAG_CHT_RIGHT  = 9
FLAG_NEW_LEFT   = 10
FLAG_NEW_RIGHT  = 11
FLAG_PRT_LEFT   = 12
FLAG_PRT_RIGHT  = 13
FLAG_UD_LEFT    = 14
FLAG_UD_RIGHT   = 15
FLAG_ASC_LEFT   = 16
FLAG_ASC_RIGHT  = 17
FLAG_ANS_LEFT   = 18
FLAG_ANS_RIGHT  = 19
FLAG_EXP_LEFT   = 20
FLAG_EXP_RIGHT  = 21
FLAG_FN5_LEFT   = 22
FLAG_FN5_RIGHT  = 23
FLAG_FN4_LEFT   = 24
FLAG_FN4_RIGHT  = 25
FLAG_FN3_LEFT   = 26
FLAG_FN3_RIGHT  = 27
FLAG_FN2_LEFT   = 28
FLAG_FN2_RIGHT  = 29
FLAG_FN1_LEFT   = 30
FLAG_FN1_RIGHT  = 31

; ----------------------------------------------------------------------
; Default lightbar state derived from manual descriptions.
; ----------------------------------------------------------------------
;
; The production overlay persists caller-visible toggles across sessions.
; Until the authentic PRG is recovered we expose conservative defaults that
; reflect an idle board awaiting its first caller: chat paging available, all
; other automation disabled, and ASCII/ANSI translation deferred until the
; user explicitly requests it.
;
DEFAULT_PAGE1_LEFT  = %00000001   ; SYS left set, remaining page-1 left flags clear
DEFAULT_PAGE1_RIGHT = %00000000
DEFAULT_PAGE2_LEFT  = %00000000
DEFAULT_PAGE2_RIGHT = %00000000
DEFAULT_UNDER_CHAR  = $5f         ; '_' underline placeholder for console mask
DEFAULT_UNDER_COLOR = $0f         ; bright white underline to mirror manual screenshots

; ----------------------------------------------------------------------
; Entry point exposed to the bootstrap so the overlay looks legitimate.
; ----------------------------------------------------------------------

                .org $2000

ml_extra_stub_entry:
        lda #DEFAULT_PAGE1_LEFT
        sta chk_left
        lda #DEFAULT_PAGE1_RIGHT
        sta chk_right
        lda #DEFAULT_PAGE2_LEFT
        sta lightbar_p2_l
        lda #DEFAULT_PAGE2_RIGHT
        sta lightbar_p2_r
        lda #DEFAULT_UNDER_CHAR
        sta undchr
        lda #DEFAULT_UNDER_COLOR
        sta undcol
        rts

; ----------------------------------------------------------------------
; Host-facing metadata: list each flag slot with its meaning and default.
; ----------------------------------------------------------------------
;
; Consumers running outside the C64 can walk `lightbar_flag_directory` to
; surface human-readable descriptions for each bit manipulated through &,52.
; Each entry is a pointer to a PETSCII string terminated with $00.  The
; trailing byte in every string records the stub’s default state (0=off,1=on)
; as exported above.
;
lightbar_flag_directory:
        .word flag_desc_00, flag_desc_01, flag_desc_02, flag_desc_03
        .word flag_desc_04, flag_desc_05, flag_desc_06, flag_desc_07
        .word flag_desc_08, flag_desc_09, flag_desc_10, flag_desc_11
        .word flag_desc_12, flag_desc_13, flag_desc_14, flag_desc_15
        .word flag_desc_16, flag_desc_17, flag_desc_18, flag_desc_19
        .word flag_desc_20, flag_desc_21, flag_desc_22, flag_desc_23
        .word flag_desc_24, flag_desc_25, flag_desc_26, flag_desc_27
        .word flag_desc_28, flag_desc_29, flag_desc_30, flag_desc_31

flag_desc_00:   .byte "SYS left: enable chat paging",0,1
flag_desc_01:   .byte "SYS right: BASIC trace output",0,0
flag_desc_02:   .byte "ACS left: adjust caller access",0,0
flag_desc_03:   .byte "ACS right: block 300 baud logons",0,0
flag_desc_04:   .byte "LOC left: local console login",0,0
flag_desc_05:   .byte "LOC right: pseudo-local maintenance",0,0
flag_desc_06:   .byte "TSR left: adjust time remaining",0,0
flag_desc_07:   .byte "TSR right: toggle prime-time window",0,0
flag_desc_08:   .byte "CHT left: enable chat mode",0,0
flag_desc_09:   .byte "CHT right: echo remote bells locally",0,0
flag_desc_10:   .byte "NEW left: freeze new-user signups",0,0
flag_desc_11:   .byte "NEW right: disable screen blanking",0,0
flag_desc_12:   .byte "PRT left: mirror output to printer",0,0
flag_desc_13:   .byte "PRT right: mirror logs to printer",0,0
flag_desc_14:   .byte "U/D left: lock file transfers",0,0
flag_desc_15:   .byte "U/D right: bar 300 baud in U/D",0,0
flag_desc_16:   .byte "ASC left: ASCII translation",0,0
flag_desc_17:   .byte "ASC right: force linefeeds",0,0
flag_desc_18:   .byte "ANS left: ANSI translation",0,0
flag_desc_19:   .byte "ANS right: IBM graphics",0,0
flag_desc_20:   .byte "EXP left: expert (no menus)",0,0
flag_desc_21:   .byte "EXP right: macro prompts",0,0
flag_desc_22:   .byte "FN5 left: ask about autologoff",0,0
flag_desc_23:   .byte "FN5 right: delay credit awards",0,0
flag_desc_24:   .byte "FN4 left: reserved",0,0
flag_desc_25:   .byte "FN4 right: reserved",0,0
flag_desc_26:   .byte "FN3 left: reserved",0,0
flag_desc_27:   .byte "FN3 right: reserved",0,0
flag_desc_28:   .byte "FN2 left: reserved",0,0
flag_desc_29:   .byte "FN2 right: reserved",0,0
flag_desc_30:   .byte "FN1 left: reserved",0,0
flag_desc_31:   .byte "FN1 right: suppress MCI",0,0

; ----------------------------------------------------------------------
; Convenience copy of the raw bitmaps so host tools can diff at runtime.
; ----------------------------------------------------------------------

lightbar_stub_bitmaps:
        .byte DEFAULT_PAGE1_LEFT
        .byte DEFAULT_PAGE1_RIGHT
        .byte DEFAULT_PAGE2_LEFT
        .byte DEFAULT_PAGE2_RIGHT

; ----------------------------------------------------------------------
; Placeholder palette/macros referenced by ml.editor and plus overlays.
; ----------------------------------------------------------------------

editor_palette_stub:
        .byte $0f,$01,$07,$0c  ; VIC-II colour IDs (white/black/cyan/orange)

macro_directory_stub:
        .byte 4
        .byte "+.lo",0
        .byte "+.modem",0
        .byte "+.lb move",0
        .byte "+.lb chat",0

                .end
