# Maintaining this kit

This file is for agents working **on the kit itself**. If you've been asked to set the kit up in
someone's mod repo, ignore this file and follow `README.md` ("For agents: setting up the kit");
the files to copy are in `templates/`.

## What belongs here

Only what mod developers copy and use: `README.md`, `LICENSE`, `templates/`, `skills/`,
`checklists/`, and `tests/` for the scripts. Nothing else.

- **Game-agnostic only.** No examples, numbers, names or screenshots from any particular game
  mod, and no references to the author's own project, notes, timeline or playtests. Turn a lesson
  from a specific mod into general advice ("a mod can report thousands of submitted pairs while
  the headset shows Waiting"), keeping any useful number as a starting default.
- Check applicability beyond game names: combat, skeletons, virtual pads and on-foot locomotion
  are optional capabilities, not universal prerequisites. Keep concrete patterns conditional;
  distinguish requested actions from observed game outcomes. Exercise the harness examples for
  melee, puzzle interaction and vehicles when changing the shared contracts.
- **No writeup content.** The narrative guide, its images, the site and the author's working
  notes live elsewhere and are not part of this repo. Don't add them back.
- Skills use the `SKILL.md` format with `name` and a trigger-rich `description`, and are written
  as instructions to an agent, not prompts in the human's voice.

## Before you commit

Run `python -m unittest tests.test_kit` (needs `numpy` and `pillow`). It checks the scripts, the skill
frontmatter, links, that the repo holds only the kit, and that no game-specific names slipped in.
CI runs the same tests on every push.
