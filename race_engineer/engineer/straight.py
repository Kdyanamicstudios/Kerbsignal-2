"""Detailed straightaway briefings that leave time for critical driving calls."""
import math
from .driving import safe_straight
from .position import MPH
from .time_format import elapsed


def corner_details(plan,reference,length):
 start=plan.get('turn') or plan.get('brake');end=plan.get('end')
 if start is None or end is None:return dict(description='turn details unavailable',minimum_mph=None)
 seq=[s for s in reference if max(0,start-25/max(length,1))<=s.p<=end]
 speeds=[s.speed*MPH for s in seq if start<=s.p and isinstance(s.speed,(int,float)) and math.isfinite(s.speed)]
 minimum=round(min(speeds)) if speeds else None
 direction=plan.get('direction');kind=plan.get('kind')
 points=[]
 for sample in seq:
  if sample.lat is None or sample.lon is None or not all(math.isfinite(v) for v in (sample.lat,sample.lon)):continue
  if not points:lat0=sample.lat;lon0=sample.lon
  x=(sample.lon-lon0)*111320*math.cos(math.radians(lat0));y=(sample.lat-lat0)*111320
  if not points or math.hypot(x-points[-1][0],y-points[-1][1])>=8:points.append((x,y))
 if not direction and len(points)>=5:
  headings=[math.atan2(b[1]-a[1],b[0]-a[0]) for a,b in zip(points,points[1:])]
  changes=[(b-a+math.pi)%(2*math.pi)-math.pi for a,b in zip(headings,headings[1:])]
  left=sum(v for v in changes if v>0)*180/math.pi;right=-sum(v for v in changes if v<0)*180/math.pi
  net=left-right
  if left>35 and right>35:direction='left-right';kind=kind or 'direction change'
  elif abs(net)>=12:direction='left' if net>0 else 'right';kind=kind or ('hairpin' if abs(net)>130 else 'sweeper' if abs(net)<40 else 'turn')
 if direction:
  description=('left-right direction change' if direction=='left-right' else kind.split()[0]+' '+direction+' turn' if kind in ('slow turn','medium turn','fast turn') else direction+' '+(kind or 'turn'))
 elif kind:description=kind
 else:description='turn details not learned'
 return dict(description=description,minimum_mph=minimum)

class StraightBriefing:
 def __init__(self):self.reset()
 def reset(self):self.snapshot={};self.seen=set();self.last=-1e9;self.details={}
 def update(self,d,meta,plans,reference,progress_speed=None):
  self.snapshot={};p=d.get('LapDistPct');length=meta.get('length',0)
  if not isinstance(p,(int,float)) or not math.isfinite(p) or not 0<=p<=1 or length<=0 or d.get('OnPitRoad') or d.get('IsReplayPlaying'):return {}
  candidates=[]
  for i,plan in enumerate(plans):
   if plan.get('brake') is None:continue
   distance=((plan['brake']-p)%1)*length
   if distance<1:continue
   candidates.append((distance,i,plan))
  if not candidates:return {}
  distance,index,plan=min(candidates,key=lambda row:row[0])
  rate=max(1,progress_speed if progress_speed is not None else d.get('Speed',0));distance=max(0,distance-rate*max(0,d.get('TelemetryAgeSeconds',0)))
  key=(id(reference),index,plan.get('name'),plan.get('brake'),plan.get('end'))
  if key not in self.details:self.details[key]=corner_details(plan,reference,length)
  details=self.details[key];target_lap=int(d.get('Lap',0))+(1 if plan['brake']<p else 0)
  self.snapshot=dict(name=plan.get('name','Next corner'),distance_m=round(distance),eta_s=round(distance/rate,1),target=(target_lap,index),**details)
  self.seen={item for item in self.seen if item[0]>=int(d.get('Lap',0))}
  return self.snapshot
 def voice(self,d,gaps,quiet=False):
  info=self.snapshot;t=d.get('SessionTime',0)
  if quiet or not info or not safe_straight(d) or info['target'] in self.seen or t-self.last<getattr(self,'cooldown',25):return None
  distance=info['distance_m'];eta=info['eta_s']
  if distance<100 or not 7<=eta<=30:return None
  rounded=max(10,round(distance/10)*10)
  description=info['description']
  count=getattr(self,'phrase_count',0);self.phrase_count=count+1
  openings=[f'Next braking zone in {rounded} meters, about {eta:.0f} seconds.',f'We’ve got {rounded} meters to the next braking marker, roughly {eta:.0f} seconds.',f'Your next braking marker is {rounded} meters ahead, about {eta:.0f} seconds away.',f'Set up for the next corner. Braking in {rounded} meters.',f'Look ahead now. There are {rounded} meters to the next braking zone.',f'The next marker is coming up in about {eta:.0f} seconds, {rounded} meters from here.',f'Use this straight to prepare. Next braking marker, {rounded} meters.',f'Your next braking zone is {rounded} meters up the road. Around {eta:.0f} seconds.']
  base=openings[count%len(openings)]
  if description!='turn details not learned':base+=' '+description.capitalize()+'.'
  details=[]
  for name,label in (('ahead','Car ahead'),('behind','Car behind')):
   item=gaps.get(name)
   if item:details.append(f'{label}, estimated {item["gap_s"]:.1f} seconds.')
  full=base+' '+ ' '.join(details)
  # Budget for speech generation, the spoken text, and a clean countdown window.
  def fits(text):return len(text.split())/2.6+2+3.8<=eta
  if fits(full):text=full.strip()
  elif fits(base):text=base
  else:
   text=f'Braking in {rounded} meters.'
   if description!='turn details not learned':text+=' '+description+'.'
   if not fits(text):return None
  self.seen.add(info['target']);self.last=t;return text
 def hud(self,gaps):
  if not self.snapshot:return 'Next braking zone: learn / import aligned corner markers'
  s=self.snapshot
  text=f'NEXT BRAKE  {s["distance_m"]:.0f} m  /  ~{elapsed(s["eta_s"])}  •  {s["name"]}  •  {s["description"]}'
  if s['minimum_mph'] is not None:text+=f'  •  Reference minimum ~{s["minimum_mph"]} mph (observed)'
  return text
