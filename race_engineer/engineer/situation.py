"""On-track passage-time gap estimates and conservative session briefings."""
import math
from collections import deque
from .driving import driving,safe_straight

class RelativeTraffic:
 def __init__(self):self.reset()
 def reset(self):self.traces={};self.current={};self.previous_t=None;self.trends={};self.last_voice=-1e9;self.latest={};self.phrase_count=0
 def update(self,d):
  t=d.get('SessionTime',0);positions=d.get('CarIdxLapDistPct');surfaces=d.get('CarIdxTrackSurface');pits=d.get('CarIdxOnPitRoad');player=d.get('PlayerCarIdx')
  if (self.previous_t is not None and not 0<t-self.previous_t<=.5) or d.get('IsReplayPlaying') or not d.get('IsOnTrack') or d.get('TelemetryAgeSeconds',0)>.3:
   self.reset()
  self.previous_t=t;self.latest={};self.current={}
  if not isinstance(positions,list) or not isinstance(surfaces,list) or not isinstance(pits,list) or type(player) is not int:
   self.traces.clear();self.trends.clear();return {}
  if d.get('OnPitRoad'):
   self.reset();return {}
  for i,p in enumerate(positions):
   if i>=len(surfaces) or i>=len(pits) or surfaces[i]!=3 or pits[i] or not isinstance(p,(int,float)) or not math.isfinite(p) or not 0<=p<1:
    self.traces.pop(i,None);continue
   seq=self.traces.setdefault(i,deque(maxlen=4000))
   if seq:
    delta=(p-(seq[-1][1]%1)+.5)%1-.5;dt=t-seq[-1][0]
    if dt<=0 or abs(delta)>.035 or delta<-.0002:seq.clear()
    elif dt<.09:self.current[i]=p;continue
   seq.append((t,p if not seq else seq[-1][1]+delta));self.current[i]=p
   while seq and t-seq[0][0]>60:seq.popleft()
  if player not in self.current or d.get('OnPitRoad'):return {}
  own=self.current[player];ahead=[];behind=[]
  for i,p in self.current.items():
   if i==player:continue
   distance=(p-own+.5)%1-.5
   if distance>.00005:ahead.append((distance,i))
   elif distance<-.00005:behind.append((-distance,i))
  for label,seq in (('ahead',ahead),('behind',behind)):
   if not seq:continue
   _,idx=min(seq);leader=idx if label=='ahead' else player;target=own if label=='ahead' else self.current[idx]
   gap=self.passage_gap(self.traces.get(leader,()),target,t)
   if gap is None or gap>30:continue
   key=(label,idx);history=self.trends.setdefault(key,deque(maxlen=400));history.append((t,gap))
   while history and t-history[0][0]>15:history.popleft()
   baseline=next(((when,g) for when,g in reversed(history) if t-when>=10),None)
   change=baseline[1]-gap if baseline else None
   self.latest[label]=dict(car_idx=idx,gap_s=round(gap,2),gain_s=round(change,2) if change is not None else None,window_s=round(t-baseline[0],1) if baseline else None,estimated=True)
  self.trends={k:v for k,v in self.trends.items() if v and t-v[-1][0]<2}
  return self.latest
 @staticmethod
 def passage_gap(trace,p,t):
  if len(trace)<2:return None
  target=trace[-1][1]-((trace[-1][1]%1-p)%1)
  for a,b in zip(reversed(list(trace)[:-1]),reversed(list(trace)[1:])):
   if a[1]<=target<=b[1] and b[1]>a[1]:
    when=a[0]+(target-a[1])/(b[1]-a[1])*(b[0]-a[0]);return max(0,t-when)
  return None
 def voice(self,d,quiet=False):
  t=d.get('SessionTime',0)
  if quiet or not safe_straight(d) or t-self.last_voice<getattr(self,'cooldown',35):return None
  for label in ('behind','ahead'):
   item=self.latest.get(label,{})
   gain=item.get('gain_s');window=item.get('window_s')
   if gain is None or gain<.25 or not window:continue
   self.last_voice=t
   variants=('The car behind is closing.','We have pressure building behind.','Keep an eye on the car behind.','The gap behind is coming down.') if label=='behind' else ('You are catching the car ahead.','You are taking time out of the car in front.','The gap ahead is coming down.','Your pace is bringing the car ahead closer.')
   opening=variants[self.phrase_count%len(variants)];self.phrase_count+=1
   who='They gained' if label=='behind' else 'You gained'
   return opening+f' Estimated gap {item["gap_s"]:.1f} seconds. {who} {gain:.1f} seconds over {window:.0f} seconds.'
  return None

class SituationCoach:
 def __init__(self):self.reset()
 def reset(self):self.announced=False;self.was_pit=None;self.exit_time=None;self.briefing=None;self.wet=None;self.last=-1e9
 def update(self,d,meta):
  t=d.get('SessionTime',0);pit=d.get('OnPitRoad',True)
  if self.was_pit is True and not pit:self.exit_time=t
  self.was_pit=pit
  if not self.announced and driving(d) and str(meta.get('session_type','')).casefold() not in ('','unknown'):
   self.announced=True
   kind=str(meta.get('session_type','Session'));lower=kind.lower()
   purpose='Use this run to work on one change and repeat it cleanly.' if 'practice' in lower or 'test' in lower else 'Find some space and focus on a clean timed lap.' if 'qual' in lower else 'Stay predictable in traffic and let the pace come to you.' if 'race' in lower else 'I’ll track your inputs and keep the calls relevant.'
   self.briefing=(t,kind+' session. '+purpose+' Build grip progressively; tire readings can be delayed and live brake temperatures are unavailable.')
  wet=bool(d.get('WeatherDeclaredWet') or d.get('TrackWetness',1)>2)
  if self.wet is False and wet:self.briefing=(t,'Conditions have turned wet. Build up grip progressively and reassess your braking markers.')
  self.wet=wet
 def take(self,d,quiet=False):
  if not self.briefing:return None
  t=d.get('SessionTime',0);created,text=self.briefing
  if t-created>60 or t<created:self.briefing=None;return None
  if not quiet and safe_straight(d) and t-self.last>=40:
   self.briefing=None;self.last=t;return text
  return None
 def summary(self,meta):return str(meta.get('session_type','Waiting'))+' • Tire temperatures: delayed / pit readings • Live brake temperatures: unavailable'
