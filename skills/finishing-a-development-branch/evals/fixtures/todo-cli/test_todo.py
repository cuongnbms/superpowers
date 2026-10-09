import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import todo


class TodoTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        todo.STORE = Path(self.dir.name) / "todo.json"

    def tearDown(self):
        self.dir.cleanup()

    def run_cli(self, *argv):
        out = io.StringIO()
        with redirect_stdout(out):
            todo.main(list(argv))
        return out.getvalue()

    def test_add_and_list(self):
        self.run_cli("add", "milk")
        self.assertEqual(self.run_cli("list"), "[ ] #1 milk\n")

    def test_done(self):
        self.run_cli("add", "milk")
        self.run_cli("done", "1")
        self.assertEqual(self.run_cli("list"), "[x] #1 milk\n")


if __name__ == "__main__":
    unittest.main()
