"""Synthetic end-to-end manifest tests; no network or customer data."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import contextlib
import io

ROOT = Path(__file__).resolve().parent
SCRIPT = ROOT / 'evaluation/batch-manifest.py'
spec = importlib.util.spec_from_file_location('batch_manifest', SCRIPT)
manifest_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manifest_module)


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.data = self.root / 'data space'
        self.data.mkdir()
        self.before = self.data / '-before $(touch NEVER).csv'
        self.after = self.data / 'after café.csv'
        self.before.write_text('id,value,time\n1,a,x\n', encoding='utf-8')
        self.after.write_text('id,value,time\n1,b,y\n', encoding='utf-8')
        self.manifest = self.data / 'batch.json'
        self.valid = {'version': 1, 'pairs': [{'before': self.before.name,
                       'after': self.after.name, 'key': 'id'}]}

    def write(self, data=None):
        self.manifest.write_text(json.dumps(self.valid if data is None else data), encoding='utf-8')

    def run_manifest(self, name='reports', options=()):
        return subprocess.run([sys.executable, str(SCRIPT), *options, str(self.manifest), name],
                              cwd=self.root, capture_output=True, timeout=20)

    def assert_refusal(self, result, code=None, report='reports'):
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, b'')
        expected = {('Cannot run manifest [' + k + ']: ' + v + '\n').encode()
                    for k, v in manifest_module.REASONS.items()}
        self.assertIn(result.stderr, expected)
        if code is not None:
            self.assertEqual(result.stderr, ('Cannot run manifest [' + code + ']: ' +
                             manifest_module.REASONS[code] + '\n').encode())
        self.assertFalse((self.root / report).exists())

    def test_corrected_manifest_collision_preserves_reports_and_inputs(self):
        # Exercise the CLI adapter as well as its shell runner. Existing paths
        # include reports, the manifest's directory, and regular input files.
        def snapshot():
            return {str(p.relative_to(self.root)): p.read_bytes()
                    for p in self.root.rglob('*') if p.is_file()}

        self.valid['pairs'].append(dict(self.valid['pairs'][0], key='missing'))
        self.write()
        partial = self.run_manifest('partial', ('--totals',))
        self.assertEqual(partial.returncode, 2)
        original_reports = {p.name: p.read_bytes()
                            for p in (self.root / 'partial').iterdir()}
        partial_totals = json.loads((self.root / 'partial/totals.json').read_text())
        self.assertTrue(partial_totals['partial'])
        self.valid['pairs'][1]['key'] = 'id'
        self.write()
        occupied = self.root / 'occupied'
        (occupied / 'nested').mkdir(parents=True)
        (occupied / 'nested/keep.bin').write_bytes(bytes(range(256)))
        (occupied / 'status.tsv').write_bytes(b'existing status\n')
        protected = snapshot()
        for index, options in enumerate(((), ('--totals',))):
            for target in ('partial', 'occupied', str(self.data),
                           str(self.manifest), str(self.before)):
                with self.subTest(options=options, target=target):
                    refused = self.run_manifest(target, options)
                    self.assertEqual(refused.returncode, 2)
                    self.assertEqual(refused.stdout, b'')
                    self.assertIn(b'Cannot create a new report directory; choose an unused path.',
                                  refused.stderr)
                    self.assertEqual(snapshot(), protected)
                    self.assertFalse((self.root / 'NEVER').exists())
            fresh = self.root / ('recovered-' + str(index))
            recovered = self.run_manifest(str(fresh), options)
            self.assertEqual(recovered.returncode, 1)
            self.assertEqual(recovered.stderr, b'')
            statuses = (fresh / 'status.tsv').read_text().splitlines()[1:]
            self.assertEqual([row.split('\t')[1] for row in statuses], ['1', '1'])
            self.assertEqual((fresh / 'totals.json').exists(), bool(options))
            if options:
                totals = json.loads((fresh / 'totals.json').read_text())
                self.assertFalse(totals['partial'])
            self.assertEqual(original_reports, {p.name: p.read_bytes()
                             for p in (self.root / 'partial').iterdir()})
            # Exclude only the newly created recovery subtree for this check.
            current = snapshot()
            self.assertEqual({n: current[n] for n in protected}, protected)
            protected = current

    def test_validate_only_never_launches_runner_or_reads_csvs(self):
        # Nonexistent inputs and shell-looking strings are valid manifest data.
        self.valid['pairs'][0]['before'] = 'missing $(touch NEVER).csv'
        self.write()
        triples = manifest_module.load_manifest(self.manifest)
        self.assertEqual(triples[0], str(self.data / 'missing $(touch NEVER).csv'))
        self.assertEqual(triples[1], str(self.after))
        self.assertEqual(triples[2], 'id')
        for report in ([], [str(self.root / 'reports')], [str(self.before)]):
            with self.subTest(report=report):
                output = io.StringIO()
                with mock.patch.object(sys, 'argv', ['batch-manifest.py', '--validate-only',
                        '--totals', '--ignore-column=time', str(self.manifest), *report]), \
                     mock.patch.object(manifest_module.subprocess, 'run') as runner, \
                     contextlib.redirect_stdout(output):
                    self.assertEqual(manifest_module.main(), 0)
                runner.assert_not_called()
                self.assertEqual(output.getvalue(),
                    'Manifest valid: 1 pair(s); CSV files not checked; no reports created.\n')
        self.assertFalse((self.root / 'reports').exists())
        self.assertFalse((self.root / 'NEVER').exists())
        self.assertEqual(self.before.read_text(), 'id,value,time\n1,a,x\n')

    def test_validate_only_cli_and_invalid_cases(self):
        self.write()
        result = subprocess.run([sys.executable, str(SCRIPT), '--validate-only',
            str(self.manifest)], cwd=self.root, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, b'')
        self.assertEqual(result.stdout,
            b'Manifest valid: 1 pair(s); CSV files not checked; no reports created.\n')
        for raw, code in [(b'{', 'E_JSON'), (b'{}', 'E_SCHEMA'),
                          (b'{"version":1,"pairs":[]}', 'E_PAIRS')]:
            self.manifest.write_bytes(raw)
            self.assert_refusal(self.run_manifest(options=('--validate-only',)), code)
        self.write()
        self.assert_refusal(self.run_manifest(options=('--validate-only',
                            '--max-input-bytes=0')), 'E_BUDGET')
        missing_report = subprocess.run([sys.executable, str(SCRIPT), str(self.manifest)],
            cwd=self.root, capture_output=True, timeout=20)
        self.assert_refusal(missing_report, 'E_ARGUMENTS')

    def assert_json_result(self, result, code, pairs=None):
        self.assertEqual(result.returncode, 0 if code == 'OK' else 2)
        self.assertEqual(json.loads(result.stdout), {
            'version': 1, 'valid': code == 'OK', 'code': code,
            'pair_count': pairs, 'csv_files_checked': False, 'reports_created': False})
        self.assertEqual(len(result.stdout.splitlines()), 1)
        self.assertNotIn(b'PRIVATE_SENTINEL', result.stdout + result.stderr)
        if code == 'OK':
            self.assertEqual(result.stderr, b'')
        else:
            self.assertEqual(result.stderr, ('Cannot run manifest [' + code + ']: ' +
                manifest_module.REASONS[code] + '\n').encode())
        self.assertFalse((self.root / 'reports').exists())

    def test_json_preflight_success_counts_and_preserves_inputs(self):
        for count in (1, 100):
            self.valid['pairs'] = [dict(before='PRIVATE_SENTINEL missing.csv',
                after='PRIVATE_SENTINEL $(touch NEVER).csv', key='PRIVATE_SENTINEL')] * count
            self.write()
            before = {p: p.read_bytes() for p in self.data.iterdir()}
            self.assert_json_result(self.run_manifest(options=('--json', '--validate-only')),
                                    'OK', count)
            self.assertEqual(before, {p: p.read_bytes() for p in self.data.iterdir()})
            self.assertFalse((self.root / 'NEVER').exists())

    def test_preflight_does_not_pin_later_csv_contents(self):
        # Sequential mutations, not a concurrency or filesystem atomicity test.
        self.write()
        manifest_bytes = self.manifest.read_bytes()
        before_bytes = self.before.read_bytes()
        cases = [
            ('changed-to-equal', b'id,value,time\n1,b,y\n', before_bytes, 0),
            ('equal-to-changed', before_bytes, b'id,value,time\n1,c,x\n', 1),
            ('valid-to-duplicate', before_bytes,
             b'id,value,time\n1,c,x\n1,d,x\n', 2),
        ]
        for name, initial, later, expected in cases:
            with self.subTest(case=name):
                self.after.write_bytes(initial)
                target = self.root / name
                preflight = self.run_manifest(str(target), ('--validate-only', '--json'))
                self.assert_json_result(preflight, 'OK', 1)
                self.assertFalse(target.exists())
                self.assertEqual(self.after.read_bytes(), initial)
                self.after.write_bytes(later)
                # The same preflight response accepts the changed input, too.
                repeated = self.run_manifest(str(target), ('--validate-only', '--json'))
                self.assert_json_result(repeated, 'OK', 1)
                self.assertEqual(repeated.stdout, preflight.stdout)
                result = self.run_manifest(str(target), ('--totals',))
                self.assertEqual(result.returncode, expected)
                table = (target / 'status.tsv').read_text().splitlines()
                self.assertEqual(len(table), 2)
                fields = table[1].split('\t')
                self.assertEqual(fields[1], str(expected))
                totals = json.loads((target / 'totals.json').read_text())
                self.assertEqual(totals['completed'], 1)
                self.assertEqual(totals['equal'], int(expected == 0))
                self.assertEqual(totals['changed'], int(expected == 1))
                self.assertEqual(totals['error'], int(expected == 2))
                self.assertEqual(totals['partial'], expected == 2)
                if expected == 2:
                    self.assertEqual(fields[2], '-')
                    self.assertFalse((target / 'pair-0001.json').exists())
                    self.assertTrue((target / fields[3]).read_bytes())
                else:
                    report = json.loads((target / fields[2]).read_text())
                    self.assertEqual(report['counts']['changed'], expected)
                    self.assertEqual(report['counts']['unchanged'], 1 - expected)
                    self.assertEqual((target / fields[3]).read_bytes(), b'')
                self.assertEqual(self.manifest.read_bytes(), manifest_bytes)
                self.assertEqual(self.before.read_bytes(), before_bytes)
                self.assertEqual(self.after.read_bytes(), later)
                self.assertFalse((self.root / 'NEVER').exists())

    def test_json_preflight_fixed_failure_codes(self):
        pair = self.valid['pairs'][0]
        cases = [
            (b'\xffPRIVATE_SENTINEL', 'E_ENCODING'),
            (b'\xef\xbb\xbfPRIVATE_SENTINEL', 'E_BOM'),
            (b'{PRIVATE_SENTINEL', 'E_JSON'),
            (b'[' * 33 + b']' * 33, 'E_DEPTH'),
            (b' ' * 65537, 'E_SIZE'),
            (b'{"version":1,"version":1,"pairs":[]}', 'E_DUPLICATE'),
            (b'{"PRIVATE_SENTINEL":1}', 'E_SCHEMA'),
            (json.dumps(dict(self.valid, version=True)).encode(), 'E_VERSION'),
            (json.dumps(dict(self.valid, pairs=[])).encode(), 'E_PAIRS'),
            (json.dumps(dict(self.valid, pairs=[pair, {}])).encode(), 'E_PAIR'),
            (json.dumps(dict(self.valid, pairs=[dict(pair, key='PRIVATE_SENTINEL\n')])).encode(), 'E_TEXT'),
        ]
        for raw, code in cases:
            with self.subTest(code=code):
                self.manifest.write_bytes(raw)
                self.assert_json_result(self.run_manifest(options=('--validate-only', '--json')), code)
                self.assertEqual(self.manifest.read_bytes(), raw)
        self.manifest.unlink()
        self.assert_json_result(self.run_manifest(options=('--validate-only', '--json')), 'E_READ')
        self.manifest.mkdir()
        self.assert_json_result(self.run_manifest(options=('--validate-only', '--json')), 'E_FILE')

    def test_json_argument_errors_refuse_execution(self):
        self.write()
        for options, code in [
            (('--json',), 'E_ARGUMENTS'),
            (('--json', '--validate-only', '--PRIVATE_SENTINEL'), 'E_ARGUMENTS'),
            (('--validate-only', '--max-input-bytes=PRIVATE_SENTINEL', '--json'), 'E_ARGUMENTS'),
            (('--json', '--validate-only', '--max-input-bytes=0'), 'E_BUDGET'),
            (('--json', '--validate-only', '--ignore-column=PRIVATE_SENTINEL\n'), 'E_TEXT'),
        ]:
            with self.subTest(options=options):
                self.assert_json_result(self.run_manifest(options=options), code)
        result = subprocess.run([sys.executable, str(SCRIPT), '--json', '--validate-only'],
                                cwd=self.root, capture_output=True, timeout=20)
        self.assert_json_result(result, 'E_ARGUMENTS')

    def test_json_preflight_never_launches_runner(self):
        self.write()
        output = io.StringIO()
        with mock.patch.object(sys, 'argv', ['batch-manifest.py', '--json', '--validate-only',
                str(self.manifest), str(self.before)]), \
             mock.patch.object(manifest_module.subprocess, 'run') as runner, \
             contextlib.redirect_stdout(output):
            self.assertEqual(manifest_module.main(), 0)
        runner.assert_not_called()
        self.assertEqual(json.loads(output.getvalue())['pair_count'], 1)
        self.assertEqual(self.before.read_text(), 'id,value,time\n1,a,x\n')

    def test_json_flag_after_double_dash_is_literal_filename(self):
        self.write()
        literal = self.root / '--json'
        literal.write_bytes(self.manifest.read_bytes())
        result = subprocess.run([sys.executable, str(SCRIPT), '--validate-only', '--', '--json'],
                                cwd=self.root, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(result.stdout.startswith(b'Manifest valid: 1 pair(s);'))
        self.assertEqual(result.stderr, b'')

    def test_leading_bom_refusal_and_separate_copy_recovery(self):
        for newline in ('\n', '\r\n'):
            with self.subTest(newline=newline):
                raw = json.dumps(self.valid, indent=2).replace('\n', newline).encode()
                original = b'\xef\xbb\xbf' + raw
                self.manifest.write_bytes(original)
                for options in ((), ('--validate-only',)):
                    self.assert_refusal(self.run_manifest(options=options), 'E_BOM')
                copy = self.manifest.with_name('batch-no-bom.json')
                with copy.open('wb') as stream:
                    stream.write(original[3:])
                self.assertEqual(manifest_module.load_manifest(copy),
                    [str(self.before), str(self.after), 'id'])
                result = subprocess.run([sys.executable, str(SCRIPT), '--validate-only',
                    str(copy)], cwd=self.root, capture_output=True, timeout=20)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stderr, b'')
                self.assertFalse((self.root / 'reports').exists())
                report = self.root / ('recovered-' + str(len(newline)))
                result = subprocess.run([sys.executable, str(SCRIPT), str(copy), str(report)],
                    cwd=self.root, capture_output=True, timeout=20)
                self.assertEqual(result.returncode, 1)
                self.assertTrue((report / 'status.tsv').is_file())
                self.assertEqual(self.manifest.read_bytes(), original)

    def test_bom_diagnostic_is_fixed_and_not_content_dependent(self):
        cases = [b'\xef\xbb\xbf' + suffix for suffix in (
            b'', b'PRIVATE_SENTINEL', b'\xef\xbb\xbf{}', b'[' * 40)]
        for raw in cases:
            self.manifest.write_bytes(raw)
            for options in ((), ('--validate-only',)):
                self.assert_refusal(self.run_manifest(options=options), 'E_BOM')
        # Byte limits and UTF-8 decoding retain precedence over BOM detection.
        self.manifest.write_bytes(b'\xef\xbb\xbf' + b' ' * 65536)
        self.assert_refusal(self.run_manifest(), 'E_SIZE')
        self.manifest.write_bytes(b'\xef\xbb\xbf\xff')
        self.assert_refusal(self.run_manifest(), 'E_ENCODING')
        self.manifest.write_bytes(b' \xef\xbb\xbf{}')
        self.assert_refusal(self.run_manifest(), 'E_JSON')
        self.valid['pairs'][0]['key'] = 'literal\ufeffkey'
        self.write()
        self.assertEqual(manifest_module.load_manifest(self.manifest)[-1], 'literal\ufeffkey')

    def test_fixed_actionable_refusal_codes(self):
        pair = self.valid['pairs'][0]
        cases = [
            (b'\xff', 'E_ENCODING'), (b'{', 'E_JSON'),
            (b'{"version":NaN,"pairs":[]}', 'E_JSON'),
            (b'[' * 2000 + b']' * 2000, 'E_DEPTH'),
            (b' ' * 65537, 'E_SIZE'),
            (b'{"version":1,"version":1,"pairs":[]}', 'E_DUPLICATE'),
            (b'{"version":1,"pairs":[{"before":"a","before":"b"}]}', 'E_DUPLICATE'),
            (json.dumps(dict(self.valid, secret='PRIVATE_SENTINEL')).encode(), 'E_SCHEMA'),
            (json.dumps(dict(self.valid, version=True)).encode(), 'E_VERSION'),
            (json.dumps(dict(self.valid, pairs=[])).encode(), 'E_PAIRS'),
            (json.dumps(dict(self.valid, pairs=[pair, {}])).encode(), 'E_PAIR'),
            (json.dumps(dict(self.valid, pairs=[dict(pair, key='PRIVATE_SENTINEL\n')])).encode(), 'E_TEXT'),
        ]
        for raw, code in cases:
            with self.subTest(code=code):
                self.manifest.write_bytes(raw)
                for options in ((), ('--validate-only',)):
                    self.assert_refusal(self.run_manifest(options=options), code)
        self.manifest.unlink()
        self.assert_refusal(self.run_manifest(), 'E_READ')
        self.manifest.mkdir()
        self.assert_refusal(self.run_manifest(), 'E_FILE')
        self.manifest.rmdir()
        import os
        os.mkfifo(self.manifest)
        self.assert_refusal(self.run_manifest(), 'E_FILE')
        self.manifest.unlink()
        self.write()
        for options, code in [
            (('--max-input-bytes', '0'), 'E_BUDGET'),
            (('--max-input-bytes', 'PRIVATE_SENTINEL'), 'E_ARGUMENTS'),
            (('--PRIVATE_SENTINEL',), 'E_ARGUMENTS'),
            (('--ignore-column', 'PRIVATE_SENTINEL\n'), 'E_TEXT'),
        ]:
            with self.subTest(options=options):
                self.assert_refusal(self.run_manifest(options=options), code)

    def test_nesting_budget_and_quoted_brackets(self):
        # Exactly 32 structural levels parse, then fail the top-level schema.
        self.manifest.write_bytes(b'[' * 32 + b']' * 32)
        self.assert_refusal(self.run_manifest(), 'E_SCHEMA')
        self.manifest.write_bytes(b'[' * 33 + b']' * 33)
        self.assert_refusal(self.run_manifest(), 'E_DEPTH')
        # Brackets and escaped quotes/backslashes in strings do not count.
        key = '[{' * 100 + '"' + chr(92) + '}]' * 100
        self.valid['pairs'][0]['key'] = key
        self.write()
        self.assertEqual(manifest_module.load_manifest(self.manifest)[-1], key)

    def test_runner_launch_error_is_fixed_and_does_not_create_reports(self):
        self.write()
        errors = io.StringIO()
        with mock.patch.object(sys, 'argv', ['batch-manifest.py', str(self.manifest), str(self.root/'reports')]), \
             mock.patch.object(manifest_module.subprocess, 'run', side_effect=OSError('PRIVATE_SENTINEL')), \
             contextlib.redirect_stderr(errors):
            self.assertEqual(manifest_module.main(), 2)
        self.assertEqual(errors.getvalue(), 'Cannot run manifest [E_RUNNER]: ' +
                         manifest_module.REASONS['E_RUNNER'] + '\n')
        self.assertFalse((self.root/'reports').exists())

    def test_equivalence_and_literal_paths(self):
        self.valid['pairs'] += [dict(self.valid['pairs'][0], after=self.before.name),
                               dict(self.valid['pairs'][0], before='missing.csv'),
                               dict(self.valid['pairs'][0], after=self.before.name)]
        self.write()
        for options in ((), ('--totals',), ('--totals', '--ignore-column', 'time')):
            with self.subTest(options=options):
                n=str(len(options))
                result=self.run_manifest('manifest'+n, options)
                triples=manifest_module.load_manifest(self.manifest)
                direct=subprocess.run(['sh',str(ROOT/'evaluation/batch-review.sh'),*options,'--','direct'+n,*triples],
                                      cwd=self.root,capture_output=True,timeout=20)
                self.assertEqual(result.returncode,2)
                self.assertEqual(result.returncode,direct.returncode)
                for a in (self.root/('manifest'+n)).iterdir():
                    b=self.root/('direct'+n)/a.name
                    self.assertTrue(b.exists(),a.name)
                    self.assertEqual(a.read_bytes(),b.read_bytes(),a.name)
                statuses=(self.root/('manifest'+n)/'status.tsv').read_text()
                self.assertEqual([r.split('\t')[1] for r in statuses.splitlines()[1:]], ['1','0','2','0'])
        self.assertFalse((self.root/'NEVER').exists())
        self.assertFalse((self.data/'NEVER').exists())

    def test_exact_key_and_whitespace(self):
        for i,key in enumerate((' id ', '-id', '識別子', '$(touch NEVER)')):
            with self.subTest(key=key):
                self.before.write_text(key+',value\n1,a\n',encoding='utf-8')
                self.after.write_text(key+',value\n1,b\n',encoding='utf-8')
                self.valid['pairs'][0]['key']=key
                self.write()
                result=self.run_manifest('exact'+str(i))
                self.assertEqual(result.returncode,1,result.stderr)
                report=json.loads((self.root/('exact'+str(i))/'pair-0001.json').read_text())
                self.assertEqual(report['counts']['changed'],1)
                self.assertEqual(manifest_module.load_manifest(self.manifest)[-1],key)

    def test_invalid_schema_creates_no_reports(self):
        cases=[{},[],None,{'version':True,'pairs':self.valid['pairs']},
               {'version':2,'pairs':self.valid['pairs']},dict(self.valid,command='touch NEVER'),
               dict(self.valid,pairs=[]),dict(self.valid,pairs=self.valid['pairs']*101)]
        for field in ('before','after','key'):
            for value in ('',None,False,[], 'x\n', 'x\x00','\ud800'):
                cases.append(dict(self.valid,pairs=[dict(self.valid['pairs'][0],**{field:value})]))
            pair=dict(self.valid['pairs'][0]);del pair[field]
            cases.append(dict(self.valid,pairs=[pair]))
        cases.append(dict(self.valid,pairs=[dict(self.valid['pairs'][0],extra=1)]))
        # Full validation must reject a bad later pair before executing the first.
        cases.append(dict(self.valid,pairs=self.valid['pairs']+[{}]))
        for data in cases:
            with self.subTest(data=data):
                self.manifest.write_text(json.dumps(data),encoding='utf-8')
                result=self.run_manifest()
                self.assert_refusal(result)

    def test_invalid_encoding_duplicates_depth_size_and_special_files(self):
        cases=[b'\xff', b'{', b'{"version":1,"version":1,"pairs":[]}',
               b'{"version":1,"pairs":[{"before":"x","before":"y","after":"z","key":"id"}]}',
               b'['*2000+b']'*2000,b' '*65537,
               b'{"version":NaN,"pairs":[]}']
        for raw in cases:
            self.manifest.write_bytes(raw)
            self.assert_refusal(self.run_manifest())
        self.manifest.unlink()
        self.assert_refusal(self.run_manifest(), 'E_READ')
        self.manifest.mkdir()
        self.assert_refusal(self.run_manifest(), 'E_FILE')
        self.manifest.rmdir()
        import os
        os.mkfifo(self.manifest)
        self.assert_refusal(self.run_manifest(), 'E_FILE')

    def test_manifest_limits_and_path_resolution(self):
        self.valid['pairs'] *= 100
        self.write()
        self.assertEqual(len(manifest_module.load_manifest(self.manifest)),300)
        raw=self.manifest.read_bytes()
        self.manifest.write_bytes(raw+b' '*(65536-len(raw)))
        self.assertEqual(len(manifest_module.load_manifest(self.manifest)),300)
        self.manifest.write_bytes(self.manifest.read_bytes()+b' ')
        with self.assertRaises(ValueError):
            manifest_module.load_manifest(self.manifest)
        self.valid['pairs']=self.valid['pairs'][:1]
        self.valid['pairs'][0]['before']='../data space/'+self.before.name
        self.valid['pairs'][0]['after']=str(self.after)
        self.write()
        self.assertEqual(self.run_manifest().returncode,1)
        # A relative manifest argument and a relative output have separate bases.
        result=subprocess.run([sys.executable,str(SCRIPT),'data space/batch.json','relative reports'],
                              cwd=self.root,capture_output=True,timeout=20)
        self.assertEqual(result.returncode,1,result.stderr)
        self.assertTrue((self.root/'relative reports/status.tsv').is_file())

    def test_symlink_base_and_no_expansion(self):
        self.write()
        link=self.root/'linked.json'
        link.symlink_to(self.manifest)
        triples=manifest_module.load_manifest(link)
        self.assertEqual(triples[0],str(self.root/self.before.name))
        self.valid['pairs'][0]['before']='~/literal-$HOME-*.csv'
        self.write()
        self.assertEqual(manifest_module.load_manifest(self.manifest)[0],
                         str(self.data/'~/literal-$HOME-*.csv'))
        self.assertEqual(self.run_manifest().returncode,2)
        self.assertEqual((self.root/'reports/status.tsv').read_text().splitlines()[1].split('\t')[1],'2')

    def test_exit_codes_budget_and_existing_output(self):
        self.write()
        self.assertEqual(self.run_manifest().returncode,1)
        self.assertEqual(self.run_manifest().returncode,2)
        self.assertEqual(self.run_manifest('small',('--max-input-bytes','1')).returncode,2)
        for value in ('0','10485761','bad'):
            self.assertEqual(self.run_manifest('invalid',('--max-input-bytes',value)).returncode,2)
            self.assertFalse((self.root/'invalid').exists())
        self.valid['pairs'][0]['after']=str(self.before)
        self.write()
        self.assertEqual(self.run_manifest('equal').returncode,0)


if __name__=='__main__':
    unittest.main()
