"""Optional, approximate reference-based braking countdown and pedal-phase cues."""
import math
import statistics
import time
from collections import deque
from .core import at, supported, context
from .guides import profile_key

PHRASES = {'three':'Three','two':'Two','one':'One','brake':'Brake now',
           'hold':'Hold the pressure','release':'Ease off','turn':'Turn in','unwind':'Unwind','throttle':'Feed in throttle'}
DANGER_FLAGS = 0x8|0x10|0x100|0x4000|0x8000|0x100000


def steering_turns(reference):
    groups=[]
    for sample in reference:
        if abs(sample.steer)>.07:
            sign=1 if sample.steer>0 else -1
            if not groups or sample.t-groups[-1][-1].t>.35 or sign*groups[-1][-1].steer<0:
                groups.append([])
            groups[-1].append(sample)
    return [g for g in groups if g[-1].t-g[0].t>.3 and g[0].p>.0001]


def cue_plans(reference,zones,length=5000.):
    plans=[];turns=steering_turns(reference);used=set()
    for zone in zones:
        seq=[s for s in reference if zone['start'] <= s.p <= zone['end']]
        braking=[s for s in seq if s.brake>.08]
        if not braking:continue
        first=braking[0];peak=max(braking,key=lambda s:s.brake)
        release=next((s for s in seq if s.p>peak.p and s.brake<max(.12,peak.brake*.45)),None)
        hold=next((s for s in braking if s.t>=first.t+.2 and s.brake>.3),None)
        apex=min(seq,key=lambda s:s.speed)
        throttle=None
        for i,s in enumerate(seq):
            if s.p>apex.p and s.throttle>=.65 and s.brake<.05:
                following=[v for v in seq[i:] if v.t-s.t<=.35]
                if following[-1].t-s.t>=.25 and all(v.throttle>=.65 and v.brake<.05 for v in following):
                    throttle=s;break
        turn_index=next((i for i,g in enumerate(turns) if i not in used and zone['start']<=g[0].p<=zone['end']),None)
        turn=turns[turn_index] if turn_index is not None else None
        if turn_index is not None:used.add(turn_index)
        peak_turn=max(turn,key=lambda s:abs(s.steer)) if turn else None
        unwind=next((s for s in seq if peak_turn and s.p>peak_turn.p and abs(s.steer)<abs(peak_turn.steer)*.55),None)
        plans.append(dict(name=zone['name'],brake=first.p,turn=turn[0].p if turn else None,unwind=unwind.p if unwind else None,hold=hold.p if hold else None,
                          release=release.p if release else None,throttle=throttle.p if throttle else None,
                          end=zone['end']))
    for i,group in enumerate(turns):
        if i in used:continue
        start=group[0].p;end=min(.99999,group[-1].p+max(30,group[-1].speed*.6)/length)
        peak=max(group,key=lambda s:abs(s.steer))
        following=[s for s in reference if peak.p<s.p<=end]
        unwind=next((s for s in following if abs(s.steer)<abs(peak.steer)*.55),None)
        throttle=next((s for s in following if s.throttle>=.7 and s.brake<.04),None)
        plans.append(dict(name=f'Turn {i+1}',brake=None,turn=start,unwind=unwind.p if unwind else None,
                          hold=None,release=None,throttle=throttle.p if throttle else None,end=end))
    return sorted(plans,key=lambda p:p['brake'] if p['brake'] is not None else p['turn'])


