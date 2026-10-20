---
name: vr-mod-game-patches
description: Keep a VR mod working across game updates. Pin the game build and fail closed, route every hard-coded address through one per-build table, port that table to a new build with a function-level binary diff, and prove the port with a live check that can't be fooled by a fallback. Use when the headset suddenly shows nothing after the mod worked before, when the store has updated the game, when adding a hook, hard-coded address (RVA) or byte check, or when porting hooks to a new game build.
---

# Surviving game patches

Stores update games silently, often overnight. A mod that hooks addresses in the game's
executable breaks on every patch that moves code. The goal is that it breaks safely, says why in
one log line, and ports in hours rather than days. If the mod only uses a framework's stable API
and hard-codes no addresses, skip to the build check and the live check; they still apply.

## Recognise a patch first

- **Symptoms.** Hooks refuse to install, the stereo path never starts, the headset shows nothing
  or the session never becomes ready. It looks like a headset or runtime problem. Check the game
  build before debugging the headset, the runtime or recent mod changes.
- **Check the build.** Compare the exe's PE timestamp (and size of image or a hash, and the
  version string if the game shows one) with the build the mod was written against. Make the mod
  log that identity as its first line on every launch, with `known=true/false`.
- **Fewer surprises.** Ask the human whether to set the store to update the game only when it's
  launched (Steam has this per game) and whether test runs should launch the exe directly where
  the game allows it. That cuts surprise updates; it doesn't stop them.
- **Port or roll back** is the human's call. Rolling back to the previous build can unblock live
  testing sooner; porting keeps the mod on the version players have.

## Pin builds and fail closed

- Identify the build by timestamp plus size or hash. Before installing each hook, compare the
  bytes at the target (the prologue, or the instructions you patch) with the bytes recorded for
  that build.
- Unknown build, or bytes that don't match: don't hook. Log the module and the reason, and leave
  the game running without that feature.
- **Never hook a guessed address**: not a scan hit, not "everything nearby moved by the same
  amount". Only verified entries get hooked.

## One lookup layer for every address

Write every address, call-site check and byte pattern against one reference build, and ask a
single lookup for the running build's value:

- `rva(build, reference_rva)`: the identity on the reference build, the table entry on a ported
  build, and 0 (refuse) for an unknown build or an address that isn't in the table.
- `code(build, reference_rva, actual_bytes)`: compares only the bytes proven equal for that
  build; anything longer, missing or unknown fails closed.

The table is generated (one block per ported build), never hand-edited, and stores the new
build's verified byte windows so the tests can run without the game binary. Never commit game
binaries.

**A static test that every hard-coded address goes through the layer.** Scan the mod's sources
for named address constants and hex literals inside the image's range, and fail on any use that
isn't wrapped by the lookup (keep a short allowlist, each entry with a reason). It's the cheap way
to catch the address you missed. Comparisons are the easiest to miss: a return-address check
like `caller == CALL_SITE + 5` installs no hook, so nothing fails at startup; it just refuses
every call on the new build and switches a feature off.

Add tests for the ported build too: identification, the fail-closed cases, and each module's
byte matchers fed the new build's bytes (the reference bytes must fail there).

## Port with a function-level diff

1. **Keep the old binaries.** The store overwrites the exe in place. Copy the exe and DLLs of
   every build you analyse to a folder outside the repo, or keep the disassembler projects: a
   Ghidra project holds every initialised section and can be dumped back out as an RVA-mapped
   image to diff against.
2. **Map both builds** as RVA-addressed images and disassemble every function in the unwind
   table (`.pdata` on x64; capstone in an analysis venv is enough).
3. **Normalise** each function: mask rip-relative displacements, rel32 call and jump targets and
   image-relative displacements (`[base+index*scale+RVA]`); keep opcodes, registers, struct
   offsets and immediates. Equal normalised bytes mean the same code, moved. Changed functions
   are reported, never mapped automatically.
4. **Map globals, vtables and callees** through the matched instructions: each matched pair
   says where the old target went. Keep vote counts and refuse conflicting answers.
5. **Locate the rest.** Leaf functions without unwind data: check at the neighbours' shift.
   Sites inside a changed function: align instruction by instruction and accept only identical
   runs.
6. **Generate the table.** For each address in the mod's sources, record the new RVA and the
   verified prefix (whole instructions from that address whose normalised bytes are equal and
   whose targets correspond). Data addresses need a conflict-free entry from step 4.
7. **Record a signature** per code entry: the shortest masked pattern (8 to 64 bytes is a
   starting range) that is unique in the old code and finds exactly the translated address in
   the new code. On an unknown build the mod can scan the signatures and log candidate addresses
   for the next port, but it never hooks from a scan.
8. **Struct layouts.** Diff the non-stack displacements in recompiled functions, and check the
   functions the mod's offsets were read from are unchanged. Write down which layouts were argued
   from unchanged code and which were observed.

Expect most of a minor patch to be code that only moved. A large share of changed functions in
the code the mod touches means a real port, not a table regeneration.

## Data packs and overrides

If the mod ships overrides of the game's data files, a patch may change the originals. An
override built from the old files silently reverts the patch's own changes. Diff every
overridden source file against the patched game data, rebuild the pack from the new sources,
and make the pack builder refuse when a source file's hash has changed.

## Prove the port live

- A run checker that prints PASS/FAIL per hook installed or bound, fails on any build refusal,
  and requires the primary path to be running.
- **A fallback can pass a "frames delivered" check.** If the mod falls back to a flat panel or a
  mono view when stereo stops, the submitted-frame counter keeps climbing. Require the primary
  path explicitly (a minimum count of real stereo pairs from the stereo producer at the end of
  the run; 100 is a starting point) and fail on any stop or fallback log line.
- **Prove the checker discriminates.** Run it on a known-bad log (the pre-port failure, or a run
  with the fix reverted) and confirm it fails, and on a known-good run and confirm it passes.
- Then run the scripted scenarios that exercise the hooked features (`vr-mod-test-harness`).
  Symptoms that don't fit, like scripted hands that never move, are worth chasing before calling
  the port done.

## Effort and records

With agents, budget a few hours for the first port: address inventory, table generator, moving
the code onto the lookup layer, live check. Most of that is building the layer once; a later
patch that only moves code is mostly regenerating the table and rerunning the checks.

Keep a dated note per patch: both build identities, the method, the generated table, what wasn't
verified, and the exact commands to port the next one. Add a `STATUS.md` entry.
