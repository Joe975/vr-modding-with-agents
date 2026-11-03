# VR modding kit

Skills and project instructions for adding VR to existing flat-screen PC games with Codex or
Claude Code. The writeup behind it: [joe975.github.io/vr-modding-writeup](https://joe975.github.io/vr-modding-writeup/).

## Quick start

Open Codex or Claude Code in your mod's folder (an empty one is fine) and tell it:

> Read https://github.com/Joe975/vr-modding-with-agents and set up its kit in this repo for
> [game]. Then start the research pass.

That's it. The agent does the rest using the instructions below.

## For agents: setting up the kit

You've been asked to set up this kit in the user's mod repo (the current working directory).

1. Get the kit: `git clone --depth 1 https://github.com/Joe975/vr-modding-with-agents` into a
   temporary folder outside the user's repo. Note the kit commit now
   (`git -C <temp folder> rev-parse --short HEAD`); the clone is deleted in step 6.
2. Copy into the root of the user's repo, without overwriting anything that already exists
   (if a file exists, merge in the missing parts and say what you changed):
   - `templates/AGENTS.md` -> `AGENTS.md`. Fill in the bracketed parts with what you know (game
     name; engine, graphics API and headset once the research pass finds them). Leave unknown
     brackets in place and list them in `STATUS.md` under "Waiting on the human".
   - `templates/CLAUDE.md` -> `CLAUDE.md` (it just imports `AGENTS.md`).
   - `templates/STATUS.md` -> `STATUS.md`. Add the first log entry: kit set up, date, kit commit.
   - `templates/gitignore` -> `.gitignore`. It keeps voice recordings, captures, dumps and
     decompiler projects out of git.
   - `checklists/before-publishing.md` -> `checklists/before-publishing.md`.
3. Copy each folder under `skills/` into both `.agents/skills/` (Codex) and `.claude/skills/`
   (Claude Code), keeping the folder names. Both agents then find the same skills. Commands in
   the skills are written to run from the repo root with the `.agents/skills/...` paths.
4. Make a Python venv in the repo (`python -m venv .venv`) and install the harness scripts'
   packages into it:
   `.venv/Scripts/python -m pip install -r .agents/skills/vr-mod-test-harness/scripts/requirements.txt`
   (`.venv/bin/python` on Linux and macOS). Run the kit's scripts with that Python.
5. Ask whether the user wants voice-recorded playtests. If so, follow the one-time setup in the
   `vr-playtest-loop` skill with the same venv (it asks before downloading the speech model).
   Otherwise skip it; they can add it later.
6. Delete the temporary clone. Git marks its pack files read-only, so a plain delete can fail:
   use `Remove-Item -Recurse -Force <temp folder>` in PowerShell or `rm -rf <temp folder>`
   elsewhere. Commit the setup if the repo uses git.
7. Skills copied during a session may not load in that session. Don't wait for them: read
   `.agents/skills/vr-mod-research/SKILL.md` directly and follow it. Tell the user to restart
   Codex or Claude Code before the next session so every skill loads by name.
8. Tell the user what you set up in two or three lines, then run the research pass for their
   game. Don't write mod code during the research pass.

To update the kit later, repeat steps 1-3 and merge, keeping the user's `STATUS.md`, `AGENTS.md`
and `.gitignore` edits.

## For humans

| Path | Step | What it's for |
|---|---|---|
| [templates/AGENTS.md](templates/AGENTS.md) | all | Project instructions for your mod repo, shared by Codex and Claude Code |
| [templates/CLAUDE.md](templates/CLAUDE.md) | all | Claude Code entry point; just imports AGENTS.md |
| [templates/STATUS.md](templates/STATUS.md) | all | Blank scratch pad the agents keep up to date, so each session picks up where the last left off |
| [templates/gitignore](templates/gitignore) | all | Your repo's `.gitignore`: voice recordings, captures, dumps and decompiler projects stay out of git |
| [skills/vr-mod-research](skills/vr-mod-research/SKILL.md) | Do the homework | The research pass before any code |
| [skills/vr-mod-test-harness](skills/vr-mod-test-harness/SKILL.md) | Get the agent to test its own work | Letting the agent see, play and measure without you |
| [skills/vr-playtest-loop](skills/vr-playtest-loop/SKILL.md) | Playtest | Voice-recorded playtests, reproduce-before-fix |
| [skills/vr-controls-design](skills/vr-controls-design/SKILL.md) | Controls | Game capabilities, camera/input choices, interaction patterns and applicable defaults |
| [skills/vr-mod-game-patches](skills/vr-mod-game-patches/SKILL.md) | Game patches | Pinning the game build, one table for every address, porting it with a binary diff, a live check a fallback can't fool |
| [skills/vr-mod-release](skills/vr-mod-release/SKILL.md) | Sharing | The player package (installer, launch profile, updates) and a public repo with none of the game's code in it |
| [checklists/before-publishing.md](checklists/before-publishing.md) | Sharing | EULA, modding policy, anti-cheat, redistribution |

**By hand:** copy the `.md` files in `templates/` to your repo's root and `templates/gitignore`
as `.gitignore`, and fill in the brackets in `AGENTS.md`. Copy each folder under `skills/` into
both `.agents/skills/` and `.claude/skills/`, and install
`.agents/skills/vr-mod-test-harness/scripts/requirements.txt` into a venv.

## Adapting it to a game

Start from the game's actions and the hooks available, then choose camera and input modes
separately. Tracked aiming with button melee, a seated cockpit with ordinary steering, and a
tabletop view with tracked selection are all valid combinations. Record the choices, contexts,
action semantics and observable outcomes in the mod's `CONTROLS.md`.

Combat, body zones, skeletal IK and virtual gamepad output are optional patterns. The controls
skill also covers [objects, tools, puzzles and vehicles](skills/vr-controls-design/topics/interaction-patterns.md).
The [test-driver contract](skills/vr-mod-test-harness/references/test-driver.md) has melee, puzzle
and vehicle scenario examples. Implement the driver and game observations in the consuming mod;
the kit supplies expectation/query tools, not a universal game adapter.

The user is responsible for checking what the game's publisher supports and permits for
modding, anti-cheat and online play, and choosing the project's scope. The research pass gathers
dated sources and flags uncertainty; this kit doesn't impose a blanket offline-only rule.

Rendering work has two required reviews in the harness:
[GPU/AA compatibility and stereo correctness](skills/vr-mod-test-harness/references/rendering-compatibility.md),
and [representative performance and broad workarounds](skills/vr-mod-test-harness/references/performance.md).
The existing `STATUS.md` template holds their evidence matrix and workaround register; there are
no extra setup files. The release skill checks the built package's effective defaults against
that evidence. Missing hardware or measurements remain explicit gaps, not compatibility claims.

**Status:** distilled from one complete mod build. Not yet tested from a clean checkout in both
agents, so expect rough edges. The voice capture, interleave, frame check, trace query,
expectation and eye flicker scripts have unit tests (`tests/test_kit.py`); the live microphone path
and the both-eye mirror recorder have only been used on one machine.
The 2026-10-20 revision separates game capabilities, camera and input choices, and adds cross-genre
scenario examples tested against representative passing/failing metrics. These are contract tests,
not live validation in multiple games. The 2026-10-22 revision adds the release skill (player
package, public-repo cleanup), distilled from a release being prepared, not one that has shipped.

**Licence:** [MIT](LICENSE). Use it, change it, ship it in your own mods, commercial or not; just
keep the copyright notice with any copies of the kit itself.
