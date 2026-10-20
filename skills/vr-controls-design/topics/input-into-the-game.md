# Getting controller input into the game

Most games don't know about VR controllers. Every gesture ends up as a press on a virtual gamepad
the game already supports; hook the game directly only for what a pad can't express (aim
direction, arm poses).

- **Prove input with a log line before the headset**: "pad state read by game: stick 0.7". A pad
  the mod writes isn't proof the game read it.
- **Budget time.** Expect several attempts. Games load their gamepad API dynamically, only poll
  pads they enumerated themselves, restore hooked functions during startup, or have an overlay
  that already wrapped the function you hooked. Hooking the game's own input dispatch is often
  more reliable than the system API.
- **Survive focus loss and re-enumeration.** When the game loses focus it may drop and re-create its
  controller. Neutralise input while unfocused and re-adopt the game's new route on return.
- **Name actions by what they do** in config, logs and test scenarios, and check each binding in
  every context (gameplay, menus, hub), since one pad button can mean different things.
- **Keep a data pak or config preset** for the bindings the mod relies on, and verify it's the one
  loaded.
