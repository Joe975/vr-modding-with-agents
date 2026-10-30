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
- **Post effects:** switch off motion blur, depth of field and anything that warps the finished
  image (lens distortion, barrel or panini projection). Depth of field blurs whatever the eyes
  converge on; a warp moves each eye's scene away from its projection, which puts the whole world
  at the wrong depth. Check that "off" really removes each one, then check the image matches the
  camera ([test harness](../../vr-mod-test-harness/SKILL.md#the-image-matches-the-camera)).
- **HUD panels:** status panels head-locked below the line of sight, readable with a glance down
  and clear of where the player aims. Starting defaults at 1.2 m: the main status strip about 19°
  below straight ahead, a second panel about 27° below; both live settings.
- **Crosshair where the weapon points:** a crosshair fixed to the player's face only marks the aim
  when the head steers the aim. Where the gameplay camera and the head can point different ways
  (gamepad aim, external or tabletop views):
  - First person: lock the game's HUD canvas to the gameplay camera rather than the head: a plane
    at a fixed distance in front of that camera, drawn into each eye with a per-eye projective map
    (a 3x3 homography from eye image coordinates to canvas coordinates). Exact on the camera's line.
  - External views: the eye is far from the gameplay camera, so a plane there has parallax and can
    be seen edge-on. A direction alone can't place the crosshair; the hit point can. Read the aim
    ray's hit point from the game's own targeting (it usually computes one every frame) and draw
    the game's own crosshair there, facing the eye at the angular size it has on the gameplay
    camera, so reload, heat and hit markers on it stay live. Leave that patch out of the
    head-locked canvas so it doesn't show twice.
  - Don't assume the crosshair is at the canvas centre: many third-person cameras look below the
    aim. Its canvas position is the hit point projected through the gameplay camera, while the
    game's own ray aims. Cut the patch wide enough for indicators beside the crosshair.
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
  the first-person heading, and return when the game gives control back.
- **Takeovers end when control returns, not when the camera does.** After a finisher, grapple or
  similar, the game hands movement back to the player before its camera glides back to the head,
  often by a second or two. Waiting for the camera leaves the player watching their character walk
  off before the view cuts onto it. Detect control back from the game's state if it exposes it, or
  from the character's root moving with the stick (e.g. 1.5 m/s or more within 30° of the stick's
  direction for 0.1 s), and keep the camera return as a fallback. Also check the stick's heading
  during a takeover: if it's read against the game's turned camera rather than the view, movement
  goes off in an unrelated direction.
- **Context changes:** walking, vehicles, menus and scripted sequences may need different input
  and camera policies. Release outgoing controls and prevent held inputs carrying into a new
  action. Test the transition as well as each mode in isolation.
