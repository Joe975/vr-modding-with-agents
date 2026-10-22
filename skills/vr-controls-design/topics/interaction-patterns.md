# Objects, tools, puzzles and vehicles

Read the sections relevant to the game's action inventory. Physical motion is optional; retain
ordinary controls wherever hooks, precision, fatigue or accessibility make them the better fit.

## Selecting and operating objects

Separate selecting a target from activating it. Selection might use gaze, a hand ray, proximity
or the game's existing target lock. Activation might be a button, a held input or direct motion.
Verify the game's selected target and resulting state, not just the mod's highlight.

- **Lever or puzzle control:** with an interact hook, a hand gesture can request the existing
  interaction animation. Continuous hand-driven lever movement requires a transform or analog
  hook and compatible puzzle logic. State which version is supported; test completion and release.
- **Tool use:** identify aim, contact, activation and mode selection separately. A drill, scanner
  or repair tool may require sustained input, target validity or a resource. Check interruptions
  stop the action and that hand movement alone doesn't consume anything.
- **Inventory or strategy selection:** a hand ray can replace a cursor without grabbing world
  objects. Preserve hover, click, drag, cancel and scroll semantics where the UI needs them.
  Confirm the selected item/unit and command outcome, including accidental double activation.

## The game targets from its own camera

Use targets and interaction prompts are usually chosen by the game's gameplay camera: a cone or
cylinder along its heading, a focus cone around its crosshair, and a radius. If the mod anchors
the headset view to a stable reference and leaves that camera where it was (body following does
this), the game keeps targeting along a heading the player stopped looking at long ago. Every
press then fails, except by walking into the object. The prompt itself is often drawn on the
game's own HUD canvas, which the headset never shows, so the player can't tell a missing target
from a wrong button and reports "shove the hand in and hope".

- Find the game's selection rules in its data or scripts (viewer cones, radii, the input and its
  hold time) and record them in `CONTROLS.md`.
- Log the native camera's heading and the gaze relative to it. A checker that lists each use
  press with its misalignment turns the complaint into numbers.
- Fix by steering the native camera to follow the gaze through the game's own look input, with
  its response curve measured and inverted, a deadband and a re-engage band; or re-aim the
  game's target selection from the headset if a hook allows it. Check that movement, dodges and
  aim that compensate for native camera yaw still agree once it moves.
- Bring the prompt into the headset: crop the centre of the native HUD canvas onto a head-locked
  plane with the native camera's angular mapping. The focused prompt sits near the native
  crosshair, so it always lands in the crop.
- Judge the follow by gaze motion: a look is a gaze movement over a threshold, settling is
  measured after the gaze stops, and hunting only counts while the gaze is still.

## Vehicles and seated contexts

Choose a stable cockpit or external view independently of steering input. Retain gamepad,
keyboard or wheel controls where appropriate; virtual steering is an optional interaction.

- Identify steering, throttle, brake, reverse and context-specific actions. Keep analog values
  analog rather than turning them into repeated button taps unless the game requires that.
- Virtual steering needs a defined grip, centre, range and release behaviour. Measure the game's
  received steering and the vehicle response; a wheel mesh turning proves neither.
- On entering or leaving a vehicle, release the old context's actions before enabling the new
  ones. A held grip or trigger must not become an unrelated action in the new context; require
  release/re-arm where needed. Test entry, exit, pause, focus and tracking loss.
- Calibrate seated reach and camera placement separately from standing movement. Don't inherit
  head-relative walking, character-facing rules or body zones automatically.

## Shared interaction ownership

Conflicting consumers of the same input need explicit ownership. Record priority and cancellation
in `CONTROLS.md`: selection versus tool use, UI drag versus world grab,
or steering versus inventory. Trace rejected candidates and test that only the intended action
reaches the game. On interruption, send releases/neutral values through the active integration
route and re-arm before accepting a new gesture.
