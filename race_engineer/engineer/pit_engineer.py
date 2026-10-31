"""Session-aware pit-stop radio from observed SDK states, without service guesses."""
from collections import deque
import math,statistics
from .core import incident
from .session_review import explain,tire_snapshot,tire_text

BANK={
 'entry':['Pit lane. Watch your pit speed and get ready for the box.','You’re on pit road. Keep it tidy; I’ll brief you when you stop.','Pit entry confirmed. Mind the speed limit and your box.'],
 'box':['You’re stopped in the box. Here’s the useful part of that run.','In the box. Let’s use this pause to reset the plan.','You’re stationary in the pit stall. Quick debrief while we have a moment.'],
 'complete':['The sim reports service complete. Check your exit before pulling away.','Service completion is confirmed. Eyes on the lane as you leave the box.','Service is complete according to telemetry. Rejoin the lane when clear.'],
 'exit':['Back on track. Build the grip progressively and leave room at the blend line.','Pit exit confirmed. Check traffic and settle into the next stint.','You’re off pit road. Bring the pace back smoothly and keep the rejoin predictable.']}
CORRECTIONS={100:'The sim reports the car is too far left in the box.',101:'The sim reports the car is too far right in the box.',102:'The sim reports you are too far forward in the box.',103:'The sim reports you are too far back in the box.',104:'The sim reports the car is at the wrong angle in the box.',105:'The sim reports that repair cannot be completed.'}

def number(v):return isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v)
def session_kind(meta):
 value=str(meta.get('session_type','')).lower()
 if 'qual' in value:return 'qualifying'
 if 'race' in value:return 'race'
 if any(s in value for s in ('practice','test','warmup','warm up')):return 'practice'
 return 'session type unavailable'
def lap_phrase(seconds):
 minutes=int(seconds)//60;rest=seconds-minutes*60
 return f'{minutes} minute {rest:.1f} second' if minutes else f'{rest:.1f} second'

