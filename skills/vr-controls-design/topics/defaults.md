# Standard defaults

Apply these without asking; they're settings the human can change.

- **Move:** smooth locomotion on the left stick, head-relative by default (controller-relative as
  an option), stick click to sprint. Teleport as a comfort option only if the game allows it. If
  the engine can't cope with room-scale walking, turn it off explicitly rather than letting the
  camera and body drift apart.
- **Turn:** snap turn on the right stick, 30° default, adjustable (e.g. 15-90°), once per push,
  rotating the rig around the head. Smooth turn as an option with adjustable speed. The
  character's body follows head facing and snap turns.
- **Recentre and calibrate:** one button recentres and levels to gravity. Head height, forward
  offset and per-hand wrist angle are live settings. Expect several tries to get them right,
  which is why they must be live.
- **Body:** hide the character's head; stop animations leaning the body into the view.
- **Left-handed mode:** swaps everything. Plan it from the start.
- **Menus:** on a panel in front of the player, centred and fully visible, pointed at with the
  dominant hand. A panel can easily end up off to one side or too big to see all at once: check
  menus with an eye snapshot, not just a log line.
- **Cutscenes:** the game's camera takes over. Detect them (prefer the engine's own cinematic
  state over guessing from camera distance), keep the horizon level, and don't let head turns
  swing a camera that's far from the character. A scripted camera flying through the level is a
  fast way to make the player sick: consider freezing the view or showing cutscenes on a panel.
