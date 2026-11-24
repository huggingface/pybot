import os
import random
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from bot import runtime  # noqa: E402
from bot.compose import fallback  # noqa: E402


class AnswerAbovePredicates(unittest.TestCase):
    def setUp(self):
        random.seed(0)

    def test_small_talk_after_a_knowledge_answer_does_not_raise(self):
        memory = {"turns": [{"module": "answers", "bot": "x" * 60}]}
        self.assertTrue(fallback.reads_as_small_talk("are you having a good day", memory))

    def test_the_two_answer_above_readings_keep_distinct_inputs(self):
        self.assertTrue(fallback._knowledge_answer_above(
            {"turns": [{"module": "answers", "bot": "x" * 60}]}))
        self.assertFalse(fallback._knowledge_answer_above({"turns": []}))
        self.assertTrue(fallback._substantive_answer_above([{"bot": "one two three four five six seven eight"}]))
        self.assertFalse(fallback._substantive_answer_above([]))

    def test_small_talk_after_an_egg_answer_is_not_another_egg_answer(self):
        memory = {}
        runtime.turn("how long should i boil an egg", memory)
        result = runtime.turn("are you having a good day", memory)
        self.assertNotEqual(result["module"], "answers")
        self.assertNotIn("cholesterol", result["reply"].lower())
        self.assertNotIn("egg", result["reply"].lower())


if __name__ == "__main__":
    unittest.main()
