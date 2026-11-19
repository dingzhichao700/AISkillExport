import hashlib,json,tempfile,threading,time,unittest
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from unittest.mock import patch
import remote_verify as v

class Tests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
  self.objects={'a':b'abc','b':b'def'};self.no_etag=False;self.omit304=False;self.active=0;self.peak=0;self.lock=threading.Lock();self.requests=[]
  outer=self
  class Handler(BaseHTTPRequestHandler):
   def log_message(self,*args):pass
   def do_GET(self):
    key=self.path.split('?')[0][1:]
    with outer.lock:outer.active+=1;outer.peak=max(outer.peak,outer.active);outer.requests.append((key,self.headers.get('If-None-Match')))
    try:
     time.sleep(.015)
     if key not in outer.objects:self.send_response(404);self.end_headers();return
     data=outer.objects[key];etag='"'+hashlib.sha256(data).hexdigest()+'"'
     same=self.headers.get('If-None-Match')==etag
     self.send_response(304 if same else 200)
     if not outer.no_etag and not (same and outer.omit304):self.send_header('ETag',etag)
     self.end_headers()
     if not same:self.wfile.write(data)
    finally:
     with outer.lock:outer.active-=1
  self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler);self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();self.url='http://127.0.0.1:'+str(self.server.server_port)+'/'
  for k,b in self.objects.items():(self.root/k).write_bytes(b)
 def tearDown(self):self.server.shutdown();self.server.server_close();self.temp.cleanup()
 def verify(self,action='stage',previous=None,workers=4):
  return v.verify_files([f.name for f in self.root.iterdir() if f.name in ('a','b')],self.root,self.url,action,lambda k,p:self.objects.update({k:p.read_bytes()}),previous,workers)
 def stage(self):return {r['key']:r for r in self.verify()[0]}
 def test_full_then_reuse(self):
  old=self.stage();rows,stats=self.verify('activate',old);self.assertEqual(stats['conditionalReused'],2);self.assertEqual(stats['downloadedBytes'],0)
 def test_mutation_blocks(self):
  old=self.stage();self.objects['a']=b'bad'
  with self.assertRaises(ValueError):self.verify('activate',old)
 def test_missing_blocks_activation(self):
  old=self.stage();del self.objects['a']
  with self.assertRaises(ValueError):self.verify('activate',old)
 def test_upload_missing_and_read_back(self):
  del self.objects['a'];self.verify();self.assertEqual(self.objects['a'],b'abc')
 def test_missing_etag_full_fallback(self):
  self.no_etag=True;old=self.stage();self.assertEqual(self.verify('activate',old)[1]['fullDownloads'],2)
 def test_missing_304_validator_full_fallback(self):
  old=self.stage();self.omit304=True;self.assertEqual(self.verify('activate',old)[1]['fullDownloads'],2)
 def test_changed_local_cannot_reuse(self):
  old=self.stage();(self.root/'a').write_bytes(b'new')
  with self.assertRaises(ValueError):self.verify('activate',old)
 def test_no_receipt_no_reuse(self):self.assertEqual(self.verify('activate')[1]['fullDownloads'],2)
 def test_weak_etag_rejected(self):self.assertIsNone(v.strong_etag('W/"abc"'));self.assertIsNone(v.strong_etag('bad\r\nvalue'))
 def test_bounded_parallel(self):
  self.verify(workers=99);self.assertGreater(self.peak,1);self.assertLessEqual(self.peak,4)
 def test_corrupt_receipt_falls_back(self):
  f=self.root/'receipt.json';f.write_text('{}');self.assertEqual(v.trusted_stage({'evidence':str(f),'sha256':'0'*64},'t',self.url,'b','r'),{})
 def test_receipt_identity_and_hash(self):
  f=self.root/'receipt.json';r={'transactionId':'t','publicRoot':self.url,'baseVersion':'base','release':'r','action':'stage','files':list(self.stage().values())};f.write_text(json.dumps(r));step={'evidence':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
  self.assertEqual(len(v.trusted_stage(step,'t',self.url,'base','r')),2)
  self.assertEqual(v.trusted_stage(step,'other',self.url,'base','r'),{})
 def test_duplicate_receipt_keys_rejected(self):
  f=self.root/'receipt.json';r={'transactionId':'t','publicRoot':self.url,'baseVersion':'base','release':'r','action':'stage','files':[{'key':'a'},{'key':'a'}]};f.write_text(json.dumps(r));self.assertEqual(v.trusted_stage({'evidence':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()},'t',self.url,'base','r'),{})
 def test_unrequested_304_rejected(self):
  with patch.object(v,'get_object',return_value=(304,b'','"a"')):
   with self.assertRaises(ValueError):self.verify()

if __name__=='__main__':unittest.main()
