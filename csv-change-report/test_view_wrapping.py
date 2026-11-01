"""Synthetic text integrity and inert wrapping regressions; no browser claims."""
import copy
from html.parser import HTMLParser
import json
from pathlib import Path
import unittest
import view_report

class Parse(HTMLParser):
    def __init__(self, html):
        super().__init__(); self.text=[]; self.tags=[]; self.feed(html)
    def handle_data(self, text): self.text.append(text)
    def handle_starttag(self, tag, attrs): self.tags.append((tag,dict(attrs)))

class WrappingTests(unittest.TestCase):
    def setUp(self):
        self.report=json.loads((Path(__file__).parent/'examples/expected-report.json').read_text())
    def test_hashes_retain_exact_text_without_css_or_script(self):
        p=Parse(view_report.render(self.report))
        for name in ('before_sha256','after_sha256'):
            self.assertIn(self.report[name], ''.join(p.text))
        self.assertEqual(sum(t=='wbr' for t,a in p.tags),4)
        self.assertFalse(any(t in ('script','style','link','iframe') for t,a in p.tags))
        self.assertTrue(all(not a for t,a in p.tags if t=='wbr'))
        csp=next(a['content'] for t,a in p.tags if t=='meta' and a.get('http-equiv')=='Content-Security-Policy')
        self.assertEqual(csp,"default-src 'none'; base-uri 'none'; form-action 'none'")
    def test_untrusted_labels_roundtrip_at_chunk_boundaries(self):
        for label in ('X'*23+'<script>alert(1)</script>&"', 'A'*24+'&amp;<wbr>', '  first  '+ 'Y'*96+' last  ', '列é🧪e\u0301'*40, 'tab\tline\n'+'Z'*80):
            with self.subTest(label=repr(label)):
                r=copy.deepcopy(self.report)
                r['changed_cells_by_column']={label:1}
                r['changed_records'][0]['columns']=[label]
                r['ignored_columns']=[label+' ignored']
                p=Parse(view_report.render(r))
                self.assertIn(label, ''.join(p.text))
                self.assertIn(label+' ignored', ''.join(p.text))
                self.assertFalse(any(t in ('script','img','style','iframe') for t,a in p.tags))
                self.assertFalse(any(k.startswith('on') or k in ('src','href','style') for t,a in p.tags for k in a))
    def test_counts_only_keeps_metadata_and_hides_positions(self):
        html=view_report.render(self.report,counts_only=True)
        self.assertIn('Counts-only view:',html)
        self.assertNotIn('<h3>Changed records</h3>',html)
        self.assertIn(self.report['before_sha256'],''.join(Parse(html).text))

    def test_unicode_graphemes_are_not_split(self):
        label='é🧪e\u0301'*40
        self.report['changed_cells_by_column']={label:1}
        self.report['changed_records'][0]['columns']=[label]
        html=view_report.render(self.report)
        self.assertIn('<td>'+label+'</td>',html)
