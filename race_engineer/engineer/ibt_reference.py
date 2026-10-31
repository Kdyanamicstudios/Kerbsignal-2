"""Read-only native IBT import using recorded SDK time and identity.
Binary layout checked against the primary pyirsdk IBT reader:
https://github.com/kutu/pyirsdk/blob/master/irsdk.py
No simulator control, uploads, executable content or third-party lap library.
"""
from pathlib import Path
import mmap,struct,math
from .sdk import FORMATS,WANTED,metadata
from .core import Coach,reference_payload,supported

REQUIRED={'SessionTime','LapDistPct','Speed','Brake','Throttle','SteeringWheelAngle','Lap','SessionNum','PlayerCarIdx','OnPitRoad','IsOnTrack','PlayerTrackSurface'}

def import_ibt(path,target=None,cancel=None,progress=None):
 path=Path(path)
 if not 144<=path.stat().st_size<=4*1024**3:raise ValueError('IBT file size is unsupported.')
 with path.open('rb') as source,mmap.mmap(source.fileno(),0,access=mmap.ACCESS_READ) as raw:
  header=struct.unpack_from('<12i',raw)
  version,_,rate,_,slen,soff,nvars,voff,nbuf,stride=header[:10]
  records=struct.unpack_from('<i',raw,140)[0];start=struct.unpack_from('<i',raw,52)[0]
  if not 1<=version<=10 or not 1<=rate<=1000 or not 1<=nvars<=3000 or not 1<=nbuf<=4:raise ValueError('Invalid IBT header.')
  if not 0<slen<=4*1024**2 or not 144<=soff<len(raw) or soff+slen>len(raw):raise ValueError('Invalid IBT session information bounds.')
  if not 144<=voff<len(raw) or voff+nvars*144>len(raw):raise ValueError('Invalid IBT variable table bounds.')
  if not 16<=stride<=1024*1024 or not 100<=records<=10_000_000 or start<144 or start+records*stride>len(raw):raise ValueError('IBT recording is incomplete or has invalid record bounds.')
  schema={}
  for n in range(nvars):
   offset=voff+n*144;typ,pos,count=struct.unpack_from('<iii',raw,offset)
   name=raw[offset+16:offset+48].split(b'\0',1)[0].decode('ascii','replace')
   if name not in WANTED or count!=1:continue
   if typ not in FORMATS or typ==0:continue
   fmt='<'+FORMATS[typ];size=struct.calcsize(fmt)
   if pos<0 or pos+size>stride:raise ValueError('IBT variable extends beyond its record.')
   if name in schema:raise ValueError('Duplicate IBT variable name.')
   schema[name]=(fmt,pos)
  missing=REQUIRED-set(schema)
  if missing:raise ValueError('IBT lacks required validation channels: '+', '.join(sorted(missing)))
  if not {'PlayerCarMyIncidentCount','PlayerCarDriverIncidentCount'}&set(schema):raise ValueError('IBT has no incident counter; clean-lap validation is unavailable.')
  text=raw[soff:soff+slen].rstrip(b'\0').decode('utf-8',errors='replace')
  coach=Coach();best=None;profile=None;identity=None;last_time=None;last_p=None
  complete=clean=0
  for i in range(records):
   if cancel and cancel.is_set():raise InterruptedError('IBT import canceled.')
   base=start+i*stride
   d={name:struct.unpack_from(fmt,raw,base+pos)[0] for name,(fmt,pos) in schema.items()}
   if any(isinstance(d[k],float) and not math.isfinite(d[k]) for k in REQUIRED):raise ValueError('IBT contains non-finite driving telemetry.')
   d={k:(None if isinstance(v,float) and not math.isfinite(v) else v) for k,v in d.items()}
   if not 0<=d['LapDistPct']<=1 and (not d['IsOnTrack'] or d['OnPitRoad']):
       coach.active=False;coach.previous=None;coach.samples=[];continue
   if not 0<=d['LapDistPct']<=1 or not 0<=d['Brake']<=1 or not 0<=d['Throttle']<=1 or not 0<=d['Speed']<150:raise ValueError('IBT driving input is outside expected bounds.')
   current=(d['SessionNum'],d['PlayerCarIdx'])
   if current!=identity:
    profile=metadata(text,d['PlayerCarIdx'],d['SessionNum']);identity=current;coach=Coach();last_time=last_p=None
    if not supported(profile):raise ValueError('IBT does not identify its car and exact layout.')
    if target and any(str(profile.get(k,''))!=str(target.get(k,'')) for k in ('car_path','car_id','track_id','config')):raise ValueError('IBT car or exact layout does not match the connected session.')
    if target and abs(profile['length']-target.get('length',0))>5:raise ValueError('IBT track length does not match the connected layout.')
   if last_time is not None and d['SessionTime']<=last_time:raise ValueError('IBT timestamps reset or do not advance.')
   last_time=d['SessionTime']
   lap,_=coach.update(d,profile)
   if lap:
    complete+=1
    if lap['clean']:
     clean+=1
     if best is None or lap['lap_time']<best['lap_time']:
      best=reference_payload(lap,dict(profile));best['label']='Native IBT clean lap; optimality unverified'
   if progress and i%10000==0:progress(i,records)
  if not best:raise ValueError('IBT contains no complete validated clean lap. Record through two start/finish crossings without incidents or off-track driving.')
  best['provenance']=dict(provider='Local iRacing IBT',file_name=path.name,derived_time=False,timing_source='recorded SessionTime',complete_laps=complete,clean_laps=clean)
  if progress:progress(records,records)
  return best
