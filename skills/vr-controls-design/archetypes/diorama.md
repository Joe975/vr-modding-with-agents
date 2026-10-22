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
- Keep existing input unless tracked selection is chosen. For pointing, dragging or issuing
  commands, see [interaction patterns](../topics/interaction-patterns.md).
- Optional shoulder variant: a closer over-the-shoulder anchor, same rules.
- Cutscenes: hold the anchor steady or show them on a panel; see [defaults](../topics/defaults.md).
