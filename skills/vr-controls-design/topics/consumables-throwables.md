# Consumables and throwables

If these actions exist and physical use is chosen, select an item through a button, inventory or
[body zone](body-zones.md). A throw, mouth or application gesture can then request its game action.
Keep a button fallback. Don't assume selecting an item creates a physically simulated object.

- **Throw on release with speed.** Throw when the grip is released while the hand moves forward
  fast enough; 1.5 m/s is a reasonable starting threshold.
- **Separate intentional motion from locomotion.** Head-relative velocity is one starting point;
  test head turns, walking and vehicle motion so those don't count as throwing.
- **A slow release cancels or puts it back if supported**, without triggering another grip action.
- **Check how the game does it first.** Tap to throw or hold to aim? Does it fly along the camera
  or a separate target? Does releasing commit, and is there a cancel action? A put-back requires
  a reliable cancel or deferring activation until commitment; don't promise it otherwise. If the
  gesture sends a throw action, the game still owns aim and ballistics. Hand-driven trajectories
  require separate hooks; state which implementation is supported.
- **Decide who owns the grip.** If the same grip also blocks, the throw's follow-through must not
  turn into a block or another action: require release/re-arm before the next interaction.
