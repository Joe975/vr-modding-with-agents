# Archetype: first-person full motion

The player is the character: the head is the camera, tracked hands drive the arms and weapons,
and game actions become things you do with your body. The most work, and the most fun.

**Good for:** first-person games, and third-person games where a first-person camera can be forced
(a camera distance of 0 and a wider FOV, often through the game's own camera config or a data pak).

**Build, in order:**

1. Head is the camera; hide the character's head and helmet from your own view.
2. [Standard defaults](../topics/defaults.md): locomotion, snap turn, recentre, calibration.
3. Controllers drive the arms through the engine's own IK where it has one. Tracked fingers where
   the controller has them (e.g. Index skeletal curl).
4. Stop running and other animations leaning the body into the view: an opt-in upright-torso
   correction that removes the animation's lean.
5. [Weapons and combat](../topics/combat.md): guns aim from the wrist first, then the rest.
6. [Body zones](../topics/body-zones.md) and [throwables](../topics/consumables-throwables.md),
   chosen with the human.
7. Left-handed mode swaps everything. Plan it from the start.

**Watch out for:** gestures misfiring or fighting each other. Every gesture needs a trace event
for its decisions, near misses included, and a test driver scenario.
