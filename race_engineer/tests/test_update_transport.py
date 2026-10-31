import unittest,tempfile,hashlib,io,threading
from pathlib import Path
from unittest.mock import patch
from engineer import updater
URL='https://release.example/stable.json'
def response(raw):return io.BytesIO(raw)
def fixture():
 chunks=[b'MZ'+b'a'*2048,b'b'*2048,b'c'*1024];whole=b''.join(chunks)
 manifest=dict(product='RaceEngineer',platform='windows-x64',version='0.14.0',size=len(whole),sha256=hashlib.sha256(whole).hexdigest(),chunks=[dict(url=f'https://release.example/{n}.bin',size=len(raw),sha256=hashlib.sha256(raw).hexdigest()) for n,raw in enumerate(chunks)])
 return manifest,chunks,whole
class UpdateTransportTests(unittest.TestCase):
 def test_download_chunks_and_reuse_verified_cache(self):
  manifest,chunks,whole=fixture();seen=[]
  def open_url(url,**kw):seen.append(url);return response(chunks[int(url.split('/')[-1].split('.')[0])])
  with tempfile.TemporaryDirectory() as folder,patch('engineer.updater.opener') as op:
   op.return_value.open.side_effect=open_url
   path=updater.download(manifest,folder,URL);self.assertEqual(path.read_bytes(),whole);self.assertEqual(len(seen),3)
   path.unlink();seen.clear();path=updater.download(manifest,folder,URL);self.assertEqual(path.read_bytes(),whole);self.assertFalse(seen)
 def test_resume_after_connection_failure(self):
  manifest,chunks,whole=fixture();seen=[]
  with tempfile.TemporaryDirectory() as folder,patch('engineer.updater.opener') as op:
   op.return_value.open.side_effect=[response(chunks[0]),OSError('connection lost')]
   with self.assertRaises(OSError):updater.download(manifest,folder,URL)
   self.assertFalse(list(Path(folder).glob('*.exe')))
   op.return_value.open.side_effect=[response(chunks[1]),response(chunks[2])]
   self.assertEqual(updater.download(manifest,folder,URL).read_bytes(),whole)
   self.assertEqual(op.return_value.open.call_count,4)
 def test_changed_cached_chunk_is_downloaded_again(self):
  manifest,chunks,whole=fixture()
  with tempfile.TemporaryDirectory() as folder,patch('engineer.updater.opener') as op:
   op.return_value.open.side_effect=[response(v) for v in chunks];path=updater.download(manifest,folder,URL);path.unlink()
   cached=next(Path(folder).rglob('000-*.bin'));cached.write_bytes(b'x'*len(chunks[0]))
   op.return_value.open.side_effect=[response(chunks[0])];self.assertEqual(updater.download(manifest,folder,URL).read_bytes(),whole)
 def test_mismatched_whole_hash_never_publishes_executable(self):
  manifest,chunks,whole=fixture();manifest['sha256']='0'*64
  with tempfile.TemporaryDirectory() as folder,patch('engineer.updater.opener') as op:
   op.return_value.open.side_effect=[response(v) for v in chunks]
   with self.assertRaises(ValueError):updater.download(manifest,folder,URL)
   self.assertFalse(list(Path(folder).glob('*.exe')))
 def test_rejects_bad_chunk_origins_sizes_and_totals(self):
  manifest,chunks,_=fixture()
  for change in [dict(url='https://other.example/a'),dict(size=0),dict(size=True),dict(sha256='bad')]:
   m={**manifest,'chunks':[{**manifest['chunks'][0],**change},*manifest['chunks'][1:]]}
   with self.assertRaises(ValueError):updater.validate_manifest(m,URL)
 def test_cancellation_keeps_previous_install_untouched(self):
  manifest,_,_=fixture();stop=threading.Event();stop.set()
  with tempfile.TemporaryDirectory() as folder:
   old=Path(folder)/'old.exe';old.write_bytes(b'MZold')
   with self.assertRaises(InterruptedError):updater.download(manifest,folder,URL,cancel=stop)
   self.assertEqual(old.read_bytes(),b'MZold');self.assertFalse(list(Path(folder).glob('*.part')))
 def test_login_page_is_not_a_release(self):
  with patch('engineer.updater.opener') as op:
   op.return_value.open.return_value=response(b'<html>Sign in</html>')
   with self.assertRaisesRegex(ValueError,'requires sign-in'):updater.check(URL)
