# Archetype: camera swap

Replace the game's camera with a VR camera and change nothing else. Players keep a normal
controller (or the VR controllers mapped as one) and the game plays exactly as it did flat.

**Good for:** a first milestone for basic VR support in any game; proving the stereo and head
tracking work before touching input.

**Watch out for:** motion sickness. The game's camera still swings, shakes, chases the character
and gets driven by the right stick while the player's body stands still. For third-person games
the [diorama](diorama.md) avoids most of that.

**Build:**

- Head tracking adds to the game camera's orientation and position; stereo from the per-eye
  offsets and projections.
- Strip camera shake, head bob and motion blur where the game allows it. Check that "off" is
  really off: some games' lowest setting is still a mild blur preset.
- Keep the horizon level: don't pass the game's camera roll through.
- Recentre on a button.
- Menus and HUD on a panel in front of the player; see [defaults](../topics/defaults.md).
