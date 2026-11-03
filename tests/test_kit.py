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
flicker = load("eye_flicker", HARNESS)


class VoiceCaptureTests(unittest.TestCase):
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

    def test_trace_events_are_placed_by_the_header_start(self):
        # `t` is seconds from the run's start, so it only lines up through the header's wall clock.
        trace = [json.dumps(r) for r in (
            {"t": 0.0, "type": "header", "start": "2026-10-18T14:19:00.000+13:00", "hz": 30},
            {"t": 5.0, "type": "sample", "metrics": {"x": 1}},
            {"t": 9.25, "type": "event", "event": "parry", "detail": "rejected: too slow"},
            {"t": 115.0, "type": "event", "event": "focus_lost"},
        )]
        lines = inter.trace_lines(trace)
        self.assertEqual(lines[1], '2026-10-18T14:19:09.250+13:00 [trace t=9.250] parry {"detail": "rejected: too slow"}')
        self.assertEqual(len(lines), 3)  # samples are left out
        out = inter.interleave(inter.parse_notes(TRANSCRIPT), lines, context=15)
        first, second = out.split("## 14:21:00")
        self.assertIn("parry", first)
        self.assertIn("focus_lost", second)
        self.assertIsNone(inter.trace_lines(["14:19:09 plain log line"]))
        with self.assertRaisesRegex(ValueError, "wall-clock start"):
            inter.trace_lines([json.dumps({"t": 0.0, "type": "header"})])

    def test_cli_writes_utf8_on_a_legacy_console_and_fails_without_notes(self):
        import sys
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            transcript, log, empty = Path(tmp) / "t.md", Path(tmp) / "game.log", Path(tmp) / "empty.md"
            transcript.write_text(TRANSCRIPT.replace("Shadows", "Shadows → flicker"), encoding="utf-8")
            log.write_text("14:20:55 renderer: ≈ 3 ms\n", encoding="utf-8")
            empty.write_text("# nothing said\n", encoding="utf-8")
            raw = io.BytesIO()
            legacy = io.TextIOWrapper(raw, encoding="cp1252")  # what `> timeline.md` gets on Windows
            saved, sys.stdout = sys.stdout, legacy
            try:
                self.assertEqual(inter.main([str(transcript), str(log)]), 0)
                sys.stdout.flush()
            finally:
                sys.stdout = saved
            self.assertIn("→ flicker", raw.getvalue().decode("utf-8"))
            with contextlib.redirect_stderr(io.StringIO()) as err, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(inter.main([str(empty), str(log)]), 1)
            self.assertIn("No notes found", err.getvalue())


