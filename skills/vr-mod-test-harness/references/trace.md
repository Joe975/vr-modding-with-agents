# Gameplay trace

A fixed-rate JSON-lines file the mod writes during a run (30 Hz is plenty; opt-in). It lets the agent
check "my hands drift off the body" or "the parry didn't fire" against data instead of memory.
Build it before the first playtest that's about feel.

## Header

- Wall-clock start time (with timezone), so it lines up with voice notes.
- Mod version/commit, settings in force, sample rate.

## Every sample

- **Tracked head and hands**, raw, in metres.
- **What the mod sent to the game**: the virtual pad state.
- **The game's idea of the player**: the character's head and hand bones as the animation left
  them, IK targets and where the hands ended up, weapon bones, camera mode (normal, cutscene,
  external), and the controlled character.
- **The deltas, already worked out**: eye minus the character's head bone, tracked wrist minus the
  animated hand, IK miss distance. In metres, in the character's own axes, so they don't change
  when you turn.

Use `null` for anything missing rather than leaving it out, so "not tracked" differs from zero.

## Events

- Every button edge, named by what it does ("LB parry/block down").
- Every gesture decision, near misses included ("guard rejected, controller pointed forward",
  "grenade put back, release at 0.4 m/s").
- Cutscenes, pause, focus loss and return, recentres, character changes.
- Animation takeovers (knockback, grabs). If you haven't hooked the game's animation state, infer
  it, e.g. flag a takeover when the animated head bone moves 25 cm from its usual spot for 200 ms.
  Leave those spans out of drift numbers.

## Session summary

A script that turns a trace into one page: offset medians, drift in cm per minute split at every
legitimate re-anchor (recentre, cutscene, character change), presses per action, gesture outcomes
and warnings. Read it after every run.
