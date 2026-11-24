import os
import random
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from bot import runtime  # noqa: E402


class MemoryRegressions(unittest.TestCase):
    def setUp(self):
        random.seed(0)
        self.memory = {}

    def say(self, text):
        return runtime.turn(text, self.memory)

    def test_explicit_city_correction_does_not_replace_the_name(self):
        self.say("my name is sam")
        self.say("actually i live in manchester")
        reply = self.say("what is my name")["reply"]
        self.assertEqual(str(self.memory["user"].get("name")).lower(), "sam")
        self.assertEqual(str(self.memory["user"].get("city")).lower(), "manchester")
        self.assertIn("sam", reply.lower())

    def test_explicit_job_correction_does_not_replace_the_name(self):
        self.say("im a nurse")
        self.say("my name is sam")
        self.say("actually im a doctor")
        self.assertEqual(str(self.memory["user"].get("name")).lower(), "sam")
        self.assertIn("doctor", str(self.memory["user"].get("job")).lower())

    def test_bare_age_correction_still_works(self):
        self.say("im 34")
        self.say("no im 35")
        self.assertEqual(self.memory["user"].get("age"), 35)
        self.assertIn("35", self.say("how old am i")["reply"])

    def test_diet_denial_is_not_a_markerless_correction(self):
        for denial in ("im not vegetarian", "i'm not vegetarian", "i am not vegetarian"):
            with self.subTest(denial=denial):
                self.memory = {}
                self.say("i am vegetarian")
                self.say(denial)
                self.assertNotIn("diet", self.memory.get("user") or {})

    def test_other_son_has_a_stable_identity(self):
        self.say("my son is 7")
        self.say("my other son is 5")
        self.assertEqual([entry.get("who") for entry in self.memory["others"]],
                         ["son", "other son"])
        self.assertIn("5", self.say("how old is my other son")["reply"])
        self.assertIn("7", self.say("how old is my son")["reply"])

    def test_pronoun_correction_updates_the_newest_other_son(self):
        self.say("my son is 7")
        self.say("my other son is 5")
        self.say("actually hes 6")
        ages = {entry["who"]: entry.get("age") for entry in self.memory["others"]}
        self.assertEqual(ages, {"son": 7, "other son": 6})
        self.assertIn("6", self.say("how old is my other son")["reply"])
        self.assertIn("7", self.say("how old is my son")["reply"])
    def test_explicit_name_correction_still_replaces_the_name(self):
        self.say("my name is sam")
        self.say("actually my name is alex")
        self.assertEqual(str(self.memory["user"].get("name")).lower(), "alex")

    def test_other_son_summary_does_not_merge_the_first_son(self):
        self.say("my son is 7")
        self.say("my other son is 5")
        reply = self.say("what do you know about my other son")["reply"]
        self.assertIn("5", reply)
        self.assertNotIn("7", reply)

    def test_later_facts_merge_into_the_same_other_son(self):
        self.say("my son is 7")
        self.say("my other son is 5")
        self.say("my other son is allergic to peanuts")
        reply = self.say("what is my other son allergic to")["reply"]
        self.assertIn("peanut", reply.lower())
        self.assertEqual([entry.get("who") for entry in self.memory["others"]],
                         ["son", "other son"])
    def test_equivalent_other_relative_descriptors_recall_the_same_person(self):
        for descriptor in ("second", "youngest"):
            with self.subTest(descriptor=descriptor):
                self.memory = {}
                self.say("my son is 7")
                self.say("my %s son is 5" % descriptor)
                reply = self.say("how old is my %s son" % descriptor)["reply"]
                self.assertIn("5", reply)
                self.assertNotIn("7", reply)


if __name__ == "__main__":
    unittest.main()
