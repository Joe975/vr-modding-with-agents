---
name: vr-mod-research
description: Research pass before writing any VR mod code for a flat-screen PC game. Use when starting a VR mod, when asked to "add VR to [game]", or before choosing a runtime, stereo approach or interaction scope. Finds existing mods/frameworks and game capabilities, then records an evidence-based plan in RESEARCH.md.
---

# VR mod research

Don't write mod code during this pass. The output is `RESEARCH.md` with sources, and a
recommendation the human can argue with.

## 1. Search the web first

- **Existing VR mods of this game.** The easiest mod is one someone has already made. Check mod
  sites, Reddit, GitHub, Discord announcements.
- **VR mods for other games on the same engine**, and the framework they share. Starting from a
  proven core beats hand-rolling (e.g. REFramework-derived cores, UEVR for Unreal).
- **Modding guides and tools for the game and engine.** How mods load (a `dxgi.dll` proxy, an ASI
  loader, a mod manager), data paks, modders' test scenes or autostart flags, console commands.
- **Publisher support, anti-cheat and online play.** Find the publisher's current modding policy
  and any documented modding modes, launch options or anti-cheat requirements. Summarize what
  they say, with sources and dates, and flag unknowns. The user is responsible for checking what
  the publisher supports and permits, and choosing the project's scope. Don't infer an
  offline-only restriction simply because anti-cheat or online play exists; distinguish
  technical feasibility from publisher permission.

## 2. How the engine draws a frame

- Graphics API (D3D11, D3D12, Vulkan): decides the swapchain and texture-sharing code.
- Where the camera, the projection matrix and the frame boundary live. Ghidra headless and
  RenderDoc fill the gaps the web doesn't.
- Whether the engine already has a second camera or multi-view path (picture-in-picture, split
  screen, mirrors, scope rendering). This decides whether same-frame stereo is possible.

## 3. Discover gameplay and integration capabilities

- Inventory the game's actual contexts and actions from bindings, menus and modding APIs:
  character movement, combat, tools, puzzles, vehicles, selection/UI, or others present.
- Establish what a mod can control: camera, digital/analog input, aim/target, object transforms,
  skeleton/IK, collision and gameplay state. Separate confirmed hooks from untested possibilities.
- Record input semantics that matter: tap versus hold/release, analog ranges, timing, targeting
  and context-dependent bindings. Don't assume melee, a humanoid body or a virtual pad exists.
- Ask for the intended experience if unknown: camera support with existing controls, tracked
  interaction, external/tabletop view, seated cockpit, or a mixture. Choose camera and input
  independently; defer detailed mappings to `vr-controls-design`.

## 4. Recommend, with evidence

**Runtime.** Default to OpenXR: it works with every headset, so the mod reaches more players.
OpenVR is SteamVR only. Its one advantage is Index skeletal finger tracking and SteamVR Input
with little work, but OpenXR can get the fingers too, through `XR_EXT_hand_tracking` with the
controller data source, at the cost of more work. Recommend OpenVR only when the human's headset
or required input needs something OpenXR can't provide, and say what. Put the runtime behind a
small backend interface either way. The choice isn't about speed: the runtime's per-frame cost is
usually well under a millisecond, while the game rendering two eyes costs tens of milliseconds.

**Stereo rendering.** Rank for this game specifically:

| Approach | Trade-off |
|---|---|
| Same-frame stereo | Both eyes from one head pose each frame. Best result; needs a multi-view or second-camera path |
| Alternate-eye | One eye per game frame, so one stereo pair per two frames. Easy, but fast objects shift between eyes and temporal effects can smear |

Don't default to alternate-eye because it's quicker to get running. If the game can do
same-frame, time spent on alternate-eye is mostly wasted. If same-frame looks possible, recommend
it and say what's needed.

## 5. Prove the hook cheaply

Before any headset work, the first experiment is on the flat screen: shift the camera by a known
amount and check the scene moves by the predicted fraction of the screen width. That one test
shows the camera hook is real before anything else is built on it.

## Output

Write `RESEARCH.md` with sources for every claim:

1. Existing mods and frameworks found, and whether to build on one.
2. How mods load, the graphics API, and publisher guidance on modding, anti-cheat and online play:
   dated sources, unresolved questions and the user's chosen scope.
3. Where the camera, projection and frame boundary live (or how you'll find them).
4. Runtime recommendation and stereo approach, ranked with evidence.
5. Gameplay contexts, available integration/observation hooks, unknowns and feasible interaction
   scope. Include the evidence needed to distinguish a requested action from its game outcome.
6. The first flat-screen experiment.

Then fill in what you learnt in `AGENTS.md`'s brackets, add a `STATUS.md` entry, and ask the human
which headset and input they care about if it's still unknown. Wait for them to agree the plan
before writing mod code.
