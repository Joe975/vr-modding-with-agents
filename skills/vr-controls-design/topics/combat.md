# Weapons and combat

- **Guns aim where the hand points.** Retarget the weapon to the wrist and drive the game's own aim
  ray from it, so hits are honest. Trigger fires; the off-hand trigger aims or alt-fires.
- **Two-handed weapons:** the off-hand grip steadies the weapon.
- **Melee swings are opt-in.** Detect from speed and travel over a short window (~200 ms). They
  misfire both ways: a swing detector can fire while the player is just using a gun, and a fast
  wrist with a twist can keep a blade tip still so a real swing doesn't count. Use the hand's
  motion as well as the tip's.
- **Block or parry as a guard pose:** off hand raised in front of the face or chest. A zone test,
  not motion detection, so it fires on the first sample (a swing detector's window is too slow for
  a timed parry). Hold to block, flick to parry, with a minimum press (~80 ms) so a flick reaches
  the game.
- **Tell a guard from a hand that's just there.** The off hand also sits in front when supporting a
  gun, so also require the controller pointing across or up (e.g. at least 50° from forward), and
  let aiming down sights cancel it.
- **Dodge stays on a button**, direction from the left stick. A lean gesture fights room-scale
  movement and comfort. Check dodges go the way the stick says relative to the view, with a test
  driver scenario per direction: the game's own dodge logic may assume a camera the mod replaced.
