"""Read the SDK spotter's occupancy. This is not an opponent XY sensor."""
import math

TRAFFIC_PHRASES = {
 'left':'Car left. Hold your line.', 'right':'Car right. Hold your line.',
 'both':'Three wide. Hold your line.', 'two_left':'Two cars left. Hold your line.',
 'two_right':'Two cars right. Hold your line.', 'clear_left':'Clear left.',
 'clear_right':'Clear right.', 'clear':'Clear both sides.', 'still':'Still there. Hold your line.'}
SIDES={1:(0,0),2:(1,0),3:(0,1),4:(1,1),5:(2,0),6:(0,2)}

class Spotter:
 def __init__(self):self.reset()
 def reset(self):
  self.state=None;self.candidate=None;self.since=0.;self.last_time=None;self.last_call=-1e9
  self.left=self.right=0;self.available=False;self.message='Traffic signal unavailable'
 def update(self,d):
  t=d.get('SessionTime');raw=d.get('CarLeftRight')
  valid=(isinstance(t,(float,int)) and math.isfinite(t) and type(raw) is int and raw in SIDES
    and d.get('IsOnTrack') and not d.get('OnPitRoad',True) and not d.get('IsReplayPlaying')
    and d.get('PlayerTrackSurface')==3 and d.get('TelemetryAgeSeconds',0)<=.3)
  if not valid or self.last_time is not None and not 0<t-self.last_time<=.35:
   self.reset()
   if not valid:return None
  self.last_time=t;self.available=True
  # New occupancy is immediate; any reduction must remain stable for 0.6 seconds.
  old=SIDES.get(self.state,(0,0));new=SIDES[raw]
  reducing=new[0]<=old[0] and new[1]<=old[1] and new!=old
  if raw!=self.state:
   if reducing:
    if self.candidate!=raw:self.candidate=raw;self.since=t
    if t-self.since<.6:return None
   self.candidate=None;self.state=raw;self.left,self.right=new
   self.message=TRAFFIC_PHRASES.get({2:'left',3:'right',4:'both',5:'two_left',6:'two_right'}.get(raw),'Clear alongside')
   event={2:'left',3:'right',4:'both',5:'two_left',6:'two_right'}.get(raw)
   if raw==1 and any(old):event='clear' if all(old) else ('clear_left' if old[0] else 'clear_right')
   if event:self.last_call=t
   return event
  self.candidate=None
  if any(new) and t-self.last_call>=5:self.last_call=t;return 'still'
  return None
 def snapshot(self):return dict(available=self.available,left=self.left,right=self.right,message=self.message)
