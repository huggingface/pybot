import argparse
import io
import os
import sys
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pybot  # noqa: E402


class StubRuntime:
    def turn(self, text, memory):
        return {"reply": "Cost: £10 — 你好", "module": "stub"}


class GBK(io.TextIOWrapper):
    def __init__(self):
        super().__init__(io.BytesIO(), encoding="gbk", errors="strict", write_through=True)


class DynamicOutputEncoding(unittest.TestCase):
    def output(self, call):
        stream = GBK()
        with mock.patch.object(sys, "stdout", stream):
            call(stream)
        stream.flush()
        return stream.buffer.getvalue().decode("gbk")

    def test_one_shot_escapes_characters_the_stream_cannot_encode(self):
        args = argparse.Namespace(prompt="hello", verbose=False)
        text = self.output(lambda stream: pybot.one_shot(StubRuntime(), args))
        self.assertIn(r"\xa3", text)

    def test_pipe_escapes_characters_the_stream_cannot_encode(self):
        args = argparse.Namespace(verbose=False)
        stdin = io.StringIO("hello\n")
        with mock.patch.object(sys, "stdin", stdin):
            text = self.output(lambda stream: pybot.pipe(StubRuntime(), args))
        self.assertIn(r"\xa3", text)

    def test_chat_escapes_both_user_echo_and_reply(self):
        args = argparse.Namespace(prompt="£10", interactive=True, seed=None, verbose=False)
        with mock.patch("builtins.input", side_effect=["/exit"]):
            text = self.output(lambda stream: pybot.chat(StubRuntime(), args))
        self.assertIn(r"user: \xa310", text)
        self.assertIn(r"pybot: Cost: \xa310", text)


if __name__ == "__main__":
    unittest.main()
