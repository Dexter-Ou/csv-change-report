"""Static table naming regression across modes; not assistive-technology testing."""
import copy
from html.parser import HTMLParser
import json
from pathlib import Path
import unittest
import view_report

class Tables(HTMLParser):
    def __init__(self, html):
        super().__init__(); self.tables=[]; self.current=None; self.in_caption=False
        self.feed(html)
    def handle_starttag(self, tag, attrs):
        if tag=='table':
            self.current={'children':[], 'captions':[], 'headers':[]};self.tables.append(self.current)
        elif self.current is not None:
            self.current['children'].append(tag)
            if tag=='caption':self.in_caption=True;self.current['captions'].append('')
            if tag=='th':self.current['headers'].append(dict(attrs).get('scope'))
    def handle_data(self, data):
        if self.in_caption:self.current['captions'][-1]+=data
    def handle_endtag(self, tag):
        if tag=='caption':self.in_caption=False
        if tag=='table':self.current=None

class CaptionTests(unittest.TestCase):
    def test_named_tables_across_modes_and_empty_results(self):
        base=json.loads((Path(__file__).parent/'examples/expected-report.json').read_text())
        for summary in (False,True):
            for counts in (False,True):
                for empty in (False,True):
                    with self.subTest(summary=summary,counts=counts,empty=empty):
                        r=copy.deepcopy(base)
                        if empty:
                            r['counts']={'before':0,'after':0,'added':0,'removed':0,'changed':0,'unchanged':0}
                            r['changed_cells_by_column']={}
                            for k in ('added_after_records','removed_before_records','changed_records'):r[k]=[]
                        if summary:
                            r['format_version']=2;r['report_mode']='summary'
                            for k in ('added_after_records','removed_before_records','changed_records'):del r[k]
                        doc=Tables(view_report.render(r,counts_only=counts))
                        expected=['Record counts','Changed cells by column']
                        if not summary and not counts and not empty:
                            if r['added_after_records']:expected.append('Added positions in after CSV')
                            if r['removed_before_records']:expected.append('Removed positions in before CSV')
                            if r['changed_records']:expected.append('Changed records')
                        expected.append('Saved source hashes')
                        self.assertEqual([t['captions'] for t in doc.tables],[[name] for name in expected])
                        for t in doc.tables:
                            self.assertEqual(t['children'][0],'caption')
                            self.assertTrue(t['headers']);self.assertTrue(all(s=='col' for s in t['headers']))
