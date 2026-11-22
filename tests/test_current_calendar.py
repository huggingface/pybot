import datetime
import unittest
from unittest.mock import patch

from bot.knowledge.maths import _today
from bot.memory.when import asks_what_today_is


class NewYearsDay(datetime.date):
    @classmethod
    def today(cls):
        return cls(2031, 1, 1)


class CurrentCalendar(unittest.TestCase):
    @patch("datetime.date", NewYearsDay)
    def test_asks_for_the_current_month_or_year(self):
        for question, expected in [
            ("what month is it?", "It's January."),
            ("which month are we in?", "It's January."),
            ("what is the month?", "It's January."),
            ("what year is it?", "It's 2031."),
            ("what's the current year?", "It's 2031."),
        ]:
            with self.subTest(question=question):
                self.assertTrue(asks_what_today_is(question))
                self.assertEqual(_today(question), expected)

    def test_questions_about_specific_events_are_left_to_other_readers(self):
        for question in ("what month is my exam?", "what year was it?", "what year is it set in?"):
            with self.subTest(question=question):
                self.assertFalse(asks_what_today_is(question))
                self.assertIsNone(_today(question))
