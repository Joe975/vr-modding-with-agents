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
- **Player height, in an embodied view:** don't give every player the developer's eye height at
  the same scale, and don't lower the camera to a short player's real eye height either (the view
  ends up inside the character's body). Scale instead: multiply head-relative motion, eye
  separation and hand offsets by `reference_eye_height / player_eye_height`, so the floor sits
  where each player's body expects it and hands land in the same places on the character. Keep
  head placement offsets constant in game units, and scale body-zone offsets by the same factor.
  Measure standing eye height on recentre (standing space has the floor at 0); only a higher
  reading replaces the stored one, so a crouched recentre can't shrink the player, plus an
  explicit re-measure control. Clamp the factor (0.75-1.35 is a reasonable start). Leave
  speed-based gestures in physical units until a playtest says otherwise. Views that aren't
  embodied (diorama, external camera) keep a factor of 1.
- **Haptics:** a pulse confirms what the player can't see: a gesture or body-zone grab firing,
  a weapon firing, a hit taken or blocked. Bridge the game's own rumble output to the
  controllers where it has one, routed to the right hand, and add mod pulses for actions the mod
  invented. Expose intensity and an off switch as live settings. Check which haptic output the
  runtime binding exposes before planning on it.
- **Visible body in an embodied view:** hide obstructing head geometry; stop animations leaning
  the body into the view. Games without a visible body don't need skeletal hooks for this.
  Posture corrections fight game logic that reads the skeleton: squaring a torso the game turns
  toward its target can make its aim check fail, so a weapon fires once per burst. Bisect such
  regressions by switching each override off in turn, and stand the override down while the game
  needs its posture (ramp out on trigger press, back a couple of seconds after the last).
- **Handedness:** support dominant-hand choice and independent movement/turn bindings. Don't
  blindly swap asymmetric equipment or device roles; test each interaction's intended mapping.
- **Menus:** a panel in front of the player, centred and fully visible, is a useful start. Choose
  hand pointing, gaze or existing controls to suit the input mode. A panel can end up off to
  one side or too big to see all at once: check menus with an eye snapshot, not just a log line.
- **Cutscenes and scripted views:** detect when the game takes camera control (prefer its cinematic
  state over guessing from camera distance), keep the horizon level, and don't let head turns
  swing a camera that's far from the character. A scripted camera flying through the level is a
  fast way to make the player sick: consider freezing the view or showing cutscenes on a panel.
  When the game pulls its camera a few metres back for an animation (a get-up, a finisher, a
  ledge drop) and the view follows it, the player sees their body from outside with the hands
  floating. Stand the eyes beside the character at the learned standing eye height instead, keep
  the first-person heading, and return when the game's camera settles.
- **Context changes:** walking, vehicles, menus and scripted sequences may need different input
  and camera policies. Release outgoing controls and prevent held inputs carrying into a new
  action. Test the transition as well as each mode in isolation.
