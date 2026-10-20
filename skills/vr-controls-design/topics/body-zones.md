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
- Check what the button you send actually does in the game, in every context. A D-pad direction
  used for weapon select in one mode can be an emote or a squad command in another. Sometimes
  the accident is fun enough to keep as its own gesture; let the human decide.
- Zone sizes and positions are live settings, with a reset and save.
- Log every zone decision to the trace, including rejections.
