"""Tests for the definition reader's key-phrase index (issue: reply time spent scanning the deck).

Run from the repository root: python -m unittest discover -s tests

The index must admit exactly the entries the plain scan would pass, and the candidates
must be read in deck order, so every answer stays the answer it was.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.knowledge import entries as all_entries  # noqa: E402
from bot.knowledge.lookup import _defines, _forms  # noqa: E402

ASKS = ["what is a sql join", "what is nappy rash", "what is a wet room",
        "what is a boundary fence", "what is a sports bra", "what are eggs",
        "what is dacia", "what is ankle", "what is allergy test",
        "what is altitude", "what is a whole", "what is abroad"]


def _defines_scanned(understood, forms, entries, reject=None):
    """The pre-index scan, kept here as the equivalence reference."""
    clean = understood.get("clean") if isinstance(understood, dict) else ""
    said = clean or (understood.get("text") if isinstance(understood, dict) else "") or ""
    thing = sys.modules["bot.knowledge.lookup"]._the_thing_asked_about(said)
    if not thing:
        return None
    purpose = sys.modules["bot.knowledge.lookup"]._asks_what_it_is_for(said)
    best = None
    best_rank = None
    for item in entries:
        if reject is not None and reject(item):
            continue
        if not sys.modules["bot.knowledge.lookup"].guard_passes(item, understood):
            continue
        if not sys.modules["bot.knowledge.lookup"]._the_key_names_the_thing(item, thing):
            continue
        if not sys.modules["bot.knowledge.lookup"]._the_reply_defines(getattr(item, "reply", ""), thing, purpose):
            continue
        if any(sys.modules["bot.knowledge.lookup"]._part_score(word, forms) for word in item.avoid):
            continue
        rank = -len(sys.modules["bot.knowledge.lookup"]._key_forms(item))
        if best_rank is None or rank > best_rank:
            best, best_rank = item, rank
    return best


class TestDefinesIndex(unittest.TestCase):
    def setUp(self):
        self.deck = all_entries()

    def _forms_of(self, ask):
        return [_forms(word) for word in ask.split()]

    def test_indexed_matches_the_plain_scan(self):
        for ask in ASKS:
            with self.subTest(ask=ask):
                understood = {"clean": ask, "text": ask, "words": ask.split()}
                forms = self._forms_of(ask)
                got = _defines(understood, forms, False, self.deck)
                want = _defines_scanned(understood, forms, self.deck)
                self.assertEqual(
                    (got.id if got is not None else None),
                    (want.id if want is not None else None),
                    f"the indexed reader changed the answer to {ask!r}")

    def test_a_foreign_entries_list_gets_its_own_index(self):
        small = self.deck[:50]
        for ask in ["what is a wet room", "what is ankle"]:
            understood = {"clean": ask, "text": ask, "words": ask.split()}
            forms = self._forms_of(ask)
            got = _defines(understood, forms, False, small)
            want = _defines_scanned(understood, forms, small)
            self.assertEqual(
                (got.id if got is not None else None),
                (want.id if want is not None else None),
                f"a smaller deck changed the answer to {ask!r}")

    def test_first_word_forms_are_covered_by_the_index(self):
        # "what are eggs" reaches keys on "egg" through the forms of the thing's first word.
        understood = {"clean": "what are eggs", "text": "what are eggs", "words": "what are eggs".split()}
        forms = self._forms_of("what are eggs")
        got = _defines(understood, forms, False, self.deck)
        want = _defines_scanned(understood, forms, self.deck)
        self.assertEqual(
            (got.id if got is not None else None),
            (want.id if want is not None else None))


if __name__ == "__main__":
    unittest.main()
