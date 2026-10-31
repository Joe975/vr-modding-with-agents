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
  when the head steers the aim. Where the gameplay camera, the head and the weapon can point
  different ways (gamepad aim, tracked aiming, external or tabletop views):
  - First person, gameplay camera aims: lock the game's HUD canvas to the gameplay camera rather
    than the head: a plane at a fixed distance in front of that camera, drawn into each eye with a
    per-eye projective map (a 3x3 homography from eye image coordinates to canvas coordinates).
    Exact on the camera's line.
  - That lock is for plain gameplay only. It assumes the gameplay camera stays near the gaze, which
    holds only while the mod steers it. In hubs, menus, photo modes, cutscenes and unknown states,
    keep the canvas head-locked, or a pop-up drawn on it can end up beside or behind the player.
    Keep the rule in one place and log which way it went.
  - External views and tracked aiming: the eye is far from the gameplay camera (a plane there has
    parallax and can be seen edge-on), or the weapon isn't aimed by that camera. A direction alone
    can't place the crosshair; the hit point can. Read the aim ray's hit point from the game's own
    targeting (it usually computes one every frame) and draw the game's own crosshair there,
    facing the eye at the angular size it has on the gameplay camera, so reload, heat and hit
    markers on it stay live. Leave that patch out of the canvas so it doesn't show twice. In first
    person, apply the plain-gameplay rule above to this patch too.
  - Handle the ray's gaps. A hit point behind the eye (a weapon lowered past the player) draws
    nothing; falling back to the canvas snaps the crosshair to the face. If the mod steers the ray,
    a lone frame the hook misses reports the game's own aim, so let a steered hit stand for about
    100 ms over newer unsteered ones. Some games report a point at fixed range for open sky, so a
    hit point can always exist.
  - Don't assume the crosshair is at the canvas centre: many cameras look below the aim, first-person
    ones included. Its canvas position is the hit point projected through the gameplay camera while
    the game's own ray aims. Take the median over ordinary play, because rays during animations can
    be well off. Once a controller steers the ray there is nothing left to measure, so keep that
    position as a setting. Cut the patch wide enough for indicators beside the crosshair; anything
    else crossing the patch moves with it.
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
  Scaling a head bone to nearly nothing leaves a tiny head where neck-weighted vertices blend, so
  hide the mesh parts as well if the engine lets you. The player's real character can be built
  differently from a test character (outfit templates holding every variant, other part names):
  select parts by pattern, check the pattern offline against every player template, and confirm on
  a normal launch that parts were actually hidden.
- **Handedness:** support dominant-hand choice and independent movement/turn bindings. Don't
  blindly swap asymmetric equipment or device roles; test each interaction's intended mapping.
- **Menus:** a panel in front of the player, centred and fully visible, is a useful start. Choose
  hand pointing, gaze or existing controls to suit the input mode. A panel can end up off to
  one side or too big to see all at once: check menus with an eye snapshot, not just a log line.
  The button that opens a menu should close it. Gameplay habits land as menu navigation (triggers
  change tabs, the stick moves a cursor), so an accidental pause gets reported as a stuck game.
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
- **Takeovers also end when the animation has settled.** With no stick push the game's camera can
  stay out for a long time, and the view waits on a character that has already stopped. Hand back
  once the character has moved and then stayed still: root, head and both hands all under about
  0.35 m/s for about 0.3 s. The root alone isn't enough, because it can stop while the arms work
  through the rest of the animation for seconds. Requiring movement first keeps a takeover that
  hasn't started from ending, and a new animation moving the character should hold again.
- **Not every camera excursion is a takeover.** Camera distance alone can't separate a lunging
  combo strike from a real takeover: the game's camera trails the lunge past the limit, the view
  holds, and the character ends up metres away from the player. If the game's animation state
  can't be read live, input history may separate them. After an unbroken chain of attacks (three,
  each within about 1.5 s, no parry or finisher input since), widen the limit (2.5 m against a 1 m
  limit) until the camera is back, and let the view ride with the character. Count the rule over
  every recorded takeover before trusting it, and ask the human about comfort, because the view
  now travels with the lunge.
- **Free-camera viewer:** where the game has a pause or photo mode, the mod can fly the eyes around
  the frozen scene. A button can also let the game run under that free camera with a neutral pad,
  so an animation plays out with sound. End it with the settle rule above, a short limit if nothing
  moves (3 s) and a cap (10 s). A play that runs its course goes back to the game rather than
  freezing; only the player's own press freezes it. Controls still held at the end wait for their
  release.
- **Context changes:** walking, vehicles, menus and scripted sequences may need different input
  and camera policies. Release outgoing controls and prevent held inputs carrying into a new
  action. Test the transition as well as each mode in isolation. A respawn or level change can
  give the player a new character object: decide what carries over (held item, hand, calibration)
  rather than letting it reset by accident, and test it.
