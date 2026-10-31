# Getting controller input into the game

Choose the smallest reliable integration route for each action: existing keyboard/mouse input,
virtual gamepad, engine action dispatch, a framework API or a direct hook. A gesture may request
a digital action, drive an analog value or update a pose/target; it need not become a pad press.
Prefer an existing mod framework's supported route when it fits.

Keep input or motion -> intended game action -> integration output -> observed result distinct
in config, traces and tests. Confirm the game consumed the input and performed the action.

## Shared requirements

- Preserve tap/hold/release, repeat, analog range and targeting semantics. Check both activation
  and release; interrupted gestures must not leave a held action or nonzero axis behind.
- Name actions by what they do in each context, not by physical binding. Check gameplay, menus,
  vehicles and any other modes the game has; one key or button can do different things.
- Keep relied-on bindings/config in a versioned preset where possible and verify what's loaded.
- Neutralise output on focus/tracking loss and adopt the new input route if the game recreates
  it. Require release/re-arm before a held controller input becomes a new context's action.
- **Check what a game button does when held.** Many mean one thing tapped and another held (dodge,
  then sprint), and anything the mod adds to the press, such as a synthesised stick direction, stays
  on for the whole hold. If the held meaning isn't wanted, let go of the native button at a cap just
  under the game's switch point, even with the physical button still down. Measure that point from
  traces, and apply the cap only in the context that needs it: menus keep plain held buttons. The
  reverse also bites: a gesture that sends a short press can't reach an action behind a hold
  threshold, so hold the native button past it.
- **Measure before adding a minimum press time.** A threshold meant to reject brushes can eat real
  taps, and the player just presses again, longer, and reports it as flaky. Thumb taps on a
  controller are often only 100-150 ms, so read press lengths from traces first; 70 ms is a safer
  start than 150 ms. A press that also catches a neighbouring button is a better signal for an
  accident: one thumb can land on both.

## On-screen prompts

The game's prompts name native buttons. Once the mod maps controls differently, a prompt can name
the wrong button or one the controller doesn't have. A working control then goes unfound: the
player tries everything with that letter and decides the action is broken. Audit prompts against
the mapping early, ranked by how often each shows and how badly it misleads, and list them in
`CONTROLS.md`.

- **Keep same-lettered buttons aligned where you can.** If a controller has the same letter as the
  pad, sending that native button in every context keeps each prompt true with no edit. A crossed
  letter makes every prompt that uses it wrong.
- **Change prompts through the game's data before drawing over them.** A draw-over doesn't know when
  a prompt is up, what it says or where it sits at another HUD scale. Prompts are often data: a site
  names an input action, the action names a key, and one table picks the glyph. Follow that chain in
  the game's files, then make the narrowest change that works: text at one site, one site pointed at
  a display-only action bound to the glyph you want, or the binding itself moved, which fixes every
  site at once.
- **A glyph table row is global.** Changing it changes that button everywhere, and one native button
  can mean different physical controls in gameplay and menus. A data pack usually can't vary per
  headset either, so prefer glyphs that are true on every supported controller.
- **Check each change on screen.** Literal text in a field that normally holds a localisation key
  may come up blank, and a bad edit to binding files can stop the game at startup. Check that a
  saved player profile doesn't override your bindings, and that the prompt clears when it should.

## If using a virtual gamepad

- **Prove input with a log line before the headset**: "pad state read by game: stick 0.7". A pad
  the mod writes isn't proof the game read it.
- **Budget time.** Expect several attempts. Games load their gamepad API dynamically, only poll
  pads they enumerated themselves, restore hooked functions during startup, or have an overlay
  that already wrapped the function you hooked. Hooking the game's own input dispatch is often
  more reliable than the system API.
- **Survive focus loss and re-enumeration.** When the game loses focus it may drop and re-create its
  controller. Neutralise input while unfocused and re-adopt the game's new route on return.
