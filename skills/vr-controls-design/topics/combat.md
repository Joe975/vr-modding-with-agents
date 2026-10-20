# Weapons and combat

Use only the patterns supported by this game's combat and the chosen input mode. Preserve its
attack timing, targeting and resource rules unless the human has chosen to change them.

## Ranged attacks and aiming

- Choose camera-directed, hand-directed or target-assisted aim based on the game's hooks and
  intended experience. For hand-directed aim, align the visible weapon and the game's actual
  aim ray; changing the mesh alone doesn't change hits. Test origin, direction and obstructions.
- Trigger-to-fire is a useful starting mapping, not a requirement. Check tap, held, charged and
  alternate actions separately; don't reserve the other trigger without checking its uses.
- If two-handed support is wanted, define what the second hand controls: orientation, stability
  or a game action. Don't assume the game already implements any of those effects.

## Melee

Distinguish two implementations before proposing physical swings:

- **Gesture requests an existing attack.** Send the game's attack action, preserving combos,
  charge/release semantics and animation timing. The game still decides reach, hits and damage;
  physical blade contact is not evidence of a hit.
- **Tracked weapon drives collision.** Requires hooks for weapon transforms and the game's hit
  rules. Check swept contact, repeated-hit suppression, reach and interaction with animations.
  Don't promise it from a camera or button hook alone.

Button melee remains useful in either mode. **Melee swings are opt-in.** Detect from speed and
travel over a short window (~200 ms as a tunable starting point). They misfire both ways: a swing
detector can fire while the player is just using a gun, and a fast wrist with a twist can keep a
blade tip still so a real swing doesn't count. Use the hand's
motion as well as the tip's. Test intentional swings and incidental movement while selecting
items, using tools or supporting a weapon.

## Defence

First identify held block, timed parry, directional guard, shield and evasion actions separately.
They need not share a binding, a hand or a recognizer.

- A guard pose is one option: use the shield hand, weapon hand or both hands as appropriate.
  An off hand raised before the chest only suits some games and loadouts.
- For a timed action, avoid waiting for a long motion window. An immediate pose-entry test or a
  button may fit better. For held block, sustain and release the action as the game expects.
- Measure the shortest press the game reliably reads; ~80 ms is an experiment starting point,
  not a universal parry duration. Check repeated entries and the game's cooldown/window rules.
- Distinguish guarding from other uses of the same space, such as supporting a weapon or using
  a tool. Orientation gates, context and explicit arming can help; tune them for each mapping.

## Evasion

If the game has dodge, dash or similar actions, a button is a conservative default. A lean
gesture can conflict with room-scale movement and comfort. Discover whether direction comes
from movement, facing, a selected target or the game itself. Test each supported direction and
view heading: the game's logic may assume a camera the mod replaced.
