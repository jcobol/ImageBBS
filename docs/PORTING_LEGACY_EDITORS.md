# Porting Legacy Editor Modules to Shared Input Helpers

This guide summarizes the steps we follow when modernizing the Image BBS 2.0
label files that still rely on their own disk I/O and editing loops.  The goal
is to swap those bespoke routines over to the shared helpers that already ship
with the new codebase while keeping each editor's original behaviour intact.

### Why the migration is worth the effort

* **Overlay compatibility:** The shared input helpers mirror the behaviour that
  the modern overlays expect, so once a legacy editor adopts them, any updated
  overlay can run unmodified—no bespoke patches or runtime surgery required.
* **Consistent maintenance:** Centralizing the record-loading and editing logic
  means fixes (like keyboard handling or cursor bugs) land in one place and
  automatically reach every ported module.
* **Lower future cost:** New UI capabilities—such as extended key mappings or
  device handling—only need to be built into the helpers.  Editors that still
  ship with their bespoke loops would otherwise require one-off rewrites to
  pick up those improvements.

The examples below are drawn from the `e.data` editor refresh, but the same
patterns apply to any of the legacy modules that own their own `get#` loops and
inlined keyboard handling.

## 1. Replace manual record-loading loops with `Input Any`

1. Ensure the module loads the input support code (look for `&,2,2` being
   available elsewhere in the build; the helper lives in `includes/input-any`).
2. Wherever the legacy code performs a `get#` loop to pull the raw record into a
   string, replace the loop with the shared helper.  For example:

   **Before**

   ```basic
   { :sub.get_data }
   ed$ = ""
   for i = 1 to 128
     get#2, a$
     if st% then exit for
     ed$ = ed$ + a$
   next
   return
   ```

   **After**

   ```basic
   { :sub.get_data }
   &,2,2       ' fetches the current record into a$
   ed$ = a$
   return
   ```

   The helper leaves the requested record in `a$`, matching the conventions used
   across the newer editor modules.  Copy the result into the buffer (`ed$`) that
   the rest of the routine expects.
3. Any caller that previously counted bytes or cleared `ed$` before reading
   should still do so—`Input Any` returns the raw record without side effects.

## 2. Delegate interactive editing to `Sliding Input`

1. Collect the values the helper expects **before** invoking it.  For `Sliding
   Input` (`&,1,32`) that means:

   **Before**

   ```basic
   { :sub.edit_string }
   print "?";ed$;
   do
     get a$
     ' bespoke cursor and insert/delete handling here
   loop until a$ = chr$(13)
   b$ = ed$
   return
   ```

   **After**

   ```basic
   { :sub.edit_string }
   od$ = ed$          ' original contents
   p$  = "{rvrs on} {rvrs off}{left}"  ' prompt template shared by modern editors
   w$  = od$          ' working buffer
   &,1,32             ' launches the shared editor
   ```

   These globals mirror the setup performed in the existing v2+ modules.  They
   ensure the cursor state and prompt text match the rest of the UI.
2. After the helper returns, read back the standard flags:

   * `tr%` reports whether the user confirmed or aborted the edit.
   * `an$` holds the new text when the edit is accepted.

   Reconcile those with the original variables the legacy routine used (for the
   e.data editor we keep `b$` and `ed$` in sync and set `tz` when changes are
   committed).
3. Preserve legacy special cases by handling them after the helper returns.  In
   the e.data editor, records 52–57 still perform a second `Input Any` call to
   gather the drive number; that logic lives outside the shared helper and works
   unchanged once the core string edit finishes.

## 3. Restore the function-key translation table

Many legacy editors once disabled their PETSCII function-key mapping strings.
When you move them to the shared input helpers, bring the translation table
back so F-keys match the rest of the system:

```basic
ft$ = ",:{f5}*?={f6}{f8}"  ' maps {f1}-{f8} to their printable equivalents
```

The exact contents should mirror the other modernized modules so the visual
output stays consistent.  The table is referenced anywhere the editor prints
text that might contain function-key tokens.

## 4. Align setup/teardown with the modern modules

* Open the command and data channels the same way the contemporary editors do
  (`open 15,...` and `open 2,...`) before the main loop begins.
* Leave the existing `close`/error paths in place unless the helper requires an
  additional cleanup step (the input routines do not).
* If the legacy editor caches device or drive numbers between edits, keep those
  variables intact—the shared helpers operate strictly on the current field.

## 5. Test the special cases

After migrating an editor, verify the behaviours that relied on the bespoke
loops still work:

* Records with multiple fields (e.g., the device/drive pairs in records 52–57).
* Cursor movement, insert/delete handling, and quitting with no changes.
* Any keyboard shortcuts that depended on the old translation table.

Running through those flows in the target environment confirms the shared
helpers are wired correctly without regressing the legacy data handling.
