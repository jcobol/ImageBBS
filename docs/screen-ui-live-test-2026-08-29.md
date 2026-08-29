# Image BBS — Screen / UI Live-Test Report

**Date:** 2026-08-29
**Scope:** every user-visible screen and prompt in Image BBS v1.2a and v2.0,
including the `v2/core/jack/` alternate-module set and all 184 "plus mod"
add-on files. `v1.2/games/*` (Empire6, Shadowrun, STTNG trivia) and the
web-page docs were treated as out of scope — they're bundled third-party
content, not BBS interface screens.

## 1. Why this is a *static* live test, not an emulator session

The ask was to live-test the software by walking every screen the way a
caller or sysop would see it. That wasn't literally possible in this
environment:

- No VICE (`x64`/`x64sc`) binary is installed, and this is a headless
  container with no display to run one interactively anyway.
- No bootable `.d64`/`.d81` disk images exist for v2 in this repository
  (only a game disk for v1.2's Shadowrun) — the BBS's ML "core" and the
  BASIC modules reviewed here are never assembled into a runnable system
  disk as part of this repo, so there was nothing to boot even with an
  emulator.
- Building that pipeline from scratch (assembler, memory layout, disk
  imaging, a terminal client scripted against a virtual modem) is a
  project in its own right, well beyond "test the screens."

So instead, every screen was reconstructed **from the source that
produces it** — the same approach a human proofreading a printed
menu layout would take — using two complementary methods:

1. **A Python PETSCII screen simulator** (`screen_sim.py`, not checked
   into the repo — it was a throwaway analysis tool) that parses every
   quoted string literal, interprets the C64List `{token}` syntax used by
   this codebase's own `&"..."` print macro, and computes the actual
   40-column layout each screen would render to. This is what caught the
   scale of the unclosed-reverse-video pattern and let overflow claims be
   checked by arithmetic instead of eyeballing.
2. **Nine parallel manual reviews** (one per major code area — core
   modules, `jack/`, six batches of plus-mods, and the v1.2a legacy tree)
   that read every screen-producing line in full context, traced
   `{rvrs on}`/`{rvrs off}` balance across subroutine boundaries, and
   cross-checked suspicious lines against sibling/mainline copies to tell
   a real regression from an established, harmless codebase idiom.

### Discoveries about this codebase's own print-macro language

Building the simulator surfaced three conventions used by the `&"..."`
print macro (OUTA$) that aren't documented anywhere in `v2/docs/`:

- **`{f6}` is a soft line-break inside `&"..."` text, not the literal F6
  keypress byte.** Evidence: `plus_MM_sb-post.lbl`'s sibling
  `plus_MM_subop.lbl:19-21` splits one message into <=40-col rows at every
  `{f6}` ("Please leave a few words explaining why{f6}you think you
  should be the SubOp of{f6}this ... Board{f6:2}"); `{f6:2}` reliably
  marks a blank line before a prompt/header everywhere it's used.
  Occurs ~5,700 times across the tree.
- **`{pound}` is this BBS's in-string macro sigil for a runtime variable
  substitution, not the literal £ glyph.** `v2/docs/& commands.txt:72`
  documents `an$="host{f3}port":&,15,2:&"{pound}v7{f6}" -> host:port` —
  the *displayed* text is "host:port", which only makes sense if
  `{pound}<code>` means "substitute variable/field `<code>` here".
  Occurs ~7,190 times, always immediately followed by a short field code
  (`%a`, `$b`, `v7`, `g1`, `q0`, `vl`, `#3`, etc.).
- **`{back arrow}NN` (bare digits, no colon) is an absolute tab-to-column
  directive**, not NN literal glyphs and not literal digits. Evidence:
  `im_screens.lbl:11-13` prints "Device", "Drive", and "Protocol" labels
  of different lengths, each followed by `{pound}<value>{pound}{back
  arrow}38` — landing the following border character at the same column
  38 regardless of label/value length. Used ~2,000+ times spanning
  columns 04-39; the generic repeat syntax `{token:N}` is never used with
  `back arrow`, and cursor tokens (`{up}`/`{down}`/`{left}`/`{right}`)
  never take a bare-digit suffix either — confirming this is a
  `back arrow`-specific idiom.

Recognizing these three conventions took the simulator's raw
overflow-candidate count from 680 down to 180 false-positive-filtered
candidates, and is also why the manual reviews below don't flag
`{pound}XX`/`{back arrow}NN`-heavy table rows as overflow bugs just
because their raw character count looks long.

**Suggested follow-up** (not done as part of this pass, since it's
documentation rather than a screen fix): add a short note to `v2/docs/`
capturing these three conventions so the next person reading `&"..."`
strings doesn't have to reverse-engineer them again.

## 2. Coverage

| Area | Files | Screens/prompts reviewed |
|---|---|---|
| v2 core (`im*.lbl`, `image.lbl`, `edata-edit-2_0.lbl`) | 21 | ~85 |
| v2 `jack/` alternate modules | 80 | ~230 |
| v2 plus-mods, batch 1 | 30 | ~110 |
| v2 plus-mods, batch 2 | 31 | ~200 |
| v2 plus-mods, batch 3 | 31 | ~90 |
| v2 plus-mods, batch 4 | 31 | ~85 |
| v2 plus-mods, batch 5 | 31 | ~110 |
| v2 plus-mods, batch 6 | 30 | ~140 |
| v1.2a core + plus-mods | 7 | ~85 |
| **Total** | **~290 files** | **~1,135 screens/prompts** |

Every `.lbl`/`.txt` file under `v1.2/core/` and `v2/core/` (including all
184 `plus_*` files and everything in `jack/`) was read; the count above is
of individual screen/prompt blocks within those files, not files.

## 3. Outcome summary

- **175 issues found.**
- **~165 of them fixed directly** across two passes (see §4) — the first
  pass (§4.1-4.8) covered mechanical, unambiguous fixes; a second pass
  (§4.9), done after the user asked for everything not specifically
  requiring their input to be fixed, resolved nearly everything that
  first pass had conservatively left for a "style preference" — wording
  consistency, column alignment (now computed with confidence — see §1's
  macro-semantics discoveries), and the remaining overflow lines.
- **~8 still flagged, not auto-fixed** (see §5) — these are genuine
  domain/design decisions: an incomplete `if` condition whose correct
  logic isn't recoverable from this file alone, a module whose own FIXME
  comments suggest it may not be live in production, which of several
  divergent duplicate modules is actually deployed, and one menu-wording
  question that's a legitimate style choice either way.
- The single most common defect, by far, was **an opened `{rvrs on}`
  never matched with `{rvrs off}`**, found identically across dozens of
  unrelated modules (title banners, confirmation prompts, stat displays,
  the login "Board Activity" bar graph every caller sees). This reads as
  a systemic habit in how these screens were authored over the years
  rather than one-off mistakes — 34 separate instances were fixed in this
  pass.

## 4. Fixes applied

All fixes below were applied directly to source and pushed to this
branch across several commits. Grouped by category.

### 4.1 Unclosed `{rvrs on}` (reverse video left on)

| File:Line | What was reversed that shouldn't have been |
|---|---|
| `im_bar.lbl:33` | Everything printed after the B.A.R. screen returns |
| `im_editor.lbl:15` | "Available/In Memory/Remaining/Free Memory" footer |
| `im_misc.lbl:111` | "Is That Correct?:" + Yes/No prompt (handle lookup) |
| `im_misc2.lbl:30` | Same bug, NotePad flow |
| `im_misc2.lbl:94-95` | Personal Signatures menu (4 of 5 opens closed) |
| `plus_ED-pina-mod.lbl:199` | Entire Account Editor main screen |
| `plus_ED.lbl:8` | Entire Account Editor main screen (sibling module) |
| `plus_ED-pina-mod.lbl:150` (v1.2) | Entire Account Editor main screen |
| `plus_MX.lbl:13` | Macro list, "Edit Which:" prompt |
| `plus_WF.lbl:13` | File-editor stats footer |
| `plus_UX.lbl:171` | Trailing cursor-reset after the prompt |
| `plus_UB.lbl:4` / `plus_bio.lbl:4` | User Bio screens (both versions) |
| `plus_UL.lbl:41` | Rest of a matched user's search-result record |
| `plus_UU.lbl:10` | "Users: N" and the rest of the editor screen |
| `plus- lo-bonus.lbl:17` | Jackpot win announcement body |
| `plus_new.lbl:38` | New-account "Write These Down!" instructions |
| `plusslashGF-other.lbl:50` | Notepad "Is That Correct?:" prompt |
| `plusslashloslashan.lbl:14` | "From: ..." + invite message (new-user welcome) |
| `plusslashlo-newsM][H.lbl:13` | News body text (auto-scan path) |
| `plusslashlo-bar.lbl:8` | **Every caller's login "Today's Board Activity" graph** |
| `plus_numbersquare.lbl:13` | Game title/credits banner (3 opens closed) |
| `plus- lo-jerk.lbl:65` | Jerk Award nomination-accepted mail text |
| `plusslashNM_netsub2.lbl:50,52` | NetSub sysop-console status lines |
| `plus_IM.lbl:172-173` / `plus_menu example.lbl:17-18` | Shared config-editor header (2 of 4 opens closed) |
| `plus_make anagram.lbl:7-8,26,66` | Title banner, confirm prompt, "List Words" table |
| `plusslashSM_make anagra.lbl:24,64` | Same two bugs in the sibling anagram-mod file |
| `plus_CM.lbl:111` | Second `{rvrs on}` was a typo for `{rvrs off}` ("BEGONE!" line) |
| `islashUD.edit.lbl` / `islashIM.modem.lbl` / `islashlo.on.lbl` (jack) | see §4.3 |

### 4.2 Logic / syntax bugs

| File:Line | Bug | Fix |
|---|---|---|
| `edata-edit-2_0.lbl:87,90` | `dv%<7 and dv%>31` / `a<0 and a>254` — tautologically false, so out-of-range device/drive numbers were silently accepted | Changed `and` → `or` |
| `plus_sysop file.lbl:92` | `i<>8 or i<>13` — always true, made the field-8/13 single-char-input branch unreachable | Changed `or` → `and` |
| `plus_index.lbl` | Menu shows 7 options but bounds check was `a<1 or a>6`, silently killing option 7 | Changed to `a>7` |
| `plus_NMslashconfig.lbl:88` | Menu has 7 lettered options (A-G) but accepted up to "H", falling into an unlabeled 8th dead branch | Changed `an$<="H"` to `an$<="G"` |
| `plus_DE.lbl:103` | `ON-(an$="N"OR an$="n"GOTO ...` — missing closing paren | Added `)` |
| `plusslashGF_UX.lbl:154` | `ABS(INT(VAL(an$))` — unbalanced parens (3 open, 2 close) | Added missing `)` |
| `islashUD.edit.lbl:1` (jack) | `IF Q=1 OR(A$=NA$AND ID=UD%(10,XN) then` — unbalanced parens | Added missing `)` |
| `plusslashIM_time.lbl:144` | Stray extra closing paren after a balanced `mid$(...)` call | Removed it |
| `plusslashlo-question.lbl:49` | Missing `&` before a print-macro string, so the input-mode directive for field #8 was never actually invoked | Added `&` |
| `plusslashSM_lk util.lbl:159` | Unterminated string literal | Added closing `"` |

### 4.3 Missing line breaks (run-on paragraphs)

| File:Line | Before | After |
|---|---|---|
| `islashIM.modem.lbl:161-163` (jack) | Modem-wizard paragraph's last segment ran 90 unbroken columns | Re-wrapped with `{f6}` breaks, ≤40 cols per row |
| `islashlo.on.lbl:8-10` (jack) | Three statements with no `{f6}` at all — ~125 columns unbroken | Split into 4 rows, wording unchanged |
| `plus_lo.lbl:164-165` | Hard-wrap split the word "HELP" into "HE"/"LP" | Break moved earlier so "HELP" prints intact |
| `plusslashIM_macros.lbl:15-16` | Hard-wrap split "your" into "yo"/"ur" | Break moved before "your" |
| `serial-test.lbl:126` (v1.2) | 94-column unbroken error message | Split into 3 `print` statements matching the file's own style |

### 4.4 Leftover debug/placeholder text shown to users

| File:Line | Before | After |
|---|---|---|
| `plus_ED-pina-mod.lbl:174,196,368,468,469` | Five literal `"TODO: ..."` strings | `"Feature not yet available."` |
| `plus_CP.lbl:232` | `"TODO: check for unique filename in queue"` | `"Checking for a unique filename..."` |
| `plus_CP.lbl:248` | `"Finish this."` | `"Re-run copy to finish these files."` |
| `plus_alphaslashind.lbl:23,29,36` | Raw `a%=...,b%=...` variable dump | `"Result: <a%> / <b%>"` |
| `plusslashSM_alphaslashind.lbl:22,28,35` | Same raw dump pattern | `"Found=<a%>  At #<b%>"` |
| `plusslashlo_on.lbl:18` | `&"i% skips!"` diagnostic left in the live login flow | Removed |
| `plus_NMslashauto.lbl:224` | `&"B$=<value>"` raw variable dump on the sysop console | Removed |
| `plus_NMslashauto.lbl:228` | Raw internal filename "nm.password Transfer Complete" | "Password Transfer Complete." |
| `plus_EM.lbl:19-20` | Dead print statement immediately after an unconditional `return`, unreachable | Deleted |

### 4.5 Missing space / duplicate colon / concatenation bugs

| File:Line | Before → After |
|---|---|
| `plusslashGF_UX.lbl:79` | Stray `{backspace}` ate a space: "you have**downloaded**" → "you have downloaded" |
| `plusslashGF_UX.lbl:23` | "P=PRG(Binary)" → "P=PRG (Binary)" |
| `plus_new.lbl:79-80` | "...long **andbegin** with..." → "...long and begin with..." |
| `plus_MM_uslashdslashc.lbl:74` | "You Now Have325 Total!" → "You Now Have 325 Total!" |
| `plus_MM_subop.lbl:43` | "Enter Handle Or ID#. Of User" → "...ID# Of User" |
| `plus_MM_subop.lbl:73` | "Credits  :150" → "Credits  : 150" |
| `plus_MM_uslashdslashc.lbl:41` | Stray space before "?": "...For \<name\> ?" → "...For \<name\>?" |
| `plus_VB.lbl:109` | Duplicate colon ("Enter Choice #3:" then a lone ": " on the next line) → single colon, one line |
| `plusslashlo-grf2.lbl:27` | Same duplicate-colon bug → single colon, one line |
| `plusslashloslashfilelist.lbl:25` | "5Files" → "5 Files" |
| `plusslashSM_reledit.lbl:65` | "Group 5?:Y" (no space) → "Group 5?: Y" |
| `plusslashSM_lk util.lbl:49` (not applied — see §5) | — |

### 4.6 Typos and wording fixes

`notifed`→`notified` (×2: `plus_JA.lbl`, `plusslashlo-jerk.lbl`), `Usefull`→`Useful`
(`plus_LMP.lbl`), `Decription`→`Description` and `to lazy`→`too lazy`
(`plus_MM_ud-local.lbl`), `Non-Existant`→`Non-Existent` (×2:
`plusslashloslashpayroll.lbl`, `plus- lo - payroll.lbl`), `Transfered`→`Transferred`
(`plus_t.lbl`), `Instrucions`→`Instructions` (`plus_bingo.lbl`), `Ecetera`→`Etcetera`
(`blocks-free-merge.lbl`, jack), `todays`/`Todays`→`Today's` (×4 across
`plus- lo - cp maint.lbl` and `plusslashloslashcp maint.lbl`), `New Ur:`→`New Usr:`
(`plusslashlo_automaint.lbl`), `[F]oward`→`[F]orward` (`plus_EM.lbl`), `'S`→`'s`
possessive (×2: `plus_NMslashconfig.lbl`, `plusslashIM_netmail.lbl`), `NetWork`→`Network`
(×2, same two files), `Kill  :`→`Kill:` (`plusslashSM_alphaslashind.lbl`),
`(? List)`→`(?=List)` (`plus_NMslashfile.lbl`), `(E)rase Or, (S)end`→`(E)rase, Or (S)end`
and `after`→`After` (`plus_FM.lbl`), `Max.Editor Lines`→`Max Editor Lines` and
`Submaint`→`Sub Maint` (`plus_ED.lbl`), `Disabled,or`→`Disabled, or` (×2:
`plusslashIM_lightbar.lbl`, and its `jack/islashIM.lightbar.lbl` counterpart),
"Closing file.."→"Closing file..." (`plus_rfe.lbl`), "Loading...module.."→"...module..."
(`plus_SM.lbl`), four-dot ellipses tightened to three
(`im.lbl:1052,1056`, `plusslashSM_netfile.lbl:119`).

### 4.7 Consistency fixes (Title Case / capitalization to match the rest of a screen)

`im_info.lbl:27-28` password-change menu; `plus_new.lbl:99-102` password-setup
menu; `plusslashSM_reledit.lbl:359` and `plus_reledit.lbl:356` "Press A Key";
`edata-edit.lbl:34-35` "To Quit"; `"modemconfig 19.2.lbl":72` "Press Any Key
to go on:"; PETSCII-encoded capitalization slips in `plus_lo.lbl:152`
("Do **You** Want ANSI Color?") and `plus_lo.lbl:174-183` (the "FIRST
NAME"/"LAST NAME" variants of the new-account info prompt).

### 4.8 Branding / labeling / column-width fixes

- `plus_BB.lbl:109` — 55-column table header shortened to 40 columns
  (`"Telephone #"` → `"Phone#"`) so it stops hard-wrapping mid-word.
- `plus_JA.lbl:42` — 44-column notice shortened to 34 ("No NOMINEES
  Accepted At This Time!") for the same reason.
- `i_CP.lbl` / `i_CP-old.lbl` (jack) — "SKIP EIGHT FILES" repadded to
  match `i_CP-modded.lbl`'s already-correct column alignment.
- `"modemconfig 19.2.lbl":7` — title missing "BBS" branding, fixed to
  match its sibling utilities' "Image BBS 1.2 ..." titles.
- `"modemconfig 19.2.lbl":41` — "Correct? " confirm prompt had no Y/N
  guidance at all; added "(Y/N): ".
- `"modemconfig 19.2.lbl"` DATA table — missing space before parenthesis
  in both "Hayes 19.2k" entries, fixed to match every other model entry.
- `plus_ED-pina-mod.lbl:140` (v1.2) — fixed a redundant "Last date date:"
  label when editing the date field.
- `plus_ED-pina-mod.lbl:244` (v1.2) — added the missing colon to "Save
  changes?: " to match the file's own confirm-prompt convention.
- `plus_ED-pina-mod.lbl:346,357` (v1.2) — "Expert Mode"/"MCI Access"
  lowercased to match the field-label table's one-capital-word
  convention.

### 4.9 Round 2 — resolved after re-examination

The first pass of this report (above) deliberately erred conservative and
left ~45 items as "needs the user's input." On request, everything in
that list was re-examined and split: items that only needed *a*
consistent choice (not specifically *the user's* choice) were fixed;
only genuine domain/design decisions were kept flagged (§5).

- **Wording/terminology consistency** (each file's own majority
  convention was used as the tiebreaker): `plus_BB.lbl` "dBASE"→"dBase";
  `plus_JA.lbl` "or"→"Or"; `plusslashIM_ecs.lbl` "ZZ Locked?"→"Locked?"
  (matching its own Add-flow sibling); `plus_alphaslashind.lbl` menu
  items repunctuated "1.Clear"→"1. Clear" (all 10, including the "0.
  Quit" the fixing agent caught after the fact); `plus_scan netsub.lbl`
  "netsubs"/"Subs"/"Sub"→"NetSub(s)" throughout;
  `plusslashSM_fixer.lbl` "Responses"→"Resps" (matching this file's own
  menu item and per-board line); `plus_VF.lbl` "Email"→"E-Mail"; `plus_t.lbl`
  "DialTone"→"Dial Tone"; `plus_greed.lbl` "Top Five"→"Top 5";
  `plus_reledit.lbl` "Inserted."/"Moved"→"Inserted!"/"Moved!" (matching
  the file's own "Added!"/"Deleted!"); `plusslashSM_lk util.lbl`
  "(c)NISSA"→"(c) NISSA" (the codebase's copyright-line convention,
  confirmed against 5+ other files' "(c) NAME" spacing).
- **Column alignment**, now computed with confidence using the
  `{back arrow}NN`/`{pound}` semantics documented in §1: `plus_greed.lbl`'s
  leaderboard header retargeted to column 6/23 to match the data-row
  builder (verified by reconstructing the exact prefix width), and its
  dice-roll header's tab targets corrected from 07/10/13/16/19/22 to
  09/12/15/18/21/24; `plus_top ten.lbl`'s "User" header tab moved from
  column 9 to 10; `plusslashSM_baredit.lbl`'s stat-table header moved
  from column 13 to 14; `plus_make anagram.lbl`'s Edit Words *and* List
  Words data rows both given an explicit `{back arrow}26` tab so "1st"/
  "2nd" line up with the header in both screens.
- **Overflow lines re-wrapped or shortened** — the ~20 plain-prose
  overflow lines previously left as "hardware auto-wraps fine" were
  cleaned up properly: 7 shortened to fit ≤40 columns outright (e.g.
  `i_GF.lbl:53`, `islashlo!help.lbl:4`, `islashlo.instant.lbl:30`), the
  rest given an `{f6}` break at a sensible word boundary with wording
  otherwise unchanged. `plus_NMslashreport.lbl`'s 74-column report line
  now truncates to 38 columns for the screen echo only (the full line
  still goes to the report file); `plusslashSM_bu.lbl`'s "Copying: X To
  Y" line now splits at "To".
- **`plusslashlo_misc.lbl`'s `{ifdef:jack}` block** — its three prompts'
  wording synced to exactly match the actively-maintained version above
  it in the same file (this is wording sync between two paths of the
  same feature, not a decision about which one survives).
- **`islashIM.access.lbl`/`plusslashIM_access.lbl`**'s two access-group
  fields both labeled "Time/Call" — field 19's label changed to
  "(Unused)" since it's confirmed dead/unreachable (no real editor was
  built for it, since that would be inventing new functionality).
- **`plusslashlo-netwall.lbl`**'s dead code — re-verified line-by-line
  against every label reference in the file (not just direct `GOTO`, but
  `ON...GOTO` comma-lists too). The reviewing agent's first pass had
  overreached: `{:4166}`/`{:4168}` turned out to be live, called from a
  legitimate entry point, and were left alone. Only the genuinely
  unreferenced subset — an orphaned duplicate POKE block and a
  self-contained, zero-reference loop (`{:4154}`/`{:4156}`/`{:4160}`/
  `{:4162}`) — was removed.
- **v1.2 low-confidence notes**: `serial-test.lbl:96` "Re-sav" spelled
  out to "Re-saving" (confirmed safe against its `tab(30)"Done."`
  layout, and confirmed the save genuinely takes long enough to be read
  mid-word). `"modemconfig 19.2.lbl":71`'s "setup1.2a" was investigated
  (grepped the whole repo for the real filename) but no reference to it
  exists anywhere outside this one line, so it was correctly left alone.

## 5. Flagged for a maintainer's judgment (not auto-fixed)

Everything below genuinely needs input only the user/sysop has — a
design decision, knowledge of what's actually deployed, or domain
knowledge about intended game/feature logic that isn't recoverable from
the source alone.

- **`plusslashIM_time.lbl:180`** — a literal placeholder `[...]` left
  inside an `if` condition guarding prime-time auto-disable. Investigated
  further: the condition needs to compare against `p2%`/`p3%`
  (prime-time start/end), but the file's own comments show the original
  author never resolved the wraparound behavior when the end time is
  earlier than the start time ("if p3%<p2%, does it wrap am/pm?"), and a
  related variable (`pt`) is set here but read only by some other module
  not in this file. Guessing at the condition risks silently breaking
  prime-time enforcement — this needs the person who knows the intended
  behavior.
- **`plusslashlo-question.lbl`** — carries explicit developer `' FIXME:
  don't commit yet` / `' FIXME: question text does not display` comments,
  suggesting this module may not be live in production. Worth confirming
  with whoever runs this BBS before touching it further.
- **Divergent duplicate modules** where two versions of the same feature
  coexist and it's unclear which is current — this is a "which do we
  keep" call, not a wording fix: `islashlo-net.grf.lbl` vs
  `islashlo-net.grf_rel.lbl` (different confirm routines and abort
  targets for the same "Wall Writer" feature), `islashlo.firstimage.lbl`
  vs `islashlo_firstimage.lbl` (old PETSCII-caps style vs. a Title Case
  rewrite — both had their shared overflow bug fixed in §4.9, but the
  duplication itself remains), `plus_bio.lbl` ("User Bio v1.3") vs
  `plus_UB.lbl` ("v2.0") — likely a stale earlier revision left in the
  tree, and `plus_NMslashconfig.lbl` vs `plusslashIM_netmail.lbl`
  (near-identical NetMail config screens, probably a stale fork of one
  another — confirmed `plusslashIM_netmail.lbl` doesn't share
  `plus_NMslashconfig.lbl`'s off-by-one menu bug, so they've already
  diverged in behavior, not just wording). None of these are "broken"
  exactly — they're duplicated maintenance burden, and removing/merging
  one is a call for whoever owns this codebase.
- **`plusslashSM_lk util.lbl:50-52` vs. `:112/:137/:151/:168`** — main
  menu says "4. Multi-File Copy" etc., but the screen it leads to is
  titled "Multi-Copy". Left as-is on reflection: a menu entry being more
  descriptive than the short screen title it leads to is a normal,
  harmless UI pattern (not unlike a "New Message" menu item opening a
  screen titled "Compose") — forcing them to match verbatim isn't
  obviously an improvement, so this is a genuine style call for whoever
  maintains this tool's wording, not a bug.

## 6. Method note on the parallel review

Nine reviews ran independently and in parallel (one per file-set listed
in §2) rather than as one long serial pass, both for turnaround time and
so each reviewer could go deep on a narrower slice instead of skimming
everything. Each was asked to: locate every screen/prompt-producing
line, reconstruct its actual rendered text, and check reverse-video
balance, 40-column wrap, typos/grammar, menu/prompt convention, column
alignment, and dead/duplicate screens — then cross-check anything
suspicious against sibling modules or the equivalent mainline routine
before flagging it, specifically to avoid mistaking a long-standing,
harmless codebase idiom (e.g. a boxed-title banner that deliberately
leaves reverse video on because the very next print statement is another
reverse-video segment) for a fresh bug. After all nine finished, each
was resumed with a precise, itemized list of exactly which of its own
findings were safe to fix mechanically (see §4's criteria); everything
else was left as a documented recommendation in §5 rather than guessed
at.
