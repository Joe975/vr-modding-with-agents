# Archetype: diorama

An external view of the game world, optionally scaled down like a tabletop miniature. Keep the
game's controls or choose tracked pointing/selection where useful; a gamepad is not required.

**Good for:** third-person games, strategy games and games where an overview is useful. Also a
possible first milestone when direct character embodiment isn't wanted.

**Comfort goal:** a stable view while characters or objects move within it. Choose an anchor and
explicit repositioning policy; automatically chasing a character can reintroduce the camera
motion this approach is intended to avoid. Verify comfort with the human.

**Build:**

- World scale as a setting (1/10 scale is a tabletop starting point, not a required scale).
  Changing scale must keep the eyes on the floor at the player's real eye height; scaling about
  the camera lifts them metres above the miniature. Grounded presets (life size, a tabletop
  scale, a giant scale) cycled on a button are easier to get right than a free grab.
- Stable anchor relative to a chosen area or subject; recentre puts the view back in front.
  Place the table only from a worn headset: an unworn one on a desk reads a head height well below
  standing or seated, and a table placed from it is seen from underneath. Wait for the runtime's
  user-presence signal or the first manual recentre before the first placement, and start any
  timed snapshots from then, not from launch.
- Optional automatic recentre: once the subject has walked a set distance from where the last
  recentre placed it, slide the world so the subject is back where a recentre puts it, keeping the
  table's height and heading. Don't turn it: a button recentre turns the table to face the
  player's current gaze, and doing that automatically swings the world every time the player
  glances aside, several times a minute. Heading changes only on the first placement and on a
  manual recentre. Measure from the subject's spot at the last
  recentre, not from the head (a recentre already leaves it some way off, so a head-based limit
  would fire at once). Count horizontal distance only, so a lift doesn't move the table, and use
  game-world distance, so scale doesn't change it. 1.5 m at 1/10 scale, with the subject placed about
  0.5 m ahead, is a starting point; make it a live setting with 0 for off, and let the human judge
  how often it moves. Run it at the same point in the frame as the button so it can't split an eye
  pair, and drop a waiting request on a view change, since a recentre landing in an embodied view
  can take a body-scale reading.
- Keep existing input unless tracked selection is chosen. For pointing, dragging or issuing
  commands, see [interaction patterns](../topics/interaction-patterns.md).
- **HUD:** ask early how the human wants health, prompts and menus shown; it's part of choosing
  this view. A copy of the whole flat screen floating in gameplay (picture in picture) is not a
  default: it reads as a bug and duplicates the world. Extract the HUD alone instead: retarget the
  game's HUD canvas or layer to a mod camera rendering into a transparent texture, and show it as
  a layer in front of and slightly below the table. Check that markers the game positions in
  screen space (target rings, name tags) still land on their subjects, or drop them from the
  layer. Menus and loading screens, where the world isn't shown, can use a large flat panel.
- Optional shoulder variant: a closer over-the-shoulder anchor, same rules.
- Cutscenes: hold the anchor steady or show them on a panel; see [defaults](../topics/defaults.md).
