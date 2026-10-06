import os, sys, tempfile, unittest, io, json
from contextlib import redirect_stdout
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import dupefind


def w(root, rel, data):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as f:
        f.write(data)


class T(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.r = self.d.name
        w(self.r, "a.txt", b"hello")
        w(self.r, "sub/b.txt", b"hello")
        w(self.r, "c.txt", b"world")
        w(self.r, "d.txt", b"hellO")
        w(self.r, "skip/e.txt", b"hello")
        w(self.r, "f.log", b"hello")
        w(self.r, ".gitignore", b"skip/\n*.log\n")

    def tearDown(self):
        self.d.cleanup()

    def names(self, **k):
        return [[os.path.relpath(p, self.r) for p in g["files"]]
                for g in dupefind.find_dupes(self.r, **k)]

    def test_groups_and_ignore(self):
        self.assertEqual(self.names(), [["a.txt", "sub/b.txt"]])

    def test_min_size(self):
        self.assertEqual(self.names(min_size=100), [])

    def run_cli(self, *args):
        buf = io.StringIO()
        with redirect_stdout(buf):
            dupefind.main([self.r, *args])
        return buf.getvalue()

    def test_json(self):
        self.assertEqual(len(json.loads(self.run_cli("--json"))), 1)

    def test_hint_keeps_first(self):
        out = self.run_cli("--delete-hint")
        self.assertIn("rm --", out)
        self.assertIn("b.txt", out.split("rm --")[1])
        self.assertTrue(os.path.exists(os.path.join(self.r, "sub/b.txt")))


if __name__ == "__main__":
    unittest.main()
