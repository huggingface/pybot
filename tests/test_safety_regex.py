import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from bot import runtime
from bot.modules import safety


class SafetyRegexTest(unittest.TestCase):
    def test_patterns_compile(self):
        for name, val in vars(safety).items():
            if isinstance(val, (tuple, list)):
                for i, item in enumerate(val):
                    if isinstance(item, str) and ("\\" in item or "(?" in item):
                        with self.subTest(name=name, index=i):
                            re.compile(item)

    def test_wish_dead_tails(self):
        cases = {
            "": True,
            " \t\n": True,
            ",": False,
            ", \t\n": False,
            ",, honestly": False,
            ", !": False,
            "\t,\n honestly!": True,
            ", no\tjoke.": True,
            ", tbh\n": True,
            ", honestly, my exam went badly": False,
            ", honestly my exam went badly": False,
            ", that exam was brutal": False,
            ", any more": True,
            ", tonight": True,
            ", todayish": False,
            " tired": False,
            " set on finishing it": False,
        }
        for tail, expected in cases.items():
            with self.subTest(tail=tail):
                self.assertEqual(safety._matches(safety.WISH_DEAD, "i wish i was dead" + tail), expected)

    def test_emergency_routing(self):
        for line in ("i wish i was dead", "my dad collapsed and isn't breathing", "i drank bleach while cleaning the bathroom"):
            with self.subTest(line=line):
                self.assertEqual(runtime.turn(line, {})["module"], "safety")


if __name__ == "__main__":
    unittest.main()
