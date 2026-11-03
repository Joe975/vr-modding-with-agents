# Before publishing a VR mod

Share the method always. Before publishing the mod itself (packaging and the public-repo cleanup:
the `vr-mod-release` skill, in `.agents/skills/` or `.claude/skills/`):

- [ ] **EULA.** Most restrict reverse engineering; what that means depends on where you live. Read it.
- [ ] **Publisher's modding policy.** The user has checked the publisher's current guidance on
      what it supports and permits, including AI-assisted materials where relevant. Record
      sources, dates and unresolved questions; the user decides whether to seek clarification.
- [ ] **Anti-cheat and online play.** The user has checked publisher guidance for the intended
      modes, including any documented modding modes, launch options and anti-cheat requirements.
      Describe the mod's tested scope and relevant requirements clearly. Don't assume that
      anti-cheat means offline-only, or that a working mod is approved for online play.
- [ ] **Redistribution.** Your own code only. No game files, repacked game data or extracted assets.
      Data paks built from the game's own files are a grey area: build them on the player's
      machine from their own copy rather than shipping them.
- [ ] **No game code in the repo or the DLL.** Decompiler output, disassembly listings, crash
      dumps and game data used as test fixtures are the game's. So are byte patterns copied from
      its code into prologue checks and build tables: replace them with digests and keep a test
      that fails on new byte runs. The private history still holds all of it, so publish a fresh
      repo with one squashed commit. Scan the tree for local paths, usernames and secrets first.
- [ ] **Branding.** No logos, nothing that looks official. "Unofficial, non-commercial, not
      affiliated" at the top of the README.
- [ ] **Footage and images.** Check the publisher's video/content guidelines (often an EULA
      appendix: non-commercial, link the official site, no implied endorsement) and the IP
      owner's fan content policy. Some IP owners ban AI-generated fan art of their characters
      outright, including feeding their imagery into an image generator.
- [ ] **Licences** of the VR framework cores you built on, with attribution, and a third-party
      notices file in the package for everything bundled (runtime loaders, an embedded interpreter).
- [ ] **Issues on.** Open the repo with issues enabled so players can report problems and send fixes.
- [ ] **Rendering compatibility.** Capability minimums and real GPU/AA/runtime evidence are
      recorded separately; vendor middleware is optional for the baseline. Unsupported modes
      have a visible fallback and recovery. Both-eye images verify stereo; untested hardware and
      comfort gaps are explicit. See the release skill's rendering gates.
- [ ] **Workarounds and performance.** Every broad workaround has a correctness reason, scope,
      A/B control, representative scene costs and revisit criterion. Repeated matched runs cover
      real gameplay, timing tails, fresh stereo delivery and pose age. Resolve regressions or
      record the release decision and limitation; don't infer mission performance from a tiny room.
- [ ] **Shipped defaults.** The hashed player package's effective profile matches the evidence,
      including active workarounds and diagnostics off. Normal launch, settings changes and
      recovery pass; unresolved gaps are listed rather than counted as success.

**This is not legal advice.**
