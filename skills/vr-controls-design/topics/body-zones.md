# Body zones: holsters and belts

Most games have something to swap or grab. In VR, a zone on the body does it: squeeze the grip
with the hand in the zone to take whatever lives there.

| Zone | Common use |
|---|---|
| Over the shoulder | Primary or two-handed weapon |
| Hip | Sidearm |
| Belt or chest | Grenades, ammo, consumables |
| Mouth | Eat, drink, heal |
| Wrist | Map, inventory, objectives |

## Rules

- Zones are relative to the head's yaw, not the world, so they follow the player when they turn.
- Zones don't overlap. Cap a shoulder zone just above eye level, for example, so an overhead
  gesture can't select the weapon.
- A gesture fires once, then needs the hand lowered and the grip released to re-arm. A hand held
  in a zone when tracking or focus returns must re-arm first.
- Suppress other gestures nearby: turn off melee swings around a holster grab, or reaching for a
  weapon swings the melee weapon.
- Check what the button you send actually does in the game, in every context. A D-pad direction
  used for weapon select in one mode can be an emote or a squad command in another. Sometimes
  the accident is fun enough to keep as its own gesture; let the human decide.
- Zone sizes and positions are live settings, with a reset and save.
- Log every zone decision to the trace, including rejections.
