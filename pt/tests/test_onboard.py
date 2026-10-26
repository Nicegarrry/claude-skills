"""Onboarding, program generator, Hevy import, data dir. Run: python3 -m unittest discover -s pt/tests"""
import contextlib
import importlib.machinery
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

BIN = Path(__file__).resolve().parents[1] / "bin" / "pt"
_loader = importlib.machinery.SourceFileLoader("pt_onboard", str(BIN))
_spec = importlib.util.spec_from_loader("pt_onboard", _loader)
pt = importlib.util.module_from_spec(_spec)
_loader.exec_module(pt)

HEVY = """"title","start_time","end_time","description","exercise_title","superset_id","exercise_notes","set_index","set_type","weight_kg","reps","distance_km","duration_seconds","rpe"
"Push","12 Oct 2026, 07:00","12 Oct 2026, 07:52","","Bench Press (Barbell)",,"",0,"warmup",20,10,,,
"Push","12 Oct 2026, 07:00","12 Oct 2026, 07:52","","Bench Press (Barbell)",,"",1,"normal",60,8,,,8
"Push","12 Oct 2026, 07:00","12 Oct 2026, 07:52","","Plank",,"",0,"normal",,,,45,
"""


def answers(**rt):
    a = json.loads(json.dumps(pt.TEMPLATE))
    a["about"].update(avoid=[], injuries=[], training_years=3)
    a["goals"]["primary"] = "strength"
    a["routine"].update(days_per_week=3, session_min=60, equipment="gym", split="auto", likes=[], other=[])
    a["routine"].update(rt)
    return a


class Env(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        os.environ["PT_DATA"] = str(self.dir / "pt")
        os.environ["PT_TODAY"] = "2026-10-20"

    def tearDown(self):
        self.tmp.cleanup()
        for k in ("PT_DATA", "PT_TODAY"):
            os.environ.pop(k, None)


class Generator(Env):
    def test_full_body_three_days(self):
        prog = pt.generate_program(answers(), hist={})
        self.assertEqual(list(prog["days"]), ["A", "B", "C"])
        self.assertEqual(prog["split"], "full_body")
        self.assertEqual(len(prog["days"]["A"]), 5)
        a0 = prog["days"]["A"][0]
        self.assertEqual((a0["ex"], a0["reps"], a0["main"]), ("Squat (Barbell)", [4, 6], True))
        names = [it["ex"] for items in prog["days"].values() for it in items]
        self.assertEqual(len(names), len(set(names)))  # no lift twice
        self.assertEqual(prog["settings"]["band"], [6, 14])

    def test_four_days_upper_lower_short_sessions(self):
        prog = pt.generate_program(answers(days_per_week=4, session_min=45), hist={})
        self.assertEqual(prog["split"], "upper_lower")
        self.assertEqual(len(prog["days"]), 4)
        self.assertTrue(all(len(v) == 4 for v in prog["days"].values()))

    def test_avoid_likes_and_kit(self):
        a = answers(equipment="dumbbells", likes=["db rdl"])
        a["about"]["avoid"] = ["bulgarian split squat"]
        prog = pt.generate_program(a, hist={})
        names = [it["ex"] for items in prog["days"].values() for it in items]
        self.assertIn("Romanian Deadlift (Dumbbell)", names)
        self.assertNotIn("Bulgarian Split Squat", names)
        self.assertTrue(all(pt.kit_ok(n, "dumbbells") for n in names))

    def test_home_is_bodyweight_only(self):
        prog = pt.generate_program(answers(equipment="home"), hist={})
        for items in prog["days"].values():
            for it in items:
                self.assertIn(pt.info(it["ex"])["kind"], ("bodyweight", "time"))
        patterns = {pt.info(it["ex"])["pattern"] for items in prog["days"].values() for it in items}
        self.assertTrue({"squat", "hinge", "single_leg", "horizontal_press", "vertical_press"} <= patterns)

    def test_history_beats_default(self):
        hist = {"Safety Bar Squat": [{"date": "2026-10-01"}] * 5}
        prog = pt.generate_program(answers(), hist=hist)
        self.assertEqual(prog["days"]["A"][0]["ex"], "Safety Bar Squat")

    def test_heavy_runner_setting(self):
        prog = pt.generate_program(answers(other=[{"type": "running", "km_per_week": 50}]), hist={})
        self.assertEqual(prog["settings"]["run_heavy_km_48h"], 15)


class Flow(Env):
    def run_cli(self, *argv):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            pt.main(list(argv))
        return buf.getvalue()

    def test_onboard_confirm_plan(self):
        with self.assertRaises(SystemExit) as e:
            self.run_cli("plan")
        self.assertIn("Onboard first", str(e.exception))
        p = self.dir / "answers.json"
        p.write_text(json.dumps(answers()))
        out = self.run_cli("onboard", str(p))
        self.assertIn("Day A", out)
        self.assertIn("--confirm", out)
        with self.assertRaises(SystemExit) as e:
            self.run_cli("plan")
        self.assertIn("not confirmed", str(e.exception))
        self.run_cli("onboard", "--confirm")
        self.assertTrue(pt.profile()["confirmed"])
        self.assertTrue(self.run_cli("plan").startswith("Day A"))

    def test_data_flag(self):
        other = self.dir / "elsewhere"
        os.environ.pop("PT_DATA")
        self.run_cli("--data", str(other), "onboard", "--template")
        self.assertEqual(pt.data_dir(), other)

    def test_default_data_dir(self):
        os.environ.pop("PT_DATA")
        self.assertEqual(pt.data_dir(), Path.home() / ".pt")

    def test_import_hevy(self):
        p = self.dir / "hevy.csv"
        p.write_text(HEVY)
        self.assertEqual(pt.import_hevy(p), 1)
        s = json.loads((self.dir / "pt" / "logs" / "2026-10-12.json").read_text())
        self.assertEqual((s["duration_min"], s["source_kind"]), (52, "hevy"))
        bench = s["exercises"][0]["sets"]
        self.assertTrue(bench[0]["warmup"])
        self.assertEqual((bench[1]["weight"], bench[1]["reps"], bench[1]["rpe"]), (60.0, 8, 8.0))
        self.assertEqual(s["exercises"][1]["sets"][0]["seconds"], 45)

    def test_onboarded_avoid_and_drills(self):
        a = answers()
        a["about"].update(avoid=["db bench"], rehab_drills=["Clamshell", "e.g. Cat Cow"])
        p = self.dir / "answers.json"
        p.write_text(json.dumps(a))
        self.run_cli("onboard", str(p))
        self.run_cli("onboard", "--confirm")
        self.assertNotIn("Bench Press (Dumbbell)", pt.swap_options("Bench Press (Barbell)", {}))
        out = self.run_cli("plan")
        self.assertIn("Warm-up: Clamshell\n", out)

    def test_avoid_blocks_swaps(self):
        (self.dir / "pt").mkdir()
        (self.dir / "pt" / "profile.json").write_text(json.dumps({"avoid": ["db bench"], "confirmed": True}))
        opts = pt.swap_options("Bench Press (Barbell)", {})
        self.assertNotIn("Bench Press (Dumbbell)", opts)


if __name__ == "__main__":
    unittest.main()
