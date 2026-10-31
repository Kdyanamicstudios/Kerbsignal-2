"""Observed input feedback and sparse, lap-event-only encouragement."""
import math
from .cues import DANGER_FLAGS
from .dialogue import FLOW_LINES

def driving(d):
 return bool(d.get('IsOnTrack') and not d.get('OnPitRoad',True) and not d.get('IsReplayPlaying')
  and d.get('PlayerTrackSurface')==3 and not int(d.get('SessionFlags',0))&DANGER_FLAGS
  and isinstance(d.get('Speed'),(float,int)) and math.isfinite(d['Speed']) and d['Speed']>1.5 and d.get('TelemetryAgeSeconds',0)<=.3)

def safe_straight(d):return driving(d) and d.get('Speed',0)>12 and abs(d.get('SteeringWheelAngle',99))<.045 and d.get('Brake',1)<.03 and d.get('Throttle',0)>.65

class Encouragement:
 def __init__(self):self.reset()
 def reset(self):self.seen=set();self.recent=[];self.pending=None;self.last_voice=-1e9;self.conditions=None;self.last_kind=None
 def completed(self,lap,previous_best,mode,now):
  key=(lap.get('lap'),lap.get('lap_time'));seconds=lap.get('lap_time',0)
  if mode!='LIVE' or not lap.get('clean') or key in self.seen:return None
  if not isinstance(seconds,(int,float)) or not math.isfinite(seconds) or seconds<=0:return None
  self.seen.add(key);conditions=tuple(lap.get('context',[]))
  if conditions!=self.conditions:self.recent=[];self.pending=None;self.conditions=conditions
  self.recent.append(seconds);self.recent=self.recent[-5:];kind=''
  if previous_best and seconds<previous_best-max(.1,previous_best*.001):
   message=f'Excellent lap. New best for these conditions, {previous_best-seconds:.2f} seconds faster.';kind='best'
  elif previous_best is None:message='Clean baseline recorded. Now we can compare your corners.';kind='baseline'
  elif len(self.recent)==5 and max(self.recent)-min(self.recent)<=max(.3,seconds*.003) and self.last_kind!='consistency':
   message='Great consistency. Five clean laps within a tight window.';kind='consistency';self.recent=[]
  else:return None
  if now-self.last_voice<90:return None
  self.pending=(now,message,kind);return message
 def take(self,d,quiet=False):
  if not self.pending:return None
  t=d.get('SessionTime',0);created,text,kind=self.pending
  if t<created or t-created>30:self.pending=None;return None
  if safe_straight(d) and not quiet and t-self.last_voice>=90:
   self.pending=None;self.last_voice=t;self.last_kind=kind;return text
  return None

class FlowCoach:
 """Feedback describes observed inputs; never invents a braking landmark."""
 def __init__(self):self.reset()
 def reset(self):self.active=False;self.last=-1e9;self.last_t=None;self.previous=None;self.announced=False;self.cooldowns={};self.lap_calls=set();self.lap=None;self.phrase_counts={}
 def update(self,d,enabled,has_markers=False):
  t=d.get('SessionTime',0);prev=self.previous
  if self.last_t is not None and (t<self.last_t or t-self.last_t>.5):prev=None
  self.last_t=t;self.previous=d;self.active=bool(enabled and driving(d))
  lap=d.get('Lap')
  if lap!=self.lap:self.lap_calls=set();self.lap=lap
  if not self.active:return None
  if not self.announced:
   self.announced=True;self.last=t
   return 'Coach is active. Corner markers are ready.' if has_markers else 'Coach is active. Learning this layout. Complete a clean lap to align corner instructions.'
  if has_markers or not prev or t-self.last<8:return None
  brake=d.get('Brake',0);throttle=d.get('Throttle',0);steer=abs(d.get('SteeringWheelAngle',0));key=None
  if brake>.3 and throttle>.2:key='overlap';text='Come off the throttle while braking. Keep the inputs smooth.'
  elif prev.get('Brake',0)>.1 and .02<brake<.3 and steer>.08:key='release';text='Ease the brake pressure as you add steering.'
  elif steer>.15 and throttle>.9:key='power';text='Smooth with the power. Unwind the wheel as you accelerate.'
  elif prev.get('Brake',0)>.02 and brake<.02 and steer<.05 and throttle<.25:key='exit';text='The wheel is opening. Build the throttle smoothly.'
  if key and key not in self.lap_calls and t-self.cooldowns.get(key,-1e9)>=90:
   variants=FLOW_LINES
   count=self.phrase_counts.get(key,0);self.phrase_counts[key]=count+1
   self.lap_calls.add(key);self.cooldowns[key]=t;self.last=t;return variants[key][count%len(variants[key])]
  return None
