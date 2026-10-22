---
name: vr-mod-release
description: Package a VR mod for players and make its repository safe to publish. Use when building an installer or launcher for players, turning a private mod repo into a public one, deciding what a release may contain (no game code, game data or decompiler output), shipping an update, or when the human asks how to share the mod.
---

# Releasing a VR mod

Two jobs: a repository that holds only your own work, and the package players run. Do the legal
checklist first: [before-publishing](../../checklists/before-publishing.md). Nothing here is
legal advice; publisher permission and the project's scope are the human's decisions.

## Nothing of the game's leaves your machine

A hooking mod accumulates game material without anyone deciding to ship it. Before a repo goes
public, find and remove:

- **Decompiler and disassembler output** (`*.c` from Ghidra, `*.asm` listings), crash minidumps
  of the game process, and game data files used as test fixtures. Tests that need game data
  read it from the player's own install at test time and skip when it isn't there.
- **Game code as byte literals.** Prologue checks, call-site patterns, build tables and
  "expected bytes" arrays are copies of the game's code. Replace each with a digest: the
  reference RVA, the length and the SHA-256 of the bytes there, hashed against the running
  build's bytes at run time (`vr-mod-game-patches` has the table layout). A ported build's table
  holds only offsets and the XOR delta of the bytes that moved, never the bytes. Signatures for
  finding addresses after the next patch are game bytes too: generate them into an ignored
  folder for an offline scan script, not into the repo or the DLL.
- **A test that keeps it out.** Scan tracked sources and tests for any run of 16 or more byte
  literals and fail unless the line is marked as mod-authored. Check the shipped DLL as well:
  search its bytes for every run that used to be in the sources, allowing only generic compiler
  prologues your own code also produces.
- **A test that the digests still match.** Against local images of every supported build (kept
  outside the repo, found through an environment variable, skipped when absent): each digest is
  the reference build's code at its RVA, and the ported build's code hashes the same once the
  delta is undone.
- **History.** All of the above is still in the private repo's history. Publish a fresh repo
  with one squashed initial commit of the cleaned tree and keep the private one for history.
  Before squashing, scan the tree for the file types above and the game's data formats, for
  local paths and usernames in logs, and for secrets. Trim validation bulk (screenshots,
  hundreds of logs) to what a contributor needs.
- **Dev tools count too.** Diagnostic scripts in the tree are published even if the package
  doesn't ship them. Hash their byte patterns or leave the scripts out of the public tree.
- **Licences.** Your own licence file, plus a third-party notices file shipped in the package
  for everything bundled: runtime loaders, an embedded interpreter, detour libraries.

## The package players run

The installers players praise share a shape: one download, numbered steps each with a status
line and a fix, one button whose label says what it will do, and nothing of the game's inside.

- **Build derived data on the player's machine.** Any pak, config or asset derived from game
  files is built at install from the player's own copy, with input hashes checked first and
  nothing written unless every input verifies. Ship the builders (or a compiled patcher), not
  their output. A game update then becomes a clear message ("game updated, waiting for a mod
  release") instead of a crash.
- **Pin the game build.** The package's version file names the supported game build and the
  input hashes. Preflight refuses an unknown build and says so.
- **Launch profile in the package.** The flags and environment the mod needs travel in a
  `launch.json` inside the mod package, so a mod release can change them without an installer
  release. Candidate and experimental switches become settings or defaults before release;
  players don't type flags. Test that the installer's launch equals the dev launcher's (have
  both print their environment and compare).
- **Leave a normal launch unmodded.** Copy the mod in at launch and remove it on exit, even
  after a crash: a lock file written at launch and removed on clean exit tells the next start to
  clean up. Record every file written in an owned-files list and remove exactly that list on
  uninstall; reject any path that escapes the game folder. If the modded launch differs from
  the store's (for example starting the exe directly, without its anti-cheat), say so in the
  window as well as the README, with the tested scope.
- **Preflight with plain fixes.** Game folder from the store's registry and library files, with
  a Change button; store client running; the right VR runtime active; another overlay or proxy
  DLL beside the exe (name it, say to remove it); store client or runtime running elevated; game
  folder writable (one elevation to grant an ACL, then everything runs unelevated).
- **Back up saves** automatically before the first modded launch, to a dated folder.
- **Preserve the player's settings across updates.** Calibrations and per-user config go in a
  preserve list and are merged per key: values the player changed stay, new keys and changed
  defaults come from the release. Keep the release's own copy alongside as the merge base.
- **Startup feedback.** A modded launch can take minutes. Tail the mod's log for phase markers
  (shaders compiling, VR session ready) and show them, so nobody assumes it hung.
- **Several ways to play are several buttons**, not a rebuild. If a camera or input mode is
  decided by which data files are installed, build every variant at install and offer each as
  its own Play button.
- **One-button crash report:** a zip of the newest run's log, trace and launcher facts
  (versions, OS, which binaries exist with sizes, mod DLL hash, game build id), with no memory
  dumps, so it can be posted publicly. Warn that logs may hold personal details.
- **Updates.** A manifest fetched from the repo (installer version, URL and hash; each mod
  version with URL, SHA-256 and size; an optional beta channel; changelog; the preserve list),
  every download checked against its hash, pinned dependencies, self-update by rename-swap with
  rollback. Publishing is one script that builds the zip, uploads it, writes the manifest and
  commits.
- **Gate publishing on recorded permission.** The publish script refuses to run until a dated,
  quoted permission (or the human's explicit decision to proceed without one) is recorded in a
  versioned file, and checks the target repo's visibility is what was intended.
- **Test it like the rest of the mod:** fixture zips, fakes for the system checks (an
  environment variable that pretends a process is elevated), parity tests between the installer
  launch and the dev launcher, an off-screen render of the window for review. Tests that need a
  tool the machine lacks skip cleanly rather than erroring.

## Before the first public release

- A playtest from the built package, not the dev scripts: install, play, quit, mod files gone.
- Someone other than the author installs from the zip with only the README.
- Every feature that is on by default has been played in the headset. Default off anything that
  hasn't held up.
- README for players first: unofficial and not affiliated at the top with a link to the
  official game site, requirements, what works and known issues, what a game update does to the
  mod, the tested online scope. Developer setup second.
- Code signing for the proxy DLL, or a README note about SmartScreen and antivirus warnings.
- Issues on, a tag, a version file and release notes.
