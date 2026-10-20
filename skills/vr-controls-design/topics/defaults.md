# Standard defaults

Apply the defaults relevant to the chosen camera, input and gameplay context, respecting existing
decisions. Tell the human what you set. They're live settings the human can change after trying
them; a cockpit, external view or cursor-driven game need not use character locomotion at all.

- **On-foot tracked controls:** smooth locomotion on the left stick, head-relative by default
  (controller-relative as an option), stick click to sprint if that action exists. Teleport as
  a comfort option only if the game allows it. If
  the engine can't cope with room-scale walking, turn it off explicitly rather than letting the
  camera and body drift apart.
- **Artificial turn, where needed:** snap turn on the right stick, 30° default, adjustable
  (e.g. 15-90°), once per push, rotating the rig around the head. Smooth turn as an option with
  adjustable speed. Decide separately what turns character facing; looking around need not
  steer a character, vehicle or external camera.
- **Recentre and calibrate:** one button recentres and levels to gravity. Head height, forward
  offset and, for tracked hands, per-hand wrist angle are live settings. Expect several tries,
  which is why they must be live.
- **Visible body in an embodied view:** hide obstructing head geometry; stop animations leaning
  the body into the view. Games without a visible body don't need skeletal hooks for this.
- **Handedness:** support dominant-hand choice and independent movement/turn bindings. Don't
  blindly swap asymmetric equipment or device roles; test each interaction's intended mapping.
- **Menus:** a panel in front of the player, centred and fully visible, is a useful start. Choose
  hand pointing, gaze or existing controls to suit the input mode. A panel can end up off to
  one side or too big to see all at once: check menus with an eye snapshot, not just a log line.
- **Cutscenes and scripted views:** detect when the game takes camera control (prefer its cinematic
  state over guessing from camera distance), keep the horizon level, and don't let head turns
  swing a camera that's far from the character. A scripted camera flying through the level is a
  fast way to make the player sick: consider freezing the view or showing cutscenes on a panel.
- **Context changes:** walking, vehicles, menus and scripted sequences may need different input
  and camera policies. Release outgoing controls and prevent held inputs carrying into a new
  action. Test the transition as well as each mode in isolation.
