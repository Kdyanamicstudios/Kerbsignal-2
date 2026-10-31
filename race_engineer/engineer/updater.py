"""Pinned HTTPS release feed, verified resumable chunks, install after app exit."""
import hashlib,json,os,re,ssl,subprocess,sys,urllib.request,urllib.parse
from pathlib import Path

VERSION='0.16.0'
RELEASE_MANIFEST='https://kerbsignal-releases.fairylyric19.chatgpt.site/stable.json'
MAX_SIZE=1024*1024*1024
MAX_CHUNK=24*1024*1024

def version(value):
 if not isinstance(value,str) or not re.fullmatch(r'\d+\.\d+\.\d+',value):raise ValueError('Invalid release version')
 return tuple(map(int,value.split('.')))

def origin(url):
 p=urllib.parse.urlsplit(url)
 if p.scheme!='https' or not p.hostname or p.username or p.password or p.fragment:raise ValueError('Updates require a trusted HTTPS origin')
 return p.hostname.lower(),p.port or 443

class PinnedRedirect(urllib.request.HTTPRedirectHandler):
 def __init__(self,host):self.host=host
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  if origin(newurl)!=self.host:raise ValueError('Update redirect left the trusted release origin')
  return super().redirect_request(req,fp,code,msg,headers,newurl)

def opener(url):return urllib.request.build_opener(PinnedRedirect(origin(url)),urllib.request.HTTPSHandler(context=ssl.create_default_context()))

def validate_manifest(data,url):
 if not isinstance(data,dict) or data.get('product')!='RaceEngineer' or data.get('platform')!='windows-x64':raise ValueError('Release is for a different application or platform')
 version(data.get('version'));trusted=origin(url)
 if type(data.get('size')) is not int or not 1024<data['size']<=MAX_SIZE:raise ValueError('Installer size is invalid')
 if not re.fullmatch('[0-9a-f]{64}',str(data.get('sha256',''))):raise ValueError('Installer checksum is missing')
 chunks=data.get('chunks')
 if chunks is not None:
  if not isinstance(chunks,list) or not 1<=len(chunks)<=128:raise ValueError('Release chunk list is invalid')
  total=0
  for part in chunks:
   if not isinstance(part,dict) or origin(part.get('url',''))!=trusted:raise ValueError('Update chunk is outside the trusted origin')
   if type(part.get('size')) is not int or not 0<part['size']<=MAX_CHUNK:raise ValueError('Update chunk size is invalid')
   if not re.fullmatch('[0-9a-f]{64}',str(part.get('sha256',''))):raise ValueError('Update chunk checksum is missing')
   total+=part['size']
  if total!=data['size']:raise ValueError('Release chunks do not match the advertised total size')
 elif origin(data.get('url',''))!=trusted:raise ValueError('Installer is outside the trusted release origin')
 return data

def check(url=None):
 url=RELEASE_MANIFEST if url is None else url
 if not url:return None
 with opener(url).open(url,timeout=20) as response:
  raw=response.read(65537)
 if len(raw)>65536:raise ValueError('Release manifest is too large')
 try:data=json.loads(raw)
 except (ValueError,UnicodeError) as exc:raise ValueError('Release feed is unavailable or requires sign-in. The installed app was kept.') from exc
 data=validate_manifest(data,url)
 return data if version(data['version'])>version(VERSION) else None

def matches(path,size,digest):
 path=Path(path)
 if not path.is_file() or path.stat().st_size!=size:return False
 result=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):result.update(block)
 return result.hexdigest()==digest

def _fetch(part,path,release_url,progress,completed,total,cancel):
 digest=hashlib.sha256();size=0;temporary=path.with_name(path.name+'.download')
 try:
  with opener(release_url).open(part['url'],timeout=30) as response,temporary.open('wb') as out:
   while True:
    if cancel and cancel.is_set():raise InterruptedError('Update download paused. Verified chunks will be reused next time.')
    block=response.read(1024*1024)
    if not block:break
    size+=len(block)
    if size>part['size']:raise ValueError('Installer exceeds the advertised size')
    out.write(block);digest.update(block)
    if progress:progress(completed+size,total)
  if size!=part['size'] or digest.hexdigest()!=part['sha256']:raise ValueError('Update verification failed. The installed version was kept.')
  os.replace(temporary,path)
 finally:temporary.unlink(missing_ok=True)

def download(data,folder,url=None,progress=None,cancel=None):
 url=RELEASE_MANIFEST if url is None else url
 validate_manifest(data,url);folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
 target=folder/('KerbSignal-'+data['version']+'.exe');part=folder/'installer.part'
 if matches(target,data['size'],data['sha256']):
  if progress:progress(data['size'],data['size'])
  return target
 chunks=data.get('chunks')
 try:
  if chunks:
   cache=folder/(data['version']+'-'+data['sha256'][:16]);cache.mkdir(exist_ok=True)
   completed=0;paths=[]
   for i,chunk in enumerate(chunks):
    if cancel and cancel.is_set():raise InterruptedError('Update download paused. Verified chunks will be reused next time.')
    path=cache/(f'{i:03d}-'+chunk['sha256']+'.bin')
    if not matches(path,chunk['size'],chunk['sha256']):_fetch(chunk,path,url,progress,completed,data['size'],cancel)
    completed+=chunk['size'];paths.append(path)
    if progress:progress(completed,data['size'])
   with part.open('wb') as out:
    for path in paths:
     with path.open('rb') as src:
      for block in iter(lambda:src.read(1024*1024),b''):
       if cancel and cancel.is_set():raise InterruptedError('Update assembly paused. Verified chunks will be reused next time.')
       out.write(block)
  else:
   _fetch(data,part,url,progress,0,data['size'],cancel)
  if not matches(part,data['size'],data['sha256']):raise ValueError('Update verification failed. The installed version was kept.')
  with part.open('rb') as f:
   if f.read(2)!=b'MZ':raise ValueError('Download is not a Windows executable')
  os.replace(part,target)
  return target
 finally:part.unlink(missing_ok=True)

def launch_when_closed(path):
 if sys.platform!='win32':raise OSError('Installing updates requires Windows')
 import base64
 encoded_path=str(Path(path).resolve()).replace("'","''")
 script=f"$ErrorActionPreference='Stop'; $p=Get-Process -Id {os.getpid()} -ErrorAction SilentlyContinue; if($p){{$p.WaitForExit()}}; Start-Process -FilePath '{encoded_path}' -Wait"
 encoded=base64.b64encode(script.encode('utf-16-le')).decode('ascii')
 subprocess.Popen(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',encoded],creationflags=0x08000000)
