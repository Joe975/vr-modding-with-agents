---
name: vr-controls-design
description: Design VR controls for an existing flat-screen game from its actions, contexts and available hooks. Use when choosing a camera and input approach, mapping controllers, adding tracked interaction or gestures, or adapting combat, tools, puzzles, vehicles and menus to VR.
---

# VR controls design

The agent can build and tune controls; the human decides what's fun. Propose, don't decide, for
anything that changes how the game feels in the hand.

## 1. Discover what this game and mod can support

Read the research and existing decisions. Record in `CONTROLS.md`:

- The game's activities and contexts: walking, combat, object interaction, driving, menus, or
  whatever it actually has. Don't add mechanics because another mod had them.
- Available hooks: camera only, digital/analog input, targeting, object transforms, arm IK,
  collision. Mark unknowns for experiments; tracked hands don't imply physical interaction.
- The human's input devices, seated/standing use, handedness and accessibility needs.

## 2. Choose camera and input separately

- [Camera swap](archetypes/camera-swap.md): VR camera with the game's existing input.
- [First-person full motion](archetypes/first-person-full-motion.md): embodied view with tracked
  interaction where the game supports it.
- [Diorama](archetypes/diorama.md): an external view, optionally as a tabletop miniature.

These are starting combinations, not an upgrade ladder. A first-person camera can retain normal
controls; tracked aiming can coexist with button melee. A vehicle may use a seated cockpit view
and gamepad steering. Record camera and input choices per context, including transitions.

## 3. Sort every action

1. List every action from the game's bindings, controls menu and supported interactions. Include
   context, current binding, tap/hold/release or analog semantics, timing, targeting, and the hook
   available to implement it. The same button can mean different actions in different contexts.
2. Suggest a home for each:
    - **Keep on a button** if it needs to be instant or frequent and has no physical equivalent:
      a timed defence, sprint, jump, the menu. Keep a button fallback for physical actions too.
    - **Move to the body** if there's an obvious physical action: operating a tool, pulling a
      lever, drawing an item, throwing or aiming. Check that the game
      can express the intended result and that the movement is comfortable and repeatable.
    - **Drop or merge** only what is proven redundant. An aim toggle may still affect accuracy,
      zoom or abilities even when the human physically sights along an object.
3. The human picks the body actions in the headset. Don't build gestures before they've chosen.
   Every threshold is a live setting; reproduce each misfire they report before fixing it.

Show the action table with proposed VR input, integration route, observed success condition and
reason. Get the human's choices before building gestures, respecting choices already made.

## 4. Build only the selected interactions

- [Objects, tools, puzzles and vehicles](topics/interaction-patterns.md): read for interaction or
  context changes beyond character combat.
- [Body zones: holsters and belts](topics/body-zones.md): read if body-mounted selection is chosen.
- [Consumables and throwables](topics/consumables-throwables.md): read if those actions exist.
- [Weapons and combat](topics/combat.md): read if the game has ranged attacks, melee or defence.

For each mapping, keep controller input or motion, intended game action, integration output and
observed game result distinct. A recognizer firing or a button being sent doesn't prove success.
Test expected activation, near misses, conflicting interactions and context/focus transitions.

## 5. Defaults and plumbing

- [Movement, turning, calibration, menus, cutscenes](topics/defaults.md)
- [Getting controller input into the game](topics/input-into-the-game.md)
