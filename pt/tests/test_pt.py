"""Unit tests for the pt CLI. Run: python3 -m unittest discover -s pt/tests"""
import importlib.machinery
import importlib.util
import json
import os
import tempfile
import unittest
from datetime import date
from pathlib import Path

BIN = Path(__file__).resolve().parents[1] / "bin" / "pt"
_loader = importlib.machinery.SourceFileLoader("ptcli", str(BIN))
_spec = importlib.util.spec_from_loader("ptcli", _loader)
pt = importlib.util.module_from_spec(_spec)
_loader.exec_module(pt)

PROGRAM = {"days": {
    "A": [{"ex": "Romanian Deadlift (Barbell)", "sets": 3, "reps": [6, 8], "main": True},
          {"ex": "Bench Press (Dumbbell)", "sets": 3, "reps": [6, 8], "main": True}],
    "B": [{"ex": "Bench Press (Barbell)", "sets": 3, "reps": [5, 7], "main": True},
          {"ex": "Lat Pulldown (Cable)", "sets": 3, "reps": [6, 8], "main": True},
          {"ex": "Lying Leg Curl (Machine)", "sets": 2, "reps": [10, 12]}]}}

CSV = """Date,Workout Name,Duration,Exercise Name,Set Order,Weight,Reps,Distance,Seconds,Notes,Workout Notes,RPE
2026-05-11 07:30:00,"Morning Workout",50m,"Bench Press (Barbell)",W,20.0,5.0,0,0.0,"",,
2026-05-11 07:30:00,"Morning Workout",50m,"Bench Press (Barbell)",1,45.0,8.0,0,0.0,"",,
2026-05-11 07:30:00,"Morning Workout",50m,"Bench Press (Barbell)",2,45.0,8.0,0,0.0,,,
2026-05-11 07:30:00,"Morning Workout",50m,"Plank",1,0,0,0,60.0,,,
2025-03-03 09:00:00,"Week 1",2,300h 1m,"Dead Bugs",1,0,10.0,0,0.0,"","",
"""


def sess(dt, ex, sets, **kw):
    return dict({"date": dt, "exercises": [{"name": ex, "sets": sets}]}, **kw)


def s_(w, r, **kw):
    return dict({"weight": w, "reps": r}, **kw)


