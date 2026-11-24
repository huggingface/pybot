import os
import random
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from bot import runtime  # noqa: E402
from bot.understanding import normalize, references  # noqa: E402
from bot.memory import topics  # noqa: E402


class PlaceholderReferences(unittest.TestCase):
    def setUp(self):
        random.seed(0)

    def test_explicit_object_frame_is_a_placeholder(self):
        line = normalize.normalise("is it safe to drink the tap water")
        self.assertTrue(references._a_placeholder_it(line))

    def test_real_back_reference_is_not_a_placeholder(self):
        for text in ("is it worth getting a new one", "is it ok to use it in the rain"):
            with self.subTest(text=text):
                self.assertFalse(references._a_placeholder_it(normalize.normalise(text)))

    def test_placeholder_frame_is_not_a_follow_up(self):
        text = "is it safe to drink the tap water"
        memory = {"topic": {"turn": 0, "text": "my cat scratches the sofa",
                            "words": ["cat", "scratch", "sofa"]},
                  "turns": [{"user": "my cat scratches the sofa", "bot": "advice"}]}
        self.assertFalse(topics.is_follow_up(text, memory))

    def test_tap_water_question_does_not_contaminate_the_next_follow_up(self):
        memory = {}
        runtime.turn("my cat keeps scratching the sofa", memory)
        runtime.turn("is it safe to drink the tap water", memory)
        self.assertEqual(memory["understood"].get("clean"),
                         "is it safe to drink the tap water")
        result = runtime.turn("is it safe", memory)
        reply = result["reply"].lower()
        for stale in ("cat", "scratch", "sofa"):
            self.assertNotIn(stale, reply)
        understood = memory["understood"]
        self.assertNotEqual(understood.get("topic"), "pets")
        self.assertEqual((understood.get("ref") or {}).get("it"), "tap")
        topic_words = set((memory.get("topic") or {}).get("words") or [])
        self.assertIn("water", topic_words)
        self.assertNotIn("cat", topic_words)
    def test_brake_safety_question_keeps_the_car_reference(self):
        memory = {}
        runtime.turn("my brakes make a grinding noise", memory)
        result = runtime.turn("is it safe to drive", memory)
        self.assertEqual((memory["understood"].get("ref") or {}).get("it"), "brakes")
        self.assertEqual(memory["understood"].get("topic"), "cars")
        follow_up = runtime.turn("is it safe", memory)
        reply = follow_up["reply"].lower()
        self.assertTrue(any(word in reply for word in ("brake", "car", "recovering", "stop driving")))
        self.assertNotIn("cat", reply)

    def test_new_one_still_points_back_to_the_boiler(self):
        memory = {}
        runtime.turn("my boiler needs its yearly service", memory)
        result = runtime.turn("is it worth getting a new one", memory)
        self.assertEqual((memory["understood"].get("ref") or {}).get("it"), "boiler")
        self.assertTrue(any(word in result["reply"].lower()
                            for word in ("boiler", "gas", "pressure", "reset")))


if __name__ == "__main__":
    unittest.main()
