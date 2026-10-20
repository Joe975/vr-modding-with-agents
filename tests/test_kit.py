import contextlib
import datetime as dt
import io
import importlib.util
import json
import re
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "vr-playtest-loop" / "scripts"
HARNESS = ROOT / "skills" / "vr-mod-test-harness" / "scripts"


def load(name, folder=SCRIPTS):
    spec = importlib.util.spec_from_file_location(name, folder / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


voice = load("voice_capture")
inter = load("interleave")
frames = load("frame_check", HARNESS)
tq = load("trace_query", HARNESS)
expect = load("check_expect", HARNESS)


class VoiceCaptureTests(unittest.TestCase):
    # Carried over from sm2-vr tests/test_voice_capture.py.
    def test_trigger_requires_whole_utterance(self):
        self.assertTrue(voice.is_trigger("Go ahead."))
        for text in ("Don't go ahead", "I'll go ahead and test the pistol", "go ahead now"):
            self.assertFalse(voice.is_trigger(text))
        self.assertFalse(voice.is_trigger("anything", ""))

    def test_device_never_falls_back_to_unrelated_microphone(self):
        devices = [{"name": "Valve output", "max_input_channels": 0},
                   {"name": "Desk mic", "max_input_channels": 1},
                   {"name": "Valve VR Radio & HMD Mic", "max_input_channels": 1}]
        self.assertEqual(voice.resolve_device(devices, "Valve")[0], 2)
        self.assertEqual(voice.resolve_device(devices, "1")[0], 1)
        with self.assertRaises(ValueError):
            voice.resolve_device(devices, "Missing")

    def test_pause_flush_preserves_capture_start_and_preroll(self):
        segmenter = voice.Segmenter(silence=0.09)
        quiet, speech = np.zeros(voice.BLOCK), np.ones(voice.BLOCK) * 0.1
        for i in range(8):
            self.assertIsNone(segmenter.feed(quiet, i))
        for i in range(5):
            self.assertIsNone(segmenter.feed(speech, 8 + i))
        self.assertIsNone(segmenter.feed(quiet, 13))
        self.assertIsNone(segmenter.feed(quiet, 14))
        stamp, audio = segmenter.feed(quiet, 15)
        self.assertEqual(stamp, 2)
        self.assertEqual(len(audio), 14 * voice.BLOCK)

    def test_continuous_commentary_is_bounded_without_silence(self):
        segmenter = voice.Segmenter(maximum=0.3)
        speech = np.ones(voice.BLOCK) * 0.1
        chunks = [part for i in range(30) if (part := segmenter.feed(speech, i))]
        self.assertEqual([stamp for stamp, _ in chunks], [0, 10, 20])

    def test_short_click_does_not_generate_a_transcript(self):
        segmenter = voice.Segmenter(silence=0.09)
        self.assertIsNone(segmenter.feed(np.ones(voice.BLOCK) * 0.1, 0))
        for i in range(1, 20):
            self.assertIsNone(segmenter.feed(np.zeros(voice.BLOCK), i))
        self.assertIsNone(segmenter.flush())


TRANSCRIPT = """# VR playtest feedback

Started: 2026-10-18T14:14:02+13:00

- [2026-10-18T14:19:11.310+13:00] It suddenly stopped taking my inputs.
- [2026-10-18T14:21:00.000+13:00] Shadows differ in each eye.
<!-- Closed: stop file -->
"""


class InterleaveTests(unittest.TestCase):
    def test_parses_only_note_lines(self):
        notes = inter.parse_notes(TRANSCRIPT)
        self.assertEqual([text for _, text in notes],
                         ["It suddenly stopped taking my inputs.", "Shadows differ in each eye."])
        self.assertEqual(notes[0][0].utcoffset(), dt.timedelta(hours=13))

    def test_window_uses_iso_and_bare_clock_lines(self):
        log = [
            "14:18:40.000 too early, outside the 15 s window",
            "2026-10-18T14:19:07.173+13:00 trace disarmed: game not foreground",
            "[14:19:09.5] input: native polls stalled",
            "no timestamp here",
            "14:19:20.000 after the window",
        ]
        out = inter.interleave(inter.parse_notes(TRANSCRIPT), log, context=15, after=3)
        first = out.split("## 14:21:00")[0]
        self.assertIn("trace disarmed", first)
        self.assertIn("native polls stalled", first)
        self.assertNotIn("too early", first)
        self.assertNotIn("after the window", first)
        self.assertNotIn("no timestamp", out)
        self.assertIn("(no log lines in this window)", out.split("## 14:21:00")[1])

    def test_utc_log_lines_line_up_with_local_notes(self):
        log = ["2026-10-18T01:19:05Z focus lost"]
        out = inter.interleave(inter.parse_notes(TRANSCRIPT), log, context=15)
        self.assertIn("focus lost", out.split("## 14:21:00")[0])


def scene(seed, shape=(240, 360)):
    # Smooth random "scene": low-res noise blown up and blurred a little.
    rng = np.random.default_rng(seed)
    coarse = rng.random((shape[0] // 12 + 2, shape[1] // 12 + 2))
    img = np.kron(coarse, np.ones((12, 12)))[: shape[0], : shape[1]]
    return (img + np.roll(img, 3, 0) + np.roll(img, 3, 1) + np.roll(img, (3, 3), (0, 1))) / 4


def verdict(results):
    return {line.split()[0] + ("-" + line.split()[1] if line.startswith("stereo") else ""): ok
            for ok, line in results}


class FrameCheckTests(unittest.TestCase):
    def test_flat_frame_fails_blank_and_textured_frame_passes(self):
        results = frames.run_checks({"left": np.zeros((100, 120))})
        self.assertFalse(results[0][0])
        self.assertTrue(frames.run_checks({"left": scene(1)})[0][0])

    def test_known_bad_screen_is_rejected_and_other_scenes_are_not(self):
        waiting = scene(2)
        noisy = np.clip(waiting + np.random.default_rng(0).normal(0, 0.02, waiting.shape), 0, 1)
        self.assertFalse(frames.run_checks({"left": noisy}, reject=[("waiting", waiting)])[1][0])
        self.assertTrue(frames.run_checks({"left": scene(3)}, reject=[("waiting", waiting)])[1][0])

    def test_golden_reference_survives_resolution_change_but_not_a_different_scene(self):
        golden = scene(4, (480, 720))
        capture = golden[::2, ::2]
        self.assertGreater(frames.similarity(capture, golden), 0.9)
        self.assertLess(frames.similarity(scene(5), golden), 0.6)

    def test_shift_sign_and_size(self):
        wide = scene(6, (240, 400))
        left, right = wide[:, 10:370], wide[:, 4:364]  # left[x] == right[x + 6]
        dx, dy = frames.shift(left, right)
        self.assertEqual((dx, dy), (-6, 0))

    def test_stereo_pair_with_disparity_passes(self):
        wide = scene(7, (240, 400))
        results = frames.run_checks({"left": wide[:, 10:370], "right": wide[:, 2:362]})
        self.assertTrue(all(ok for ok, _ in results), results)

    def test_stereo_catches_mono_copy_wrong_scene_and_vertical_offset(self):
        tall = scene(8, (300, 360))
        mono = verdict(frames.run_checks({"left": tall[:240], "right": tall[:240].copy()}))
        self.assertFalse(mono["stereo-eyes"])
        other = verdict(frames.run_checks({"left": tall[:240], "right": scene(9)}))
        self.assertFalse(other["stereo-correlation"])
        offset = verdict(frames.run_checks({"left": tall[:240], "right": tall[30:270]}))
        self.assertFalse(offset["stereo-shift"])

    def test_cli_writes_previews_only_on_failure(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow not installed")
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            good, flat = Path(tmp) / "good.png", Path(tmp) / "flat.png"
            Image.fromarray((scene(10) * 255).astype(np.uint8)).save(good)
            Image.fromarray(np.zeros((900, 1600), np.uint8)).save(flat)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(frames.main([str(good)]), 0)
                self.assertEqual(frames.main([str(flat), "--max-side", "400"]), 1)
            self.assertFalse(good.with_suffix(".preview.png").exists())
            with Image.open(flat.with_suffix(".preview.png")) as preview:
                self.assertEqual(max(preview.size), 400)


TRACE = sorted([
    {"t": 0.0, "type": "header", "hz": 30},
    *[{"t": i / 10, "type": "sample", "metrics": {"head_offset_metres": [0.1 * i, None, 0.0]}} for i in range(1, 50)],
    {"t": 2.05, "type": "event", "event": "dodge", "detail": "left"},
    {"t": 4.0, "type": "event", "event": "focus_lost"},
], key=lambda r: r["t"])


class TraceQueryTests(unittest.TestCase):
    def test_count_summarises_without_rows(self):
        out = tq.counts(TRACE)
        self.assertIn("52 records, 0.000-4.900 s", out)
        self.assertIn("49\tsample", out)
        self.assertIn("1\tevent dodge", out)

    def test_window_around_event_keeps_events_and_downsamples_samples(self):
        rows = tq.query(TRACE, around="dodge", width=0.5, every=2)
        self.assertEqual([r["t"] for r in rows], [1.6, 1.8, 2.0, 2.05, 2.2, 2.4])

    def test_fields_dotted_paths_nulls_and_limit(self):
        rows = tq.query(TRACE, type_="sample", start=1.0, end=1.3)
        out = tq.format_rows(rows, ["t", "metrics.head_offset_metres.0", "metrics.head_offset_metres.1"], limit=2)
        self.assertEqual(out.splitlines(), [
            "t\tmetrics.head_offset_metres.0\tmetrics.head_offset_metres.1",
            "1.000\t1.000\t-", "1.100\t1.100\t-", "... 2 more rows (narrow the window, raise --every or --limit)"])

    def test_events_default_to_their_own_keys(self):
        rows = tq.query(TRACE, type_="event")
        self.assertEqual(tq.format_rows(rows, tq.default_fields(rows), 10).splitlines()[0], "t\ttype\tevent\tdetail")


class CheckExpectTests(unittest.TestCase):
    METRICS = {"terminal": "completed", "root": {"right_metres": 0.62, "forward_metres": 0.11},
               "dodge_windows": [{"right_metres": 0.6}], "error": None}

    def test_min_max_equals_count_and_index(self):
        results = expect.check([
            {"metric": "root.right_metres", "min": 0.5},
            {"metric": "root.forward_metres", "max": 0.08, "why": "no forward drift"},
            {"metric": "terminal", "equals": "completed"},
            {"metric": "dodge_windows.#", "equals": 1},
            {"metric": "dodge_windows.0.right_metres", "min": 0.5, "max": 1.0},
        ], self.METRICS)
        self.assertEqual([ok for ok, _ in results], [True, False, True, True, True])
        self.assertEqual(results[1][1], "root.forward_metres = 0.110 (max 0.08)  [no forward drift]")

    def test_missing_metric_and_non_numbers_fail(self):
        results = expect.check([{"metric": "root.up_metres", "min": 0}, {"metric": "terminal", "min": 0}], self.METRICS)
        self.assertEqual([ok for ok, _ in results], [False, False])
        self.assertIn("= missing", results[0][1])
        with self.assertRaises(ValueError):
            expect.check([{"metric": "terminal"}], self.METRICS)


class ScenarioExampleTests(unittest.TestCase):
    """Exercise the shipped expectations with observed outcomes, not requested inputs."""

    EXAMPLES = HARNESS.parent / "references" / "scenarios"
    RUNS = {
        "melee": (
            {"combat": {"attacks": [{"target": "practice_target"}]}},
            {"combat": {"attacks": []}},
        ),
        "puzzle": (
            {"puzzle": {"lever_fraction": 1.0, "door_open": True}},
            {"puzzle": {"lever_fraction": 0.0, "door_open": False}},
        ),
        "vehicle": (
            {"vehicle": {"distance_metres": 2.0, "yaw_degrees": 15.0}},
            {"vehicle": {"distance_metres": 2.0, "yaw_degrees": 0.0}},
        ),
    }

    def examples(self):
        for name, outcomes in self.RUNS.items():
            with self.subTest(example=name):
                scenario = json.loads((self.EXAMPLES / f"{name}.json").read_text(encoding="utf-8"))
                yield scenario, outcomes

    def test_documented_expectations_accept_observed_results_and_reject_ignored_actions(self):
        for scenario, (good, ignored) in self.examples():
            common = {"terminal": "completed", "unintended_actions": []}
            # No head/hand/weapon bones, IK or virtual gamepad metrics are needed.
            passed = expect.check(scenario["expect"], common | good)
            self.assertTrue(all(ok for ok, _ in passed), passed)
            self.assertTrue(any(not ok for ok, _ in expect.check(scenario["expect"], common | ignored)))
            self.assertTrue(any(not ok for ok, _ in expect.check(scenario["expect"], common)))
            wrong_context = common | good | {"unintended_actions": ["menu_confirm"]}
            self.assertTrue(any(not ok for ok, _ in expect.check(scenario["expect"], wrong_context)))

    def test_examples_have_bounded_keyframes_and_finish_with_neutral_input(self):
        for scenario, _ in self.examples():
            frames = scenario["frames"]
            times = [frame["ms"] for frame in frames]
            self.assertEqual(times[0], 0)
            self.assertEqual(times, sorted(set(times)))
            self.assertEqual(times[-1], scenario["duration_ms"])
            self.assertEqual(frames[-1], {"ms": scenario["duration_ms"]})
            self.assertTrue(any(frame.get("buttons") or frame.get("axes") for frame in frames))


class KitStructureTests(unittest.TestCase):
    def kit_files(self, suffixes=(".md", ".py", ".txt", ".json")):
        # Everything a user copies: the README, templates, skills and checklists (not these tests).
        for path in ROOT.rglob("*"):
            rel = path.relative_to(ROOT).parts
            if path.is_file() and path.suffix in suffixes and rel[0] not in {".git", ".venv", "tests"}:
                yield path

    def test_every_skill_has_name_and_description(self):
        skills = sorted(ROOT.glob("skills/*/SKILL.md"))
        self.assertEqual(len(skills), 5)
        for path in skills:
            front = path.read_text(encoding="utf-8").split("---")[1]
            self.assertRegex(front, rf"(?m)^name: {path.parent.name}$", path)
            self.assertRegex(front, r"(?m)^description: .{40,}", path)

    def test_kit_is_game_agnostic(self):
        # Space Marine 2 belongs in the writeup, not the reusable kit.
        banned = re.compile(r"SM2|sm2|Space Marine|Saber|Warhammer|Emperor|chainsword|\bJoe\b", re.I)
        for path in self.kit_files():
            hit = banned.search(path.read_text(encoding="utf-8"))
            self.assertIsNone(hit, f"{path.relative_to(ROOT)}: {hit and hit.group(0)}")

    def test_repo_is_only_the_kit(self):
        # No writeup, site or personal working files at the top level.
        allowed = {".git", ".github", ".gitignore", ".venv", "README.md", "LICENSE", "AGENTS.md", "CLAUDE.md", "templates", "skills", "checklists", "tests"}
        self.assertEqual(sorted(p.name for p in ROOT.iterdir() if p.name not in allowed), [])

    def test_readme_has_the_agent_setup_section_and_prompt(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("## For agents: setting up the kit", readme)
        self.assertRegex(readme, r"(?m)^> Read https://github\.com/Joe975/vr-modding-with-agents ")
        for template in ("AGENTS.md", "CLAUDE.md", "STATUS.md"):
            self.assertIn(f"templates/{template}", readme)
            self.assertTrue((ROOT / "templates" / template).is_file())

    def test_relative_links_resolve(self):
        for path in self.kit_files((".md",)):
            for target in re.findall(r"\]\(([^)#:]+)(?:#[^)]*)?\)", path.read_text(encoding="utf-8")):
                self.assertTrue((path.parent / target).exists(), f"{path.relative_to(ROOT)} -> {target}")


if __name__ == "__main__":
    unittest.main()
