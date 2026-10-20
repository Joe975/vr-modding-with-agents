---
name: vr-controls-design
description: Design VR controls for a flat-screen game being modded to VR - pick a control archetype (camera swap, first-person full motion, diorama), sort the game's actions into buttons vs body gestures, and apply standard defaults for movement, turning, calibration, menus and cutscenes. Use when planning or changing a VR mod's controls, adding holsters, grenades, melee, parry or other gestures, or mapping VR controllers onto the game's input.
---

# VR controls design

The agent can build and tune controls; the human decides what's fun. Propose, don't decide, for
anything that changes how the game feels in the hand.

## 1. Pick an archetype with the human

- [Camera swap](archetypes/camera-swap.md): VR camera, normal controller, game otherwise unchanged.
- [First-person full motion](archetypes/first-person-full-motion.md): head is the camera, hands
  drive the arms and weapons.
- [Diorama](archetypes/diorama.md): third-person games as a tabletop miniature.

## 2. Sort every action

1. List every action the game has, from its input bindings or controls menu, with its binding.
2. Suggest a home for each:
    - **Keep on a button** if it needs to be instant or frequent and has no physical equivalent:
      dodge, sprint, jump, the menu.
    - **Move to the body** if there's an obvious physical action: drawing a weapon, throwing,
      healing, blocking, aiming.
    - **Drop or merge** what VR makes redundant, like free-look or an aim-down-sights toggle.
3. The human picks the body actions in the headset. Don't build gestures before they've chosen.
   Every threshold is a live setting; reproduce each misfire they report before fixing it.

> List every action in this game and how it's bound. Suggest which stay on buttons, which become
> body gestures and which VR makes redundant. Don't build any gestures yet; I'll pick.

## 3. Build the body actions

- [Body zones: holsters and belts](topics/body-zones.md)
- [Consumables and throwables](topics/consumables-throwables.md)
- [Weapons and combat](topics/combat.md)

## 4. Standard defaults and plumbing

- [Movement, turning, calibration, menus, cutscenes](topics/defaults.md)
- [Getting controller input into the game](topics/input-into-the-game.md)
