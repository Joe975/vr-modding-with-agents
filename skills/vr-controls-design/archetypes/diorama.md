# Archetype: diorama

For third-person games: the world is scaled down like a tabletop miniature and viewed from a fixed
spot above and behind the character, while the game's own gamepad layout does everything.

**Good for:** third-person games, especially ones with big environments and crowds. Also a
low-risk first milestone.

**Why it's comfortable:** the view stays put while the character runs around in it. The player's
head moves the view a little but never drives the character or the game camera, so there's none
of the camera swing and chase that makes a straight [camera swap](camera-swap.md) sickening.

**Build:**

- World scale as a setting (start with the world at 1/10 scale).
- Fixed anchor above and behind the character; recentre on a button puts the diorama back in front.
- Game input untouched: locomotion, turning and aiming stay the game's own.
- Optional shoulder variant: a closer over-the-shoulder anchor, same rules.
- Cutscenes: hold the anchor steady or show them on a panel; see [defaults](../topics/defaults.md).