class Env(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        os.environ["PT_DATA"] = str(self.dir / "pt")
        os.environ["PT_TODAY"] = "2026-10-20"
        (self.dir / "pt").mkdir()
        (self.dir / "pt" / "program.json").write_text(json.dumps(PROGRAM))

    def tearDown(self):
        self.tmp.cleanup()
        for k in ("PT_DATA", "PT_TODAY"):
            os.environ.pop(k, None)

    def write(self, *sessions):
        for s in sessions:
            pt.write_session(dict(s, source_kind="test", start=s["date"]))


class Parsing(unittest.TestCase):
    def test_weight_reps_and_rpe(self):
        sets, _ = pt.parse_sets("47.5x10,9 @8")
        self.assertEqual([(s["weight"], s["reps"], s["rpe"]) for s in sets], [(47.5, 10, 8.0), (47.5, 9, 8.0)])

    def test_unilateral_and_multiple_specs(self):
        sets, _ = pt.parse_sets("20x8/8 30x8/8")
        self.assertEqual([(s["weight"], s["reps"], s.get("each")) for s in sets], [(20, 8, True), (30, 8, True)])

    def test_sets_of(self):
        self.assertEqual(len(pt.parse_sets("60x8x3")[0]), 3)
        sets, _ = pt.parse_sets("30kg 2x12")
        self.assertEqual([(s["weight"], s["reps"]) for s in sets], [(30, 12), (30, 12)])

    def test_time_bodyweight_lb(self):
        self.assertEqual(pt.parse_sets("60s")[0][0]["seconds"], 60)
        self.assertEqual([s["seconds"] for s in pt.parse_sets("2x30s")[0]], [30, 30])
        self.assertEqual(pt.parse_sets("bw x8,6")[0][1], {"weight": 0.0, "reps": 6})
        self.assertAlmostEqual(pt.parse_sets("100lbx5")[0][0]["weight"], 45.4, places=1)

    def test_per_set_rpe(self):
        sets, _ = pt.parse_sets("60x8@7,8@9")
        self.assertEqual([s["rpe"] for s in sets], [7.0, 9.0])

    def test_bad_token(self):
        with self.assertRaises(ValueError):
            pt.parse_sets("3x")

    def test_lines(self):
        self.assertEqual(pt.parse_line("bench 47.5x10,9 @8")["ex"], "Bench Press (Barbell)")
        self.assertEqual(pt.parse_line("lunge 30x8/8")["ex"], "Reverse Lunge (Barbell)")
        self.assertEqual(pt.parse_line("plank 60s")["sets"][0]["seconds"], 60)
        self.assertEqual(pt.parse_line("swap leg curl"), {"cmd": "swap", "ex": "Lying Leg Curl (Machine)", "to": None})
        self.assertEqual(pt.parse_line("leg curl taken")["cmd"], "swap")
        self.assertEqual(pt.parse_line("swap bench -> db bench")["to"], "Bench Press (Dumbbell)")
        p = pt.parse_line("physio done pain 2")
        self.assertEqual((p["cmd"], p["done"], p["pain"]), ("physio", True, 2))
        self.assertFalse(pt.parse_line("physio skipped")["done"])
        self.assertEqual(pt.parse_line("bw 80"), {"cmd": "bw", "kg": 80})
        self.assertEqual(pt.parse_line("run 8km")["km"], 8.0)
        self.assertEqual(pt.parse_line("pain knee 4"), {"cmd": "pain", "site": "knee", "score": 4})
        self.assertEqual(pt.parse_line("skip")["cmd"], "skip")
        self.assertEqual(pt.parse_line("done")["cmd"], "done")
        self.assertEqual(pt.parse_line("45x8", current="Bench Press (Barbell)")["ex"], "Bench Press (Barbell)")

    def test_strong_names_resolve(self):
        for n in ["Bench Press (Barbell)", "Straight Arm Pull-Down ", "Pavloff Press", "Lat Pulldown - Underhand (Cable)"]:
            self.assertIn(pt.resolve(n), pt.CATALOGUE, n)

    def test_fmt_sets(self):
        self.assertEqual(pt.fmt_sets([s_(45, 10), s_(45, 10)]), "45x10,10")
        self.assertEqual(pt.fmt_sets([s_(20, 8, each=True), s_(30, 8, each=True)]), "20x8/8 30x8/8")


class Maths(unittest.TestCase):
    def test_epley_capped(self):
        self.assertAlmostEqual(pt.e1rm(45, 10), 60.0)
        self.assertAlmostEqual(pt.e1rm(45, 15), 60.0)  # capped at 10
        self.assertIsNone(pt.e1rm(0, 10))

    def test_working_drops_ramp(self):
        ws = pt.working([s_(20, 5), s_(45, 8), s_(45, 8), s_(40, 8, warmup=True)])
        self.assertEqual([s["weight"] for s in ws], [45, 45])

    def test_increments(self):
        self.assertEqual(pt.increment("Bench Press (Barbell)", 45), 2.5)
        self.assertEqual(pt.increment("Squat (Barbell)", 60), 5.0)
        self.assertEqual(pt.increment("Lying Leg Curl (Machine)", 30), 2.5)  # 5 kg would be >10%
        self.assertEqual(pt.increment("Bench Press (Dumbbell)", 16), 2.0)


class Progression(Env):
    P = {"sets": 3, "reps": [6, 8]}

    def rows(self, *sessions):
        return pt.history(sessions)["Bench Press (Barbell)"]

    def test_top_of_range_adds_load(self):
        rows = self.rows(sess("2026-10-13", "Bench Press (Barbell)", [s_(50, 8)] * 3))
        t = pt.next_target("Bench Press (Barbell)", rows, self.P, date(2026, 10, 20))
        self.assertEqual((t["weight"], t["reps"]), (52.5, 6))

    def test_in_range_adds_reps(self):
        rows = self.rows(sess("2026-10-13", "Bench Press (Barbell)", [s_(50, 7), s_(50, 6), s_(50, 6)]))
        t = pt.next_target("Bench Press (Barbell)", rows, self.P, date(2026, 10, 20))
        self.assertEqual((t["weight"], t["reps"]), (50, 7))

    def test_hard_rpe_blocks_jump(self):
        rows = self.rows(sess("2026-10-13", "Bench Press (Barbell)", [s_(50, 8, rpe=10)] * 3))
        t = pt.next_target("Bench Press (Barbell)", rows, self.P, date(2026, 10, 20))
        self.assertEqual(t["weight"], 50)

    def test_two_stalls_drop_ten_percent(self):
        ss = [sess(f"2026-10-0{i}", "Bench Press (Barbell)", [s_(50, 7)] * 3) for i in (1, 4, 8)]
        rows = self.rows(*ss)
        self.assertEqual(pt.stalls(rows, date(2026, 10, 10)), 2)
        t = pt.next_target("Bench Press (Barbell)", rows, self.P, date(2026, 10, 10))
        self.assertEqual(t["weight"], 45)
        self.assertIn("stalled", t["why"])

    def test_new_range_converts_by_e1rm(self):
        rows = self.rows(sess("2026-10-13", "Bench Press (Barbell)", [s_(45, 10)] * 2))
        t = pt.next_target("Bench Press (Barbell)", rows, {"sets": 3, "reps": [5, 7]}, date(2026, 10, 20))
        self.assertEqual(t["weight"], 47.5)  # 60 e1RM at 5 reps + 2 in reserve

    def test_break_takes_ten_percent(self):
        rows = self.rows(sess("2026-05-01", "Bench Press (Barbell)", [s_(50, 8)] * 3))
        t = pt.next_target("Bench Press (Barbell)", rows, self.P, date(2026, 10, 20))
        self.assertLess(t["weight"], 50)
        self.assertEqual(t["why"], "after a break")

    def test_deload_session_ignored_for_progression(self):
        rows = self.rows(sess("2026-10-10", "Bench Press (Barbell)", [s_(50, 7)] * 3),
                         sess("2026-10-13", "Bench Press (Barbell)", [s_(30, 6)] * 2, deload=True))
        t = pt.next_target("Bench Press (Barbell)", rows, self.P, date(2026, 10, 20))
        self.assertEqual(t["weight"], 50)

    def test_swap_carries_load(self):
        w = pt.carry("Bench Press (Barbell)", "Bench Press (Dumbbell)", 50, {})
        self.assertEqual(w, 18.0)  # factor 0.38 per hand, rounded down to 2 kg

    def test_deload_triggers(self):
        from datetime import timedelta
        self.write(*[sess((date(2026, 8, 1) + timedelta(days=4 * i)).isoformat(), "Bench Press (Barbell)",
                          [s_(50, 8)]) for i in range(15)])
        sessions = pt.load_sessions()
        why = pt.deload_reasons(sessions, pt.history(sessions), pt.tracking(), date(2026, 9, 27))
        self.assertTrue(any("weeks since" in w for w in why))
        trk = pt.tracking()
        trk["pain"].append({"date": "2026-09-26", "site": "knee", "score": 4})
        why = pt.deload_reasons(sessions, pt.history(sessions), trk, date(2026, 9, 27))
        self.assertTrue(any("pain 4/10" in w for w in why))

    def test_break_counts_as_deload(self):
        self.write(sess("2026-05-11", "Bench Press (Barbell)", [s_(45, 8)]),
                   sess("2026-10-20", "Bench Press (Barbell)", [s_(45, 10)]))
        self.assertEqual(pt.last_deload(pt.load_sessions(), date(2026, 10, 21)), date(2026, 10, 20))


class Flow(Env):
    def test_import_strong_and_summary(self):
        csvp = self.dir / "strong.csv"
        csvp.write_text(CSV)
        self.assertEqual(pt.import_strong(csvp), 2)
        s = json.loads((self.dir / "pt" / "logs" / "2025-03-03.json").read_text())
        self.assertEqual(s["name"], "Week 1, 2")
        self.assertEqual(s["exercises"][0]["name"], "Dead Bugs")
        s = json.loads((self.dir / "pt" / "logs" / "2026-05-11.json").read_text())
        self.assertTrue(s["exercises"][0]["sets"][0]["warmup"])
        self.assertEqual(s["exercises"][1]["sets"][0]["seconds"], 60)
        md = pt.summary().read_text()
        self.assertIn("generated by `pt summary`", md)
        self.assertIn("| Bench Press (Barbell) (main) | 45 |", md)
        self.assertIn("History peaks vs now", md)
        self.assertIn("unknown (send `bw 80`)", md)

    def test_plan_add_done(self):
        self.write(sess("2026-10-13", "Bench Press (Barbell)", [s_(45, 7)] * 3, day="A"))
        out = pt.plan()
        self.assertTrue(out.startswith("Day B"))
        self.assertIn("bench 47.5 x 5, 3 sets (last: 45x7,7,7", out)  # hit 7s: +2.5
        r = pt.add("bench 45x7,7,7")
        self.assertIn("Next: lat pulldown", r)
        self.assertIn("pain 2", pt.add("physio done pain 2"))
        self.assertIn("80", pt.add("bw 80"))
        self.assertIn("8 km", pt.add("run 8km"))
        self.assertIn("->", pt.add("swap leg curl"))
        dr = pt.load_draft()
        paths = pt.finish(dr, "test", png=False)
        s = json.loads(Path(paths[0]).read_text())
        self.assertEqual(s["day"], "B")
        md = (self.dir / "pt" / "progress.md").read_text()
        self.assertIn("Bodyweight: 80 kg", md)
        self.assertIn("| 0.69 |", md)  # bench e1RM 55.5 / 80

    def test_weekly_sets_and_flags(self):
        self.write(sess("2026-10-13", "Bench Press (Barbell)", [s_(45, 8)] * 3),
                   sess("2026-10-20", "Bench Press (Barbell)", [s_(45, 8)] * 6))
        ss = pt.load_sessions()
        this = pt.weekly_sets(ss, date(2026, 10, 19))
        last = pt.weekly_sets(ss, date(2026, 10, 12))
        self.assertEqual((this["chest"], this["triceps"]), (6, 3))
        flags = pt.load_flags(this, last)
        self.assertTrue(any(f.startswith("chest up 100%") for f in flags))
        self.assertTrue(any(f.startswith("chest only 3") for f in flags))

    def test_dashboard_renders(self):
        self.write(sess("2026-10-20", "Bench Press (Barbell)", [s_(45, 10)] * 2, name="Day B"))
        out = pt.dashboard(date(2026, 10, 20), self.dir / "d.png")
        from PIL import Image
        with Image.open(out) as im:
            self.assertEqual(im.size[0], 1080)
            self.assertGreater(im.size[1], im.size[0])


if __name__ == "__main__":
    unittest.main()
