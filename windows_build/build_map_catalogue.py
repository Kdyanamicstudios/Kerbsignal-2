"""Convert Apache-2.0 SIMRacingApps track survey data into compact route data."""
from pathlib import Path
import json,gzip,math,xml.etree.ElementTree as ET,bisect
root=Path(__file__).resolve().parent
source=root/'third_party/SIMRacingApps_tracks';out=root.parent/'race_engineer/engineer/maps';out.mkdir(exist_ok=True)
def distance(a,b):
 r=6371000;la,lb=map(math.radians,(a[0],b[0]));dl=math.radians(b[0]-a[0]);dn=math.radians(b[1]-a[1]);v=math.sin(dl/2)**2+math.cos(la)*math.cos(lb)*math.sin(dn/2)**2
 return 2*r*math.asin(min(1,math.sqrt(v)))
def route(j):
 if j.get('ONTRACK'):
  pts=sorted((float(p)/100,float(v['Latitude']),float(v['Longitude'])) for p,v in j['ONTRACK'].items() if str(p).replace('.','',1).isdigit() and isinstance(v,dict) and 'Latitude' in v)
  return pts,'surveyed lap fraction'
 name=j.get('GPX',{}).get('ONTRACK')
 if not name or not (source/name).exists():return [],''
 tree=ET.parse(source/name);xy=[(float(v.attrib['lat']),float(v.attrib['lon'])) for v in tree.iter() if v.tag.split('}')[-1]=='rtept']
 if len(xy)<3:return [],''
 dd=[0.]
 for a,b in zip(xy,xy[1:]):dd.append(dd[-1]+distance(a,b))
 if dd[-1]<100:return [],''
 maxp=float(j.get('GPX',{}).get('maxPercent',100))/100
 return [(d/dd[-1]*maxp,*v) for d,v in zip(dd,xy)],'GPX distance estimate'
index={}
for path in source.glob('*.json'):
 if path.stem=='default':continue
 try:
  j=json.loads(path.read_text(encoding='utf-8-sig'))
  if 'Apache' not in j.get('License',''):continue
  pts,mode=route(j)
  if len(pts)<3:continue
  dense=[];ps=[p[0] for p in pts]
  for n in range(1001):
   p=n/1000;i=bisect.bisect_left(ps,p)
   if i==0 or i==len(pts):continue
   a,b=pts[i-1:i+1];f=(p-a[0])/(b[0]-a[0]) if b[0]>a[0] else 0
   dense.append([p,a[1]+f*(b[1]-a[1]),a[2]+f*(b[2]-a[2])])
  payload=dict(points=dense,source=mode,copyright=j.get('Copyright'),license=j['License'])
  filename=path.stem+'.json.gz'
  with gzip.open(out/filename,'wt') as f:json.dump(payload,f,separators=(',',':'))
  index[path.stem]=filename
 except (ValueError,KeyError,TypeError,ET.ParseError) as exc:print(path.name,str(exc))
(out/'index.json').write_text(json.dumps(index,sort_keys=True))
(out/'NOTICE.txt').write_text('Derived from SIMRacingAppsServer track data. Copyright (C) 2015–2024 Jeffrey Gilliam. Apache License 2.0. Source: https://github.com/SIMRacingApps/SIMRacingAppsServer . Original survey and GPX files included in Third_Party/SIMRacingApps_tracks. GPX fraction positions are estimates, not optimal racing lines.\n')
print('Bundled layouts:',len(index))
