import datetime as dt
import importlib.util
from pathlib import Path
import unittest
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
 def test_nonfeed(self):
  with self.assertRaises(ValueError): c.parse_feed(b'<html><body>Access denied</body></html>',SOURCE,NOW)
 def test_malformed(self):
  with self.assertRaises(Exception): c.parse_feed(b'invalid',SOURCE,NOW)
if __name__=='__main__': unittest.main()
