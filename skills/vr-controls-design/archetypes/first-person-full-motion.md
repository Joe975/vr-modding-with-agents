# Archetype: first-person full motion

The player has an embodied view: the head drives the camera and tracked hands control selected
interactions. Arm animation and physical object handling depend on the available hooks. This is
more integration work than a camera-only approach; choose it for the intended experience.

**Good for:** games where direct aiming, tools or object interaction benefit from tracked hands,
including third-person games with a workable first-person camera. Prove camera placement,
visibility and clipping rather than assuming a distance or FOV setting is enough.

**Build, in order:**

1. Head drives the view. Hide obstructing head geometry if there is a rendered player body.
2. Apply relevant [defaults](../topics/defaults.md): recentre, calibration and comfort, with
   locomotion only if this context needs it.
3. Prove one representative interaction from the action inventory, through to its game outcome:
   selecting an object, using a tool, aiming or attacking. Keep ordinary controls as a fallback.
4. Drive arms through the engine's IK if available and needed. Finger tracking is optional;
   neither is a prerequisite for tracked interaction in a game without a visible body.
5. If the game animates the body, stop its animations forcing the view to lean or shake.
6. Add the chosen [interaction patterns](../topics/interaction-patterns.md),
   [combat](../topics/combat.md), [body zones](../topics/body-zones.md) or
   [throwables](../topics/consumables-throwables.md) as applicable.
7. Test handedness and seated/standing reach for every selected interaction from the start.

**Watch out for:** gestures misfiring or fighting each other. Every gesture needs a trace event
for its decisions, near misses included, and a test driver scenario.
