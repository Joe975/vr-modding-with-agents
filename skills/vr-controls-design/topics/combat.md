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

## Where a weapon sits in the hand

If the mod drives a visible weapon from a tracked hand, it needs the weapon's fit relative to the
hand. That is often learned from an attachment socket on the skeleton, and from the socket readings
the mod may also infer what is held.

- **A socket only gives the fit while the weapon is on it.** With the weapon elsewhere, the same
  socket can sit in another item's grip, and a fit learned then stays wrong for the life of the
  character: the weapon and its aim ray are both off. Learn from the socket after the weapon has
  stayed on it unbroken for about 250 ms (the first frames are a blend). Until then use the carried
  weapon's pose relative to the hand. Once learned, keep it.
- **A socket reading isn't the loadout.** Melee stances and other animations can move a weapon
  between sockets, so "on the left socket" need not mean the sidearm is out. Tie a weapon change to
  the switch input plus the weapon leaving both sockets soon after (within 0.5 s, then off them for
  0.5 s), and let each press settle at most one change.
- **A respawn is not a new reading.** The first socket reading of a new character can be a melee
  carry or a spawn animation. Start from the primary weapon rather than trusting it.
- **Test the angle, not the label.** "Held in the right hand" can pass with the weapon tens of
  degrees off. Measure the fit error each time the weapon reaches its socket, across every
  recorded run.

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
- **If the human can't find the pose, draw it.** A small guide in both eyes, placed from the
  recognizer's own settings (zone centre, height, required angle), with a colour per detector
  state: not in the zone; in the zone but wrong orientation; right pose but blocked, and why;
  active. Draw it into the eye images so every runtime and snapshot shows it, never on the menu
  panel, and hide it when the action isn't available. Test that the drawn target satisfies the
  recognizer for the defaults and for random retunes, so a loosened rule moves the guide.

## Evasion

If the game has dodge, dash or similar actions, a button is a conservative default. A lean
gesture can conflict with room-scale movement and comfort. Discover whether direction comes
from movement, facing, a selected target or the game itself. Test each supported direction and
view heading: the game's logic may assume a camera the mod replaced. Hold the button down too: an
evasion button that also sprints when held can turn a mod-supplied direction into a run
([input](input-into-the-game.md#shared-requirements)).
