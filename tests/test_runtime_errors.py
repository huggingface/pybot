import contextlib
import io
import os
import sys
import types
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pybot
from bot import runtime


def broken(*args):
    raise ValueError("broken rule")


def ok_reply(*args):
    return "Hello back."


class RuntimeErrorTest(unittest.TestCase):
    def test_hook_errors(self):
        observers = [("observer", 10, broken)]
        handlers = [("bad", 20, broken), ("first", 10, ok_reply), ("second", 5, ok_reply)]
        with mock.patch.multiple(runtime, _OBSERVERS=observers, _HANDLERS=handlers, _ARBITER=broken, _AFTER=[("after", 0, broken)]):
            errors = []
            out = runtime.turn("hello", {}, errors=errors)

        self.assertEqual(set(out), {"reply", "module", "candidates"})
        self.assertEqual(out["reply"], "Hello back.")
        self.assertEqual(out["module"], "first")
        self.assertEqual(errors, [
            ("observe", "observer", "ValueError: broken rule"),
            ("respond", "bad", "ValueError: broken rule"),
            ("choose", "arbiter", "ValueError: broken rule"),
            ("after", "after", "ValueError: broken rule"),
        ])

    def test_nested_turns(self):
        inner, outer = [], []

        def respond(text, memory):
            if text == "inside":
                raise ValueError("inside")
            runtime.turn("inside", {}, errors=inner)
            raise ValueError("outside")

        with mock.patch.multiple(runtime, _OBSERVERS=[], _AFTER=[], _HANDLERS=[("rule", 0, respond)]):
            runtime.turn("outside", {}, errors=outer)

        self.assertEqual(inner, [("respond", "rule", "ValueError: inside")])
        self.assertEqual(outer, [("respond", "rule", "ValueError: outside")])

    def test_strict_mode(self):
        with mock.patch.multiple(runtime, _OBSERVERS=[], _AFTER=[], _HANDLERS=[("rule", 0, broken)]):
            with self.assertRaisesRegex(ValueError, "broken rule"):
                runtime.turn("hello", {}, strict=True)

    def test_import_errors(self):
        entry = mock.Mock()
        entry.name = "broken"
        errors = []
        with mock.patch("pkgutil.iter_modules", return_value=[entry]), mock.patch("importlib.import_module", side_effect=SyntaxError("bad syntax")):
            self.assertEqual(runtime.load_modules(errors=errors), [])

        self.assertEqual(errors, [("broken", "SyntaxError: bad syntax")])
        self.assertIsInstance(runtime.LOAD_ERRORS, tuple)

    def test_plain_runtime_fallback(self):
        plain_ok = types.SimpleNamespace(turn=lambda text, memory: {"reply": "Plain ok.", "module": "chat"})
        errors = []
        reply, mod, _ = pybot.answer(plain_ok, "hello", {}, errors=errors)
        self.assertEqual((reply, mod, errors), ("Plain ok.", "chat", []))

        plain_bad = types.SimpleNamespace(turn=lambda text, memory: (_ for _ in ()).throw(RuntimeError("boom")))
        reply, mod, _ = pybot.answer(plain_bad, "hello", {}, errors=errors)
        self.assertEqual((reply, mod), ("Hello!", None))
        self.assertEqual(errors, [("turn", "runtime", "RuntimeError: boom")])

    def test_verbose_stderr(self):
        loaded = (("bad_import", "SyntaxError: bad syntax"),)
        for flags, stdin, expected in (
            (["-p", "hello"], "", ["Hello back."]),
            ([], "hello\nthere\n", ["Hello back.", "Hello back."]),
            (["-p", "hello", "-i"], "/exit\n", ["pybot: Hello back."]),
        ):
            with self.subTest(flags=flags):
                stdout, stderr = io.StringIO(), io.StringIO()
                handlers = [("bad", 10, broken), ("ok", 0, ok_reply)]
                with mock.patch.object(pybot, "load_bot", return_value=runtime), mock.patch.object(sys, "stdin", io.StringIO(stdin)):
                    with mock.patch.multiple(runtime, _OBSERVERS=[], _HANDLERS=handlers, _AFTER=[], LOAD_ERRORS=loaded):
                        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                            self.assertEqual(pybot.main(flags + ["-v"]), 0)
                lines = stdout.getvalue().splitlines()
                if "-i" in flags:
                    lines = [line for line in lines if line.startswith("pybot: ")]
                    self.assertNotIn("error:", stdout.getvalue())
                self.assertEqual(lines, expected)
                err = stderr.getvalue()
                self.assertEqual(err.count("[load error: bad_import | SyntaxError: bad syntax]"), 1)
                self.assertEqual(err.count("[error: respond/bad | ValueError: broken rule]"), len(expected))


if __name__ == "__main__":
    unittest.main()
