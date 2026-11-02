"""Synthetic static navigation contracts; no browser interaction claim."""
import copy,json,unittest
from pathlib import Path
from html.parser import HTMLParser
import view_report
class Document(HTMLParser):
 def __init__(self,s):
  super().__init__();self.tags=[];self.feed(s)
 def handle_starttag(self,t,a):self.tags.append((t,dict(a)))
class NavigationTests(unittest.TestCase):
 def test_modes_and_optional_sections_have_exact_unique_targets(self):
  base=json.loads((Path(__file__).parent/'examples/expected-report.json').read_text())
  for summary in (False,True):
   for counts in (False,True):
    for sources in (False,True):
     for ignored in (False,True):
      with self.subTest(summary=summary,counts=counts,sources=sources,ignored=ignored):
       r=copy.deepcopy(base)
       if summary:
        r['format_version']=2;r['report_mode']='summary'
        for k in ('added_after_records','removed_before_records','changed_records'):del r[k]
       if ignored:r['ignored_columns']=['<a href="https://invalid.example">untrusted</a>']
       s=view_report.render(r,counts,sources);p=Document(s)
       ids=[a['id'] for t,a in p.tags if 'id' in a];links=[a['href'] for t,a in p.tags if t=='a']
       self.assertEqual(len(ids),len(set(ids)));self.assertEqual(links,['#'+i for i in ids])
       self.assertEqual(sum(t=='nav' and a.get('aria-label')=='Report sections' for t,a in p.tags),1)
       self.assertEqual('retained-inputs' in ids,sources);self.assertEqual('ignored-columns' in ids,ignored)
       self.assertEqual('changed-records' in ids,not summary and not counts)
       self.assertFalse(any(t in ('script','style','iframe','img','link') or any(k.startswith('on') or k in ('src','style','tabindex') for k in a) for t,a in p.tags))
       self.assertIn("default-src &#39;none&#39;; base-uri &#39;none&#39;; form-action &#39;none&#39;",s)
