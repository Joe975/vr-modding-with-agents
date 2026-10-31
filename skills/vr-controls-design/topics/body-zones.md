# Body zones: holsters and belts

If the game has items or actions that suit body-mounted selection and the human wants it, a zone
on the body can select them: squeeze the grip in the zone to request its mapped action. This
doesn't imply the game supports a physically held object. Use menus or buttons where preferable.

| Zone | Common use |
|---|---|
| Over the shoulder | Primary or two-handed weapon |
| Hip | Sidearm |
| Belt or chest | Grenades, ammo, consumables |
| Mouth | Eat, drink, heal |
| Wrist | Map, inventory, objectives |

## Rules

- Choose an anchor that suits the context. Head-yaw-relative zones are a standing starting
  point; check looking aside, seated reach and vehicle entry so zones don't move unexpectedly.
- Zones don't overlap. Cap a shoulder zone just above eye level, for example, so an overhead
  gesture can't select the weapon.
- A selection fires once, then needs zone exit and grip release to re-arm. A hand held
  in a zone when tracking or focus returns must re-arm first.
- Give the selection ownership of its input until completion/cancellation. Suppress conflicting
  actions, such as a melee swing, tool activation or UI drag, during a zone grab.
- Suppressing a gesture means pausing it, not resetting it. Where a reset latches the gesture
  (must leave the pose before it can fire again), a zone the hand rests in at idle, such as a belt
  zone for a relaxed hand, keeps every neighbouring gesture latched, and a fast move out of the zone
  straight into the pose never fires. Test the move from each resting zone into each gesture.
- Force-sensing grips (Valve Index controllers, for example) read thumb presses. Pressing a face
  button can squeeze the grip past the selection threshold, so a hand resting in a zone selects
  something on every unlucky button press. Measure it per hand. Consume a squeeze that starts while
  a thumb control on that hand is down: it selects nothing until it's released.
- If the game has one "next weapon" input, one zone that always sends it can replace a zone per
  weapon, and it still works while the held item is unknown. Let the human choose.
- Check what the button you send actually does in the game, in every context. A D-pad direction
  used for weapon select in one mode can be an emote or a squad command in another. Sometimes
  the accident is fun enough to keep as its own gesture; let the human decide.
- Zone sizes and positions are live settings, with a reset and save.
- Log every zone decision to the trace, including rejections.
