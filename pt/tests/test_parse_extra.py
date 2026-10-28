import importlib.machinery, importlib.util, pathlib, unittest

_p = pathlib.Path(__file__).resolve().parents[1] / "bin" / "pt"
_l = importlib.machinery.SourceFileLoader("pt_extra", str(_p))
_s = importlib.util.spec_from_loader("pt_extra", _l)
pt = importlib.util.module_from_spec(_s)
_l.exec_module(pt)


class ParseExtra(unittest.TestCase):
    def test_ramping_loads(self):
        sets, _ = pt.parse_sets("25x8, 30x8, 35x8")
        self.assertEqual([(s["weight"], s["reps"]) for s in sets], [(25.0, 8), (30.0, 8), (35.0, 8)])

    def test_box_height_is_bodyweight(self):
        sets, _ = pt.parse_sets("60cm 2x10")
        self.assertEqual([(s["weight"], s["reps"]) for s in sets], [(0.0, 10), (0.0, 10)])


if __name__ == "__main__":
    unittest.main()