class DrivingCues:
    def __init__(self,auto_ack=True):
        self.auto_ack=auto_ack
        self.enabled=False
        self.lead_seconds=.15
        self.guide=None
        self.reset()

    def reset(self):
        self.signature=None;self.plans=[];self.states={};self.previous_time=None
        self.last_call=-1e9;self.approaching=False
        self.motion=deque(maxlen=7);self.last_p=None;self.last_steer=0.;self.diagnostic={};self.source='Waiting for positioned corner markers'
        self.pause_reason='';self.plan_context=None;self.pending=None;self.history=deque(maxlen=100)

    def install_guide(self,guide):
        self.guide=guide;self.reset()

    def clear_guide(self):
        self.guide=None;self.reset()

    def update(self,d,meta,coach):
        self.pause_reason=''
        self.approaching=False
        self.diagnostic={};diagnostic_score=(2,float('inf'))
        if not self.enabled or not supported(meta):return None
        if self.guide and profile_key(self.guide.get('profile',{}))!=profile_key(meta):self.clear_guide()
        if self.guide and self.guide.get('context') is not None and tuple(self.guide['context'])!=context(d):
            self.states.clear();self.pending=None;self.source='Guide conditions changed — calls paused';return None
        if not self.guide and self.plans and self.plan_context!=getattr(coach,'reference_context',None):
            self.plans=[];self.states.clear();self.pending=None
        # Freeze spatial markers until explicitly resynced, rather than moving them
        # whenever a new fastest lap replaces the review reference.
        if not self.plans:
            if self.guide:
                self.plans=self.guide['corners'];self.source='Position coaching guide'
            elif coach.reference:
                self.plans=cue_plans(coach.reference,coach.zones,meta['length']);self.source='Learned spatial markers'
                self.plan_context=getattr(coach,'reference_context',None)
            else:return None
        t=d.get('SessionTime');p=d.get('LapDistPct');speed=d.get('Speed',0)
        if not all(isinstance(d.get(k),(int,float)) and math.isfinite(d[k]) for k in ('SessionTime','LapDistPct','Speed','Brake','Throttle','SteeringWheelAngle')):
            self.states.clear();self.pending=None;return None
        dt=t-self.previous_time if self.previous_time is not None else None
        gap=dt is not None and not 0<dt<=.3
        length=meta['length'];progress_speed=speed
        if dt and not gap and self.last_p is not None:
            dp=p-self.last_p
            if dp<-.8:dp+=1
            observed=dp*length/dt
            if not 0<=observed<=max(120,speed*2):gap=True
            else:self.motion.append(observed)
        if self.motion:progress_speed=statistics.median(self.motion)
        self.last_p=p
        self.previous_time=t
        valid=(0<=p<=1 and d.get('IsOnTrack') and not d.get('OnPitRoad',True)
               and d.get('PlayerTrackSurface')==3 and not d.get('IsReplayPlaying')
               and not int(d.get('SessionFlags',0))&DANGER_FLAGS and speed>2)
        if gap or not valid:
            self.states.clear();self.pending=None;self.motion.clear();return None
        refspeed=at(coach.reference,p,'speed') if coach.reference else None
        if not self.guide and (refspeed is None or refspeed<1 or not .65<=speed/refspeed<=1.4):
            self.pause_reason='Approach speed is outside the reference range — corner calls paused'
            self.states.clear();self.pending=None;return None
        progress_speed=max(1,progress_speed)
        age=max(0,d.get('TelemetryAgeSeconds',0))
        if d.get('_host_time') is not None:age+=max(0,time.monotonic()-d['_host_time'])
        if age>.3:self.states.clear();self.pending=None;return None
        age=min(.25,age)
        predicted_p=p+progress_speed*age/length
        phase_p=predicted_p+progress_speed*self.lead_seconds/length
        if self.pending:
            if t-self.pending['time']>.18 or (self.pending['event']=='brake' and d.get('Brake',0)>=.08):
                self.acknowledge(False,'expired / inputs changed',expire=True)
            else:return self.pending['event']
        lap=int(d.get('Lap',0))
        previous_steer=self.last_steer;self.last_steer=abs(d['SteeringWheelAngle'])
        for key in list(self.states):
            if key[0]<lap or key[0]>lap+1:del self.states[key]
        # Consider both the current passage and the next lap's approach at the finish line.
        for index,plan in enumerate(self.plans):
            marker=plan['brake'] if plan['brake'] is not None else plan['turn']
            distance=(marker-predicted_p)*length
            target_lap=lap
            if distance < -max(20.,speed*.4) and p>plan['end']:
                distance+=length;target_lap+=1
            eta=distance/progress_speed
            key=(target_lap,index)
            state=self.states.setdefault(key,dict(previous_eta=None,armed=False,done=set()))
            old_eta=state['previous_eta'];state['previous_eta']=eta
            if self.lead_seconds+.3<eta<6:state['armed']=True
            approaching=-.5<=eta<=4
            in_zone=marker<=p<=plan['end'] and target_lap==lap
            self.approaching=self.approaching or approaching or in_zone
            if -1<eta<8 or in_zone:
                phase='approach'
                for stage,position in sorted(((k,plan.get(k)) for k in ('brake','hold','release','turn','unwind','throttle') if plan.get(k) is not None),key=lambda v:v[1]):
                    if p>=position:phase=stage
                score=(0 if in_zone else 1,abs(distance))
                if score<diagnostic_score:
                    diagnostic_score=score
                    self.diagnostic=dict(corner=plan['name'],phase=phase,distance_m=round(distance,1),eta_seconds=round(eta,3),position_pct=round(p*100,3),source=self.source,audio_lead_ms=round(self.lead_seconds*1000))
            event=None
            if plan['brake'] is not None and approaching and d.get('Brake',0)<.08 and state['armed']:
                for threshold,name in ((3+self.lead_seconds,'three'),(2+self.lead_seconds,'two'),(1+self.lead_seconds,'one'),(self.lead_seconds,'brake')):
                    if old_eta is not None and old_eta>threshold>=eta and eta>=threshold-.25 and name not in state['done']:
                        event=name;break
            elif d.get('Brake',0)>=.08:
                # Never tell the driver to start braking when they already are.
                state['armed']=False
            # Turn guidance is position-aligned to the reference, with configurable audio lead.
            if event is None and plan.get('turn') is not None and target_lap==lap:
                turn_eta=(plan['turn']-predicted_p)*length/progress_speed
                previous_turn=state.get('turn_eta');state['turn_eta']=turn_eta
                if previous_turn is not None and previous_turn>self.lead_seconds>=turn_eta>=self.lead_seconds-.25 and abs(d['SteeringWheelAngle'])<.07 and d['Brake']<.65 and 'turn' not in state['done']:
                    event='turn'
            if event is None and in_zone:
                refbrake=at(coach.reference,phase_p,'brake')
                refsteer=at(coach.reference,phase_p,'steer')
                if plan['hold'] is not None and plan['hold']<=phase_p<(plan['release'] or plan['end']) and d.get('Brake',0)>.15 and (self.guide or refbrake is not None and refbrake>.3):
                    event='hold'
                elif plan['release'] is not None and plan['release']<=phase_p<=plan['release']+max(20,speed*.4)/length and d.get('Brake',0)>.12 and (self.guide or refbrake is not None and refbrake<.35):
                    event='release'
                elif plan.get('unwind') is not None and plan['unwind']<=phase_p<=plan['unwind']+max(.001,30/length) and ((refsteer is not None and abs(d['SteeringWheelAngle'])>max(.07,abs(refsteer)*1.25)) or self.guide and abs(d['SteeringWheelAngle'])>.07) and 'unwind' not in state['done']:
                    event='unwind'
                elif plan['throttle'] is not None and plan['throttle']<=phase_p<=min(plan['end'],plan['throttle']+max(20,speed*.4)/length) and d.get('Brake',1)<.04 and d.get('Throttle',1)<.65 and ((refsteer is not None and abs(d.get('SteeringWheelAngle',99))<=abs(refsteer)*1.25+.05) or self.guide and abs(d['SteeringWheelAngle'])<=previous_steer+.01):
                    event='throttle'
                if event in state['done']:event=None
            if event and (event in ('brake','turn','release') or t-self.last_call>=.55):
                self.pending=dict(event=event,state=state,time=t,corner=plan['name'],eta=eta,host=time.monotonic())
                if self.auto_ack:self.acknowledge(True)
                return event
        return None

    def acknowledge(self,played,reason='',expire=False):
        if not self.pending:return
        item=self.pending
        if played or expire or reason in ('traffic','muted'):
            item['state']['done'].add(item['event'])
            if played:self.last_call=item['time']
            self.history.append(dict(event=item['event'],corner=item['corner'],session_time=item['time'],eta_s=item['eta'],played=bool(played),reason=reason,dispatch_delay_ms=round((time.monotonic()-item['host'])*1000,1)))
            self.pending=None
