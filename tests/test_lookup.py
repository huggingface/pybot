import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from bot.knowledge import lookup


def make_card(name):
    item = lookup.entry(name, (name,), name.capitalize() + ".")
    item.domain = "health"
    return item


class NameCardTest(unittest.TestCase):
    def test_replace_entry(self):
        cards = [make_card("heat rash")]
        self.assertIs(lookup._the_name_card(["heat", "rash"], cards), cards[0])

        cards[0] = make_card("cradle cap")
        self.assertIsNone(lookup._the_name_card(["heat", "rash"], cards))
        self.assertIs(lookup._the_name_card(["cradle", "cap"], cards), cards[0])

    def test_mutate_entry(self):
        item = make_card("heat rash")
        cards = [item]
        self.assertIs(lookup._the_name_card(["heat", "rash"], cards), item)

        item.key = (("chest infection", "cough"),)
        self.assertIsNone(lookup._the_name_card(["heat", "rash"], cards))
        self.assertIsNone(lookup._the_name_card(["infection"], cards))
        self.assertIs(lookup._the_name_card(["chest", "infection"], iter(cards)), item)

        item.domain = "travel"
        self.assertIsNone(lookup._the_name_card(["chest", "infection"], cards))

    def test_deck_order(self):
        first, second = make_card("heat rash"), make_card("heat rash")
        cards = [first, second]
        self.assertIs(lookup._the_name_card(["heat", "rash"], cards), first)
        self.assertIs(lookup._the_name_card(["heat", "rash"], cards, lambda row: row is first), second)
        self.assertIsNone(lookup._the_name_card(["heat", "rash"], cards, allowed={"travel"}))


if __name__ == "__main__":
    unittest.main()
