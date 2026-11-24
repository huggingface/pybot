import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from bot.understanding import normalize, topics  # noqa: E402
from bot.knowledge import maths, units  # noqa: E402


class NumberRegressions(unittest.TestCase):
    def solve(self, text):
        return maths.solve(text, {"clean": text}, {})

    def test_leading_dot_decimal_survives_normalisation_and_extraction(self):
        line = normalize.normalise(".5 kg")
        numbers = topics.detect_numbers(line)
        self.assertEqual([item["value"] for item in numbers], [0.5])
        self.assertEqual(numbers[0]["unit"], "kg")

    def test_leading_dot_decimal_converts(self):
        reply = units.convert(".5 kg in g")
        self.assertIsNotNone(reply)
        self.assertIn("500", reply)
        self.assertIn("gram", reply.lower())

    def test_small_nonzero_conversions_do_not_round_to_zero(self):
        for text, expected in (("2.5 g in kg", "0.0025"),
                               ("1 ml in l", "0.001"),
                               ("100 mg in kg", "0.0001")):
            with self.subTest(text=text):
                self.assertIn(expected, units.convert(text))

    def test_undefined_fraction_amount_is_not_partially_parsed(self):
        for text in ("half of 1/0", "half of 1/00", "half of 1/0.0",
                     "half of .5/0", "2/3 of .5/0"):
            with self.subTest(text=text):
                self.assertIsNone(self.solve(text))

    def test_malformed_numeric_tokens_return_no_answer(self):
        for text in ("square root of 1..2", "cube root of 1..2",
                     "what is 20% of .", "what percentage is . of 80",
                     "increase 1..2 by 5%", "15% tip on 1..2", "20% more than 1..2"):
            with self.subTest(text=text):
                self.assertIsNone(self.solve(text))

    def test_valid_arithmetic_still_works(self):
        self.assertIn("500", self.solve("what is 20% of 2500"))
        self.assertIn("12", self.solve("square root of 144"))
        self.assertIn("0.5", self.solve("half of 1"))


if __name__ == "__main__":
    unittest.main()
