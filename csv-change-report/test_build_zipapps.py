"""Regression tests for reproducible portable builds and safe failure paths."""
import contextlib
import importlib.util
import io
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile


SOURCE = Path(__file__).resolve().parent


class BuildZipappsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        for name in ('build_zipapps.py', 'csv_change.py', 'view_report.py', 'LICENSE'):
            shutil.copyfile(SOURCE / name, self.source / name)
        self.originals = {p.name: p.read_bytes() for p in self.source.iterdir()}

    def run_builder(self, destination):
        return subprocess.run([sys.executable, '-I', str(self.source / 'build_zipapps.py'),
                               str(destination)], capture_output=True, text=True,
                              cwd=self.root)

    def assert_inputs_preserved(self):
        self.assertEqual(self.originals,
                         {p.name: p.read_bytes() for p in self.source.iterdir()})

    def test_reproducible_archives_embed_exact_programs_and_license(self):
        first, second = self.root / 'first', self.root / 'second'
        for destination in (first, second):
            result = self.run_builder(destination)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, '')
            self.assertEqual(result.stderr, '')
            self.assertEqual(sorted(p.name for p in destination.iterdir()),
                             ['csv_change.pyz', 'view_report.pyz'])
        for program in ('csv_change', 'view_report'):
            with self.subTest(program=program):
                archive = first / (program + '.pyz')
                self.assertEqual(archive.read_bytes(),
                                 (second / archive.name).read_bytes())
                with zipfile.ZipFile(archive) as built:
                    self.assertIsNone(built.testzip())
                    self.assertEqual(built.namelist(), ['__main__.py', 'LICENSE'])
                    self.assertEqual(built.read('__main__.py'),
                                     self.originals[program + '.py'])
                    self.assertEqual(built.read('LICENSE'), self.originals['LICENSE'])
        self.assert_inputs_preserved()

    def test_existing_destinations_are_refused_without_modification(self):
        directory = self.root / 'existing'
        directory.mkdir()
        sentinel = directory / 'keep'
        sentinel.write_bytes(b'preserve me')
        file = self.root / 'existing-file'
        file.write_bytes(b'also preserve me')
        for destination in (directory, file):
            with self.subTest(destination=destination.name):
                result = self.run_builder(destination)
                self.assertEqual(result.returncode, 2)
                self.assertIn('Existing destinations are never reused.', result.stderr)
                self.assertEqual(result.stdout, '')
        self.assertEqual(list(directory.iterdir()), [sentinel])
        self.assertEqual(sentinel.read_bytes(), b'preserve me')
        self.assertEqual(file.read_bytes(), b'also preserve me')
        self.assert_inputs_preserved()

    def test_each_missing_input_fails_before_claiming_destination(self):
        for name in ('LICENSE', 'csv_change.py', 'view_report.py'):
            with self.subTest(input=name):
                missing = self.source / name
                missing.unlink()
                destination = self.root / ('missing-' + name)
                result = self.run_builder(destination)
                self.assertEqual(result.returncode, 2)
                self.assertIn('Build refused or failed.', result.stderr)
                self.assertFalse(destination.exists())
                missing.write_bytes(self.originals[name])
        self.assert_inputs_preserved()

    def test_partial_build_is_preserved_with_inspection_diagnostic(self):
        # Load only the copied builder; inject a disk failure on the second ZIP.
        spec = importlib.util.spec_from_file_location('builder_under_test',
                                                      self.source / 'build_zipapps.py')
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        destination = self.root / 'partial'
        real_zipfile = zipfile.ZipFile

        def fail_second(path, *args, **kwargs):
            if Path(path).name == 'view_report.pyz':
                raise OSError('synthetic write failure')
            return real_zipfile(path, *args, **kwargs)

        error = io.StringIO()
        with mock.patch.object(sys, 'argv', ['build_zipapps.py', str(destination)]), \
                mock.patch.object(builder.zipfile, 'ZipFile', side_effect=fail_second), \
                contextlib.redirect_stderr(error):
            self.assertEqual(builder.main(), 2)
        self.assertIn('Preserve any output directory', error.getvalue())
        self.assertIn('choose a new destination after inspection', error.getvalue())
        first = destination / 'csv_change.pyz'
        self.assertTrue(first.is_file())
        self.assertFalse((destination / 'view_report.pyz').exists())
        with real_zipfile(first) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(archive.read('__main__.py'), self.originals['csv_change.py'])
        before = first.read_bytes()
        self.assertEqual(self.run_builder(destination).returncode, 2)
        self.assertEqual(first.read_bytes(), before)
        # Import can create bytecode; the source and license bytes remain exact.
        for name, data in self.originals.items():
            self.assertEqual((self.source / name).read_bytes(), data)


if __name__ == '__main__':
    unittest.main()