class PitEngineer:
 def __init__(self):
  self.state='track';self.was_pit=False;self.stopped_since=None;self.service_seen=False;self.service_last=None;self.stop_id=0;self.queue=[];self.last_voice=-1e9;self.last_t=None;self.variants={};self.initial_incidents=None
  self.laps=[];self.fuel_trace=deque(maxlen=20000);self.burns=deque(maxlen=5);self.last_gap={};self.gap_time=-1e9;self.report=None;self.report_count=0;self.last_event='';self.boxed_this_visit=False
 def phrase(self,topic):
  n=self.variants.get(topic,0);self.variants[topic]=n+1;return BANK[topic][n%len(BANK[topic])]
 def put(self,topic,text,t,priority=1):
  key=(self.stop_id,topic)
  if any(item['key']==key for item in self.queue):return
  self.queue.append(dict(key=key,topic=topic,text=text,t=t,priority=priority))
 def completed(self,lap,d):
  self.laps.append(dict(lap=lap['lap'],lap_time=lap['lap_time'],clean=lap['clean'],reviews=lap.get('reviews',[])));self.laps=self.laps[-1000:]
  if not lap['clean'] or not number(d.get('FuelLevel')):return
  start=lap['samples'][0].t if lap.get('samples') else None
  if start is None:return
  points=[v for v in self.fuel_trace if start-.25<=v[0]<=d['SessionTime']]
  if not points or abs(points[0][0]-start)>.25 or any(v[2] for v in points):return
  burn=points[0][1]-d['FuelLevel']
  if .02<burn<250:self.burns.append(burn)
 def update(self,d,meta,gaps=None,verbosity='Chatty'):
  t=d.get('SessionTime',0)
  if self.last_t is not None and (t<self.last_t or t-self.last_t>2):self.queue=[];self.stopped_since=None;self.service_seen=False;self.service_last=None
  self.last_t=t
  if d.get('IsReplayPlaying') or d.get('TelemetryAgeSeconds',0)>.3 or not d.get('IsOnTrack') or 'OnPitRoad' not in d:return
  pit=bool(d.get('OnPitRoad'));surface=d.get('PlayerTrackSurface');speed=d.get('Speed');status=d.get('PitSvStatus')
  if self.initial_incidents is None:self.initial_incidents=incident(d)
  fuel=d.get('FuelLevel')
  if number(fuel) and (not self.fuel_trace or t-self.fuel_trace[-1][0]>=.15):self.fuel_trace.append((t,fuel,pit))
  if not pit and gaps:self.last_gap=dict(gaps);self.gap_time=t
  if pit and not self.was_pit:
   self.stop_id+=1;self.queue=[];self.service_seen=False;self.service_last=None;self.state='pit_lane';self.boxed_this_visit=False
   if verbosity!='Quiet':self.put('entry',self.phrase('entry'),t)
  if pit:
   # Pit-road driving or a trackside stop does not establish a pit stop.
   boxed=number(speed) and abs(speed)<.5 and (surface==1 or status==1)
   if boxed:
    if self.stopped_since is None:self.stopped_since=t
    if t-self.stopped_since>=1.5 and not self.boxed_this_visit:
     self.state='box';self.boxed_this_visit=True;self.service_last=None;self.queue=[v for v in self.queue if v['topic']!='entry'];self.report=self.build_report(d,meta,verbosity);self.report_count+=1
     if verbosity!='Quiet':self.put('box',self.phrase('box')+' '+self.report['spoken'],t,2)
   else:
    self.stopped_since=None
    if self.state=='box':self.state='pit_lane';self.queue=[v for v in self.queue if v['topic']=='complete']
   if self.state=='box' and status==1:self.service_seen=True
   if self.state=='box' and status in CORRECTIONS and status!=self.service_last:self.put('correction-'+str(status),CORRECTIONS[status],t,10)
   if self.state=='box' and status==2 and self.service_seen and self.service_last!=2:self.put('complete',self.phrase('complete'),t,5)
   self.service_last=status
  elif self.was_pit:
   self.state='track';self.stopped_since=None;self.queue=[]
   self.put('exit',self.phrase('exit'),t,5)
  self.was_pit=pit
 def build_report(self,d,meta,verbosity):
  fuel=d.get('FuelLevel')
  kind=session_kind(meta);clean=[v for v in self.laps if v['clean']];facts=[f'This is {kind}.'];spoken=[]
  if kind=='race':
   position=d.get('PlayerCarPosition');class_position=d.get('PlayerCarClassPosition')
   if number(position) and position>0:spoken.append(f'You’re running position {int(position)}'+(f', {int(class_position)} in class.' if number(class_position) and class_position>0 else '.'))
  if clean:
   from .time_format import elapsed
   best=min(v['lap_time'] for v in clean);facts.append(f'Best clean recorded lap: {elapsed(best,3)}.');spoken.append(f'Best clean recorded lap is {lap_phrase(best)}.')
   if len(clean)>=6:
    trend=statistics.mean(v['lap_time'] for v in clean[-3:])-statistics.mean(v['lap_time'] for v in clean[-6:-3]);facts.append(f'Last-three average change: {trend:+.3f}s; conditions/traffic may explain it.')
    if abs(trend)>=.15:spoken.append(f'Your last three clean laps averaged {abs(trend):.1f} seconds {"slower" if trend>0 else "quicker"} than the previous three.')
  else:spoken.append('We haven’t recorded a complete clean lap yet. Let’s make the next run a consistent baseline.')
  current=incident(d)
  if number(current) and number(self.initial_incidents):facts.append(f'Incident-counter increase while recorded: {max(0,current-self.initial_incidents)}. This does not assign blame.')
  remaining=d.get('SessionTimeRemain');laps_left=d.get('SessionLapsRemainEx')
  if number(remaining) and 0<=remaining<24*3600:facts.append(f'Simulator session time remaining: {remaining:.0f}s.')
  if number(laps_left) and 0<=laps_left<10000:facts.append(f'Simulator laps remaining: {laps_left:.0f}.')
  if number(fuel):
   facts.append(f'Current reported fuel: {fuel:.2f} L.')
   if self.burns:
    burn=statistics.mean(self.burns);coverage=fuel/burn;facts.append(f'Estimated fuel coverage {coverage:.1f} laps, using {len(self.burns)} clean-lap consumption samples at {burn:.2f} L/lap.')
    if kind=='race':spoken.append(f'Fuel covers about {coverage:.1f} laps at our recently observed consumption. Confirm the fuel plan before leaving.')
   else:facts.append('Fuel-per-lap estimate unavailable; no invented stop strategy.')
  tires=tire_snapshot(d);facts.append(tire_text(tires))
  wear=[v['tread_min'] for v in tires if v['tread_min'] is not None]
  if wear and verbosity=='Chatty':spoken.append(f'Lowest reported tread remaining is {min(wear):.0f} percent. That is a pit snapshot, not live grip.')
  reviews=[r for v in self.laps[-3:] for r in v['reviews'] if r.get('tip') and r.get('loss',0)>=.15]
  if reviews:
   r=max(reviews,key=lambda item:item['loss']);facts.extend(['Next run: '+r['tip'],'Why: '+r.get('why',explain(r))])
   if verbosity=='Chatty':spoken.append(r['tip']+' '+r.get('why',explain(r)).split('. ')[0]+'.')
  if self.last_gap and d.get('SessionTime',0)-self.gap_time<60:
   for label,value in self.last_gap.items():
    if isinstance(value,dict) and number(value.get('gap_s')):facts.append(f'Before pit entry, estimated gap {label}: {value["gap_s"]:.1f}s. This is not a current pit-lane gap.')
  limit=meta.get('pit_speed_mps')
  facts.append(f'Reported pit speed limit: {limit*2.236936292:.1f} mph.' if number(limit) else 'Pit speed limit unavailable in app; check the simulator.')
  facts.append('Service completion is announced only after an observed in-progress → complete status. Fuel/tire selections are requests, not proof of completed work. Check lane, pit speed, mirrors and blend line before rejoining.')
  budget=3 if verbosity=='Standard' else 6
  return dict(sim_time=d.get('SessionTime'),session_type=kind,stop_id=self.stop_id,spoken=' '.join([f'This is {kind}.']+spoken[:budget]),facts=facts)
 def take(self,d,quiet=False):
  t=d.get('SessionTime',0);self.queue=[v for v in self.queue if 0<=t-v['t']<45]
  if quiet or not self.queue:return None
  item=max(self.queue,key=lambda v:v['priority']);minimum=0 if item['priority']>=5 else 4
  if t-self.last_voice<minimum:return None
  self.queue.remove(item);self.last_voice=t;self.last_event=item['topic'];return item['text']
