---
name: vr-mod-research
description: Research pass before writing any VR mod code for a flat-screen PC game. Use when starting a VR mod, when asked to "add VR to [game]", or before choosing a VR runtime (OpenXR/OpenVR) or stereo rendering approach. Searches for existing mods, same-engine VR frameworks and modding guides, then recommends a runtime and rendering approach with evidence in RESEARCH.md.
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
- **Anti-cheat.** If there is any, the mod is offline/single-player only. Never research, suggest
  or implement a bypass.

## 2. How the engine draws a frame

- Graphics API (D3D11, D3D12, Vulkan): decides the swapchain and texture-sharing code.
- Where the camera, the projection matrix and the frame boundary live. Ghidra headless and
  RenderDoc fill the gaps the web doesn't.
- Whether the engine already has a second camera or multi-view path (picture-in-picture, split
  screen, mirrors, scope rendering). This decides whether same-frame stereo is possible.

## 3. Recommend, with evidence

**Runtime.** OpenXR works with every headset. OpenVR is SteamVR only but gives Index skeletal
finger tracking and SteamVR Input with little work. Recommend for the human's headset and the
input they want, and put it behind a small backend interface either way. Don't pick OpenXR
expecting speed: the runtime's per-frame cost is usually well under a millisecond, while the
game rendering two eyes costs tens of milliseconds. Benchmark both if it matters.

**Stereo rendering.** Rank for this game specifically:

| Approach | Trade-off |
|---|---|
| Same-frame stereo | Both eyes from one head pose each frame. Best result; needs a multi-view or second-camera path |
| Alternate-eye | One eye per game frame, so one stereo pair per two frames. Easy, but fast objects shift between eyes and temporal effects can smear |

Don't default to alternate-eye because it's quicker to get running. If the game can do
same-frame, time spent on alternate-eye is mostly wasted. If same-frame looks possible, recommend
it and say what's needed.

## 4. Prove the hook cheaply

Before any headset work, the first experiment is on the flat screen: shift the camera by a known
amount and check the scene moves by the predicted fraction of the screen width. That one test
shows the camera hook is real before anything else is built on it.

## Output

Write `RESEARCH.md` with sources for every claim:

1. Existing mods and frameworks found, and whether to build on one.
2. How mods load, anti-cheat, and the graphics API.
3. Where the camera, projection and frame boundary live (or how you'll find them).
4. Runtime recommendation and stereo approach, ranked with evidence.
5. The first flat-screen experiment.

Then fill in what you learnt in `AGENTS.md`'s brackets, add a `STATUS.md` entry, and ask the human
which headset and input they care about if it's still unknown. Wait for them to agree the plan
before writing mod code.
