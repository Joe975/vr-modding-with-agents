import datetime as dt
import importlib.util
import re
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "vr-playtest-loop" / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


voice = load("voice_capture")
inter = load("interleave")


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


class KitStructureTests(unittest.TestCase):
    def kit_files(self, suffixes=(".md", ".py", ".txt", ".json")):
        # Everything a user copies: the README, templates, skills and checklists (not these tests).
        for path in ROOT.rglob("*"):
            rel = path.relative_to(ROOT).parts
            if path.is_file() and path.suffix in suffixes and rel[0] not in {".git", ".venv", "tests"}:
                yield path

    def test_every_skill_has_name_and_description(self):
        skills = sorted(ROOT.glob("skills/*/SKILL.md"))
        self.assertEqual(len(skills), 4)
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
        allowed = {".git", ".gitignore", ".venv", "README.md", "templates", "skills", "checklists", "tests"}
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