def scene(seed, shape=(240, 360)):
    # Smooth random "scene": low-res noise blown up and blurred a little.
    rng = np.random.default_rng(seed)
    coarse = rng.random((shape[0] // 12 + 2, shape[1] // 12 + 2))
    img = np.kron(coarse, np.ones((12, 12)))[: shape[0], : shape[1]]
    return (img + np.roll(img, 3, 0) + np.roll(img, 3, 1) + np.roll(img, (3, 3), (0, 1))) / 4


def depth_pair():
    """Two eyes of a scene with depth: the background at one disparity, a nearer block at another."""
    wide, near = scene(7, (240, 400)), scene(13, (240, 400))
    left, right = wide[:, 10:370].copy(), wide[:, 2:362].copy()  # background: left[x] == right[x + 8]
    left[80:200, 120:240] = near[80:200, 120:240]
    right[80:200, 134:254] = near[80:200, 120:240]  # nearer: left[x] == right[x + 14]
    return left, right


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
        left, right = depth_pair()
        results = frames.run_checks({"left": left, "right": right})
        self.assertTrue(all(ok for ok, _ in results), results)

    def test_one_disparity_across_the_frame_is_a_flat_picture(self):
        # A 2D panel (a waiting screen, a mono image at one depth) shifts as a whole: it correlates
        # well and lines up, so only the depth check catches it.
        wide = scene(7, (240, 400))
        results = verdict(frames.run_checks({"left": wide[:, 10:370], "right": wide[:, 2:362]}))
        self.assertTrue(results["stereo-correlation"] and results["stereo-shift"])
        self.assertFalse(results["depth"])

    def test_passing_checks_without_enough_evidence_are_inconclusive(self):
        left, right = depth_pair()
        two = {"left": left, "right": right}
        ok = frames.run_checks(two)
        self.assertEqual(frames.verdict(ok, two)[0], "INCONCLUSIVE")
        self.assertEqual(frames.verdict(ok, two, reject=[("waiting", scene(2))])[0], "PASS")
        self.assertEqual(frames.verdict(ok, two, ref=("golden", left))[0], "PASS")
        one = {"left": left}
        word, reason = frames.verdict(frames.run_checks(one, reject=[("waiting", scene(2))]), one,
                                      reject=[("waiting", scene(2))])
        self.assertEqual(word, "INCONCLUSIVE")
        self.assertIn("both eyes", reason)

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
            def save(name, gray):
                path = Path(tmp) / name
                Image.fromarray((gray * 255).astype(np.uint8)).save(path)
                return str(path)
            left, right = depth_pair()
            left, right, waiting = save("left.png", left), save("right.png", right), save("waiting.png", scene(2))
            flat = save("flat.png", np.zeros((900, 1600)))
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(frames.main([left, right, "--reject", waiting]), 0)
                self.assertFalse(Path(left).with_suffix(".preview.png").exists())
                self.assertEqual(frames.main([flat, "--max-side", "400"]), 1)
                self.assertEqual(frames.main([left, right]), 2)
                self.assertEqual(frames.main([left, "--reject", waiting]), 2)
                self.assertEqual(frames.main([str(Path(tmp) / "missing.png"), "--reject", waiting]), 2)
            lines = out.getvalue().splitlines()
            self.assertEqual([line.split(" (")[0].split(":")[0] for line in lines if line.startswith(("VERDICT", "ERROR"))],
                             ["VERDICT PASS", "VERDICT FAIL", "VERDICT INCONCLUSIVE", "VERDICT INCONCLUSIVE",
                              "ERROR FileNotFoundError"])
            self.assertTrue(Path(left).with_suffix(".preview.png").exists())
            with Image.open(Path(flat).with_suffix(".preview.png")) as preview:
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

    def test_mistyped_event_names_are_errors_not_empty_results(self):
        for kwargs in ({"around": "doge"}, {"event": "doge"}):
            with self.assertRaisesRegex(ValueError, "no event named 'doge'.*dodge, focus_lost"):
                tq.query(TRACE, **kwargs)
        self.assertEqual(tq.query(TRACE, type_="event", start=10.0), [])  # no match in a window is fine
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / "trace.jsonl"
            trace.write_text("\n".join(json.dumps(r) for r in TRACE), encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(tq.main([str(trace), "--around", "doge"]), 2)
                self.assertEqual(tq.main([str(Path(tmp) / "missing.jsonl"), "--count"]), 2)
                self.assertEqual(tq.main([str(trace), "--around", "dodge"]), 0)
            self.assertEqual([line.split(":")[0] for line in out.getvalue().splitlines()[:2]],
                             ["ERROR NoSuchEvent", "ERROR FileNotFoundError"])


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

    def test_a_run_that_cannot_be_judged_exits_2_not_1(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            scenario, metrics = Path(tmp) / "s.json", Path(tmp) / "m.json"
            scenario.write_text(json.dumps({"expect": [{"metric": "terminal", "equals": "completed"}]}), encoding="utf-8")
            metrics.write_text("{not json", encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(expect.main([str(scenario), str(metrics)]), 2)
                self.assertEqual(expect.main([str(scenario), str(Path(tmp) / "missing.json")]), 2)
                metrics.write_text(json.dumps({"terminal": "aborted"}), encoding="utf-8")
                self.assertEqual(expect.main([str(scenario), str(metrics)]), 1)
            lines = out.getvalue().splitlines()
            self.assertTrue(lines[0].startswith("ERROR JSONDecodeError") and lines[1].startswith("ERROR FileNotFoundError"), lines)


EYE_H, EYE_W = 88, 160


def game_frames(n, edit=None, repeat=2):
    """n game frames, each captured `repeat` times: a texture brightening smoothly."""
    x = np.arange(EYE_W, dtype=np.float32)
    frames = []
    for t in range(n):
        rgb = np.repeat(np.tile(40 + 0.4 * x + 0.5 * t, (EYE_H, 1))[..., None], 3, axis=2)
        if edit:
            edit(t, rgb)
        frames += [rgb] + [rgb.copy() for _ in range(repeat - 1)]
    return np.stack(frames)


def write_stream(prefix, left, right, start="20:05:10"):
    both = np.concatenate([left, right], axis=2).astype(np.uint8)
    both.tofile(f"{prefix}.rgb")
    Path(f"{prefix}.json").write_text(json.dumps({"width": 2 * EYE_W, "height": EYE_H, "eye_width": EYE_W, "downscale": 16, "format": "rgb24"}))
    t0 = flicker.clock_seconds(start)
    Path(f"{prefix}.times").write_text("".join(f"{i * 33.3:.1f} {flicker.clock_text(t0 + i * 0.0333)}\n" for i in range(len(both))))


def spark_and_one_eye_loss(t, rgb, shift):
    if t == 8:
        rgb[22:33, 40 + shift:60 + shift] += 60  # a spark both eyes see, a little shifted
    if t == 20 and shift:
        rgb[55:66, 100:120] -= 30  # a light the right eye alone loses for one frame


class EyeFlickerTests(unittest.TestCase):
    def test_repeated_capture_frames_count_once(self):
        self.assertEqual(len(flicker.unique_frames(flicker.luma(game_frames(30)))), 30)

    def test_blip_on_a_still_view_is_not_taken_for_a_repeat(self):
        still = game_frames(1, repeat=20)
        still[10, 0:11, 0:20] += 60  # one cell lights for one frame, nothing else moves
        gray = flicker.luma(still)
        keep = flicker.unique_frames(gray)
        self.assertEqual(list(keep), [0, 10, 11])
        up, down, _ = flicker.blips(gray[keep])
        self.assertEqual((int(up.sum()), int(down.sum())), (1, 0))

    def test_one_frame_light_on_and_off_are_blips_and_lasting_change_is_not(self):
        def edit(t, rgb):
            if t == 12:
                rgb[0:11, 0:20] += 60  # on for one game frame
            if t == 25:
                rgb[44:55, 100:120] -= 30  # off for one game frame
            if t >= 30:
                rgb[66:77, 0:20] += 60  # stays on
        gray = flicker.luma(game_frames(40, edit))
        up, down, _ = flicker.blips(gray[flicker.unique_frames(gray)])
        self.assertEqual((int(up.sum()), int(down.sum())), (1, 1))
        self.assertEqual((int(np.argmax(up)) + 1, int(np.argmax(down)) + 1), (12, 25))
        self.assertEqual(int(flicker.blips(flicker.luma(game_frames(40)))[0].sum()), 0)

    def test_one_eye_blips_leave_out_events_both_eyes_see(self):
        left = flicker.luma(game_frames(30, lambda t, rgb: spark_and_one_eye_loss(t, rgb, 0), repeat=1))
        right = flicker.luma(game_frames(30, lambda t, rgb: spark_and_one_eye_loss(t, rgb, 22), repeat=1))
        self.assertEqual(flicker.one_eye_blips(left, right), (0, 1, 28))
        self.assertEqual(flicker.one_eye_blips(left, left)[:2], (0, 0))
        # Counted per eye, the shared spark still shows in the left eye.
        self.assertEqual(int(flicker.blips(left)[0].sum()), 1)

    def test_same_pose_eyes_match_after_the_fixed_shift(self):
        wide = scene(11, (EYE_H, EYE_W + 40))[None] * 255
        left, right = wide[..., 30:30 + EYE_W], wide[..., 6:6 + EYE_W]  # right[x + 24] == left[x]
        dx, diff = flicker.aligned_difference(left, right)
        self.assertEqual(dx, 24)
        self.assertLess(diff, 0.01)
        self.assertGreater(float(np.median(np.abs(left - right))), 1.0)

    def test_marks_split_counts_by_condition(self):
        marks = flicker.read_marks(["20:05:10.400 fix off", "noise line", "[skip] 20:05:11 not at start",
                                    "20:05:10.800 fix on"])
        self.assertEqual([label for _, label in marks], ["fix off", "fix on"])
        left = game_frames(30, lambda t, rgb: spark_and_one_eye_loss(t, rgb, 0), repeat=1)
        right = game_frames(30, lambda t, rgb: spark_and_one_eye_loss(t, rgb, 22), repeat=1)
        times = flicker.clock_seconds("20:05:10") + np.arange(30) * 0.0333  # game frame 20 at 10.666
        lines, worst = flicker.summarise(left, right, times, marks, events=True)
        sections = "\n".join(lines).split("== ")
        self.assertEqual([s.splitlines()[0] for s in sections[1:]], ["before marks", "fix off", "fix on"])
        self.assertIn("right-only 1", sections[2])
        self.assertIn("20:05:10.666  right-only", sections[2])
        self.assertIn("right-only 0", sections[3])
        self.assertGreater(worst, 5)

    def test_stream_cli_gives_a_verdict_and_saves_event_frames(self):
        import tempfile
        left = game_frames(30, lambda t, rgb: spark_and_one_eye_loss(t, rgb, 0), repeat=1)
        right = game_frames(30, lambda t, rgb: spark_and_one_eye_loss(t, rgb, 22), repeat=1)
        with tempfile.TemporaryDirectory() as tmp:
            prefix = Path(tmp) / "run"
            write_stream(prefix, left, right)
            l, _, times, info = flicker.load_stream(f"{prefix}.rgb")
            self.assertEqual((l.shape, info["eye_width"]), ((30, EYE_H, EYE_W, 3), EYE_W))
            self.assertAlmostEqual(times[1] - times[0], 0.033, places=3)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(flicker.main([str(prefix), "--max-one-eye", "2"]), 1)
                self.assertEqual(flicker.main([str(prefix), "--from", "20:05:10.700", "--max-one-eye", "2"]), 0)
                try:
                    from PIL import Image
                except ImportError:
                    return
                flicker.main([str(prefix), "--save-events", str(Path(tmp) / "events")])
            self.assertIn("FAIL one-eye blips", out.getvalue())
            saved = list((Path(tmp) / "events").glob("*_right.png"))
            self.assertEqual(len(saved), 1)
            with Image.open(saved[0]) as strip:
                self.assertEqual(strip.size, (2 * EYE_W, 3 * EYE_H))

    def test_a_stream_that_cannot_be_measured_exits_2_not_1(self):
        import tempfile
        left = game_frames(10, repeat=1)
        with tempfile.TemporaryDirectory() as tmp:
            prefix = Path(tmp) / "run"
            write_stream(prefix, left, left)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(flicker.main([str(Path(tmp) / "missing"), "--max-one-eye", "1"]), 2)
                self.assertEqual(flicker.main([str(prefix), "--from", "21:00:00", "--max-one-eye", "1"]), 2)
            lines = out.getvalue().splitlines()
            self.assertTrue(lines[0].startswith("ERROR FileNotFoundError"), lines)
            self.assertTrue(lines[1].startswith("ERROR too few frames"), lines)


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


class RenderingReviewTests(unittest.TestCase):
    """Exercise the shipped acceptance contract; these are synthetic, not hardware results."""

    CONTRACT = HARNESS.parent / "references" / "rendering-review.json"

    def rules(self):
        return json.loads(self.CONTRACT.read_text(encoding="utf-8"))["expect"]

    def good(self):
        return {
            "stereo": {"image_verified": True, "output_mode": "stereo", "permanent_stops": 0,
                       "submitted_pairs": 10000},
            "temporal": {"history_failures": 0},
            "visibility": {"missing_visible_objects": 0},
            "required_metrics_missing": [],
            "timing": {"median_change_fraction": 0.02, "p95_change_fraction": 0.04},
        }

    def test_observed_stereo_passes_without_optional_vendor_telemetry(self):
        # An unavailable optional vendor utility does not prevent the baseline review.
        metrics = self.good()
        metrics["vendor_utility"] = None
        self.assertTrue(all(ok for ok, _ in expect.check(self.rules(), metrics)))

    def test_counters_cannot_hide_flat_output_or_rendering_faults(self):
        for group, field, value in (
            ("stereo", "image_verified", False),
            ("stereo", "output_mode", "flat"),
            ("stereo", "permanent_stops", 1),
            ("temporal", "history_failures", 1),
            ("visibility", "missing_visible_objects", 1),
        ):
            with self.subTest(group=group, field=field):
                metrics = self.good()
                metrics[group][field] = value
                self.assertTrue(any(not ok for ok, _ in expect.check(self.rules(), metrics)))

    def test_missing_required_evidence_cannot_pass_as_zero(self):
        for value in (["gpu_frame_ms"], None):
            metrics = self.good()
            metrics["required_metrics_missing"] = value
            self.assertTrue(any(not ok for ok, _ in expect.check(self.rules(), metrics)))
        metrics = self.good()
        metrics["timing"]["p95_change_fraction"] = None
        self.assertTrue(any(not ok for ok, _ in expect.check(self.rules(), metrics)))
        del metrics["timing"]
        self.assertTrue(any(not ok for ok, _ in expect.check(self.rules(), metrics)))

    def test_tail_regression_triggers_review_and_limits_are_configurable(self):
        metrics = self.good()
        metrics["timing"] = {"median_change_fraction": -0.1, "p95_change_fraction": 0.2}
        self.assertTrue(any(not ok for ok, _ in expect.check(self.rules(), metrics)))
        rules = self.rules()
        for rule in rules:
            if rule["metric"] == "timing.p95_change_fraction":
                rule["max"] = 0.25
        self.assertTrue(all(ok for ok, _ in expect.check(rules, metrics)))
        metrics["stereo"]["image_verified"] = False
        self.assertTrue(any(not ok for ok, _ in expect.check(rules, metrics)))


class KitStructureTests(unittest.TestCase):
    def kit_files(self, suffixes=(".md", ".py", ".txt", ".json", ".cpp")):
        # Everything a user copies: the README, templates, skills and checklists (not these tests).
        for path in ROOT.rglob("*"):
            rel = path.relative_to(ROOT).parts
            if path.is_file() and path.suffix in suffixes and rel[0] not in {".git", ".venv", "tests"}:
                yield path

    def test_every_skill_has_name_and_description(self):
        skills = sorted(ROOT.glob("skills/*/SKILL.md"))
        self.assertEqual(len(skills), 6)
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
        for template in ("AGENTS.md", "CLAUDE.md", "STATUS.md", "gitignore"):
            self.assertIn(f"templates/{template}", readme)
            self.assertTrue((ROOT / "templates" / template).is_file())

    def installed(self, into):
        """The user's repo after the README's setup steps 2-3."""
        import shutil
        for template in ("AGENTS.md", "CLAUDE.md", "STATUS.md"):
            shutil.copy(ROOT / "templates" / template, into / template)
        shutil.copy(ROOT / "templates" / "gitignore", into / ".gitignore")
        (into / "checklists").mkdir()
        shutil.copy(ROOT / "checklists" / "before-publishing.md", into / "checklists")
        for agent in (".agents", ".claude"):
            shutil.copytree(ROOT / "skills", into / agent / "skills")
        return into

    def links(self, path):
        return re.findall(r"\]\(([^)#:]+)(?:#[^)]*)?\)", path.read_text(encoding="utf-8"))

    def test_relative_links_resolve_in_the_kit_and_once_installed(self):
        import tempfile
        for path in self.kit_files((".md",)):
            for target in self.links(path):
                self.assertTrue((path.parent / target).exists(), f"{path.relative_to(ROOT)} -> {target}")
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.installed(Path(tmp))
            for path in repo.rglob("*.md"):
                for target in self.links(path):
                    self.assertTrue((path.parent / target).exists(), f"installed {path.relative_to(repo)} -> {target}")

    def test_gitignore_template_keeps_game_material_and_voice_out_but_not_the_mod(self):
        import shutil
        import subprocess
        import tempfile
        if not shutil.which("git"):
            self.skipTest("git not installed")
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.installed(Path(tmp))
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            ignored = ["sessions/session-1/audio.wav", "sessions/session-1/transcript.md", "game.dmp",
                       "re/project.gpr", "re/project.rep/data", "runs/r1/eyes.rgb", "trace.jsonl",
                       "left.preview.png", "build/mod.dll", ".venv/pyvenv.cfg"]
            kept = ["src/mod.cpp", "AGENTS.md", "STATUS.md", "tests/scenarios/dodge.json",
                    ".agents/skills/vr-mod-research/SKILL.md", "docs/CONTROLS.md"]
            result = subprocess.run(["git", "-C", str(repo), "check-ignore", "--no-index", *ignored, *kept],
                                    capture_output=True, text=True)
            self.assertEqual(sorted(result.stdout.split()), sorted(ignored))

    def test_commands_name_paths_that_exist_once_installed(self):
        # Agents run commands from the repo root, so a bare `scripts/...` path fails there.
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            repo = self.installed(Path(tmp))
            for path in self.kit_files((".md",)):
                text = path.read_text(encoding="utf-8")
                for target in re.findall(r"\.agents/skills/[\w./-]+\.(?:py|txt|md)", text):
                    self.assertTrue((repo / target).is_file(), f"{path.relative_to(ROOT)}: {target}")
                for line in re.findall(r"(?m)^\s*(?:python|cmake -S) +scripts/\S+", text):
                    self.fail(f"{path.relative_to(ROOT)}: runs from the skill folder, not the repo root: {line.strip()}")


if __name__ == "__main__":
    unittest.main()
