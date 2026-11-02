"""Subprocess regressions for the fictional safety example (stdlib only)."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

PRODUCT = Path(__file__).resolve().parent


class RegenerateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="csv-regenerate-")
        self.addCleanup(self.temp.cleanup)
        self.product = Path(self.temp.name)
        for name in ("csv_change.py", "view_report.py"):
            shutil.copyfile(PRODUCT / name, self.product / name)
        self.example = self.product / "safety-example"
        shutil.copytree(PRODUCT / "safety-example", self.example)
        self.outputs = [self.example / ("new-report." + ext) for ext in ("json", "html")]

    def run_helper(self):
        return subprocess.run([sys.executable, "-B", str(self.example / "regenerate.py")],
                              cwd=self.temp.name, capture_output=True, text=True, timeout=30)

    def assert_retained(self, result):
        self.assertIn("Viewer failed", result.stderr)
        for output in self.outputs:
            self.assertIn(str(output), result.stderr)
        self.assertIn("left in place", result.stderr)

    def test_fresh_generation_matches_saved_example(self):
        result = self.run_helper()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(self.outputs[0].read_text()),
                         json.loads((self.example / "report.json").read_text()))
        self.assertEqual(self.outputs[1].read_bytes(), (self.example / "report.html").read_bytes())

    def test_each_existing_output_refuses_without_writing(self):
        for output in self.outputs:
            with self.subTest(output=output.name):
                output.write_bytes(b"keep existing output\x00")
                result = self.run_helper()
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("Output already exists", result.stderr)
                self.assertEqual(output.read_bytes(), b"keep existing output\x00")
                self.assertFalse(next(p for p in self.outputs if p != output).exists())
                output.unlink()

    def test_viewer_failure_retains_json_and_refuses_repeat(self):
        (self.product / "view_report.py").write_text("raise SystemExit(7)\n")
        result = self.run_helper()
        self.assertEqual(result.returncode, 7, result.stderr)
        self.assert_retained(result)
        json.loads(self.outputs[0].read_text())
        self.assertFalse(self.outputs[1].exists())
        retained = self.outputs[0].read_bytes()
        repeat = self.run_helper()
        self.assertEqual(repeat.returncode, 2, repeat.stderr)
        self.assertNotIn("Viewer failed", repeat.stderr)
        self.assertEqual(self.outputs[0].read_bytes(), retained)
        self.assertFalse(self.outputs[1].exists())

    def test_partial_viewer_output_is_preserved(self):
        (self.product / "view_report.py").write_text(
            "from pathlib import Path\nimport sys\n"
            "Path(sys.argv[sys.argv.index('--output') + 1]).write_bytes(b'partial html')\n"
            "raise SystemExit(7)\n")
        result = self.run_helper()
        self.assertEqual(result.returncode, 7, result.stderr)
        self.assert_retained(result)
        retained = [p.read_bytes() for p in self.outputs]
        self.assertEqual(retained[1], b"partial html")
        self.assertEqual(self.run_helper().returncode, 2)
        self.assertEqual([p.read_bytes() for p in self.outputs], retained)

    def test_comparator_failure_has_no_viewer_diagnostic(self):
        (self.example / "before.csv").write_text("wrong,value\n1,x\n")
        result = self.run_helper()
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertNotIn("Viewer failed", result.stderr)
        self.assertTrue(all(not p.exists() for p in self.outputs))


if __name__ == "__main__":
    unittest.main()
