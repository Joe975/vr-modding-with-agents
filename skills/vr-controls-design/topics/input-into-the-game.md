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

## If using a virtual gamepad

- **Prove input with a log line before the headset**: "pad state read by game: stick 0.7". A pad
  the mod writes isn't proof the game read it.
- **Budget time.** Expect several attempts. Games load their gamepad API dynamically, only poll
  pads they enumerated themselves, restore hooked functions during startup, or have an overlay
  that already wrapped the function you hooked. Hooking the game's own input dispatch is often
  more reliable than the system API.
- **Survive focus loss and re-enumeration.** When the game loses focus it may drop and re-create its
  controller. Neutralise input while unfocused and re-adopt the game's new route on return.
