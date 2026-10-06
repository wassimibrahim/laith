import datetime as dt
import importlib.util
from pathlib import Path
import unittest
import tempfile, json
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('collect',Path(__file__).parents[1]/'scripts/collect.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
NOW=dt.datetime(2026,10,6,12,tzinfo=dt.timezone.utc)
SOURCE={'id':'ports','name':'Test','sector':'Ports & logistics','region':'Europe'}
class CollectorTests(unittest.TestCase):
 def test_canonical(self):
  self.assertEqual(c.canonical('https://EXAMPLE.com/a/?utm_source=x&b=2#thing'),'https://example.com/a?b=2')
  with self.assertRaises(ValueError): c.canonical('javascript:alert(1)')
 def test_rss(self):
  rows=c.parse_feed(b'<rss><channel><item><title>Port investment &amp; automation</title><link>https://example.com/a</link><pubDate>Tue, 06 Oct 2026 09:00:00 GMT</pubDate></item></channel></rss>',SOURCE,NOW)
  self.assertEqual(len(rows),1);self.assertEqual(rows[0]['kind'],'Innovation');self.assertIsNone(rows[0]['value']);self.assertEqual(rows[0]['status'],'Unverified')
 def test_atom(self):
  rows=c.parse_feed(b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Port loan</title><link href="https://example.com/b"/><updated>2026-10-06T07:00:00Z</updated></entry></feed>',SOURCE,NOW)
  self.assertEqual(rows[0]['url'],'https://example.com/b')
 def test_dates(self):
  old=b'<rss><channel><item><title>Old</title><link>https://example.com/a</link><pubDate>2025-01-01T00:00:00Z</pubDate></item></channel></rss>'
  self.assertEqual(c.parse_feed(old,SOURCE,NOW),[])
  self.assertIsNone(c.parse_feed(old.replace(b'2025-01-01T00:00:00Z',b'invalid'),SOURCE,NOW)[0]['publishedAt'])
 def test_merge(self):
  row={'id':'a','url':'https://example.com/a','title':'Port deal','firstSeen':'2026-10-01','lastSeen':'2026-10-01','channels':['a']}
  new={**row,'firstSeen':'2026-10-06','lastSeen':'2026-10-06','channels':['b']}
  result=c.merge([row],[new]);self.assertEqual(len(result),1);self.assertEqual(result[0]['firstSeen'],'2026-10-01');self.assertEqual(result[0]['channels'],['a','b'])
  self.assertEqual(len(c.merge(result,[{**new,'id':'b','url':'https://another.example/a'}])),1)
 def test_publisher_name_and_airports_do_not_imply_port_innovation(self):
  xml=b'<rss><channel><item><title>Airport acquisition - SMI DIGITAL</title><source>SMI DIGITAL</source><link>https://example.com/a</link></item></channel></rss>'
  row=c.parse_feed(xml,{**SOURCE,'sector':'Transport'},NOW)[0]
  self.assertEqual(row['title'],'Airport acquisition');self.assertEqual(row['kind'],'Deal lead');self.assertEqual(row['sector'],'Transport')
 def test_total_outage_preserves_archive_and_reports_failure(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'data').mkdir();(root/'reports').mkdir()
   (root/'data/sources.json').write_text(json.dumps([SOURCE]))
   row={'id':'old','url':'https://example.com/old','title':'Prior port deal','firstSeen':'2026-10-06T00:00:00+00:00','publishedAt':'2026-10-06T00:00:00+00:00','score':80,'sector':'Ports & logistics','publisher':'Test','evidence':'Unverified'}
   (root/'data/feed.json').write_text(json.dumps([row]))
   with patch.object(c,'ROOT',root),patch.object(c,'fetch',return_value=([],{**SOURCE,'state':'error','count':0,'error':'outage'})),patch('sys.argv',['collect.py']):
    self.assertEqual(c.main(),2)
   self.assertEqual(json.loads((root/'data/feed.json').read_text()),[row])
   self.assertEqual(json.loads((root/'data/health.json').read_text())['successful'],0)
   self.assertTrue((root/'data/daily.json').exists())
 def test_nonfeed(self):
  with self.assertRaises(ValueError): c.parse_feed(b'<html><body>Access denied</body></html>',SOURCE,NOW)
 def test_malformed(self):
  with self.assertRaises(Exception): c.parse_feed(b'invalid',SOURCE,NOW)
if __name__=='__main__': unittest.main()
