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
- Optional automatic recentre: once the subject has walked a set distance from where the last
  recentre placed it, do exactly what the button does. Measure from the subject's spot at the last
  recentre, not from the head (a recentre already leaves it some way off, so a head-based limit
  would fire at once). Count horizontal distance only, so a lift doesn't move the table, and use
  game-world distance, so scale doesn't change it. 1.5 m at 1/10 scale, with the subject placed about
  0.5 m ahead, is a starting point; make it a live setting with 0 for off, and let the human judge
  how often it moves. Run it at the same point in the frame as the button so it can't split an eye
  pair, and drop a waiting request on a view change, since a recentre landing in an embodied view
  can take a body-scale reading.
- Keep existing input unless tracked selection is chosen. For pointing, dragging or issuing
  commands, see [interaction patterns](../topics/interaction-patterns.md).
- Optional shoulder variant: a closer over-the-shoulder anchor, same rules.
- Cutscenes: hold the anchor steady or show them on a panel; see [defaults](../topics/defaults.md).
