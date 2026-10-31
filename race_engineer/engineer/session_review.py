"""Measured inputs and educational explanations; never a tire-slip diagnosis."""
import math,json,sqlite3,statistics
from .driving import driving,safe_straight

def explain(review):
    metric=review.get('action_metric');brake=review.get('brake_m');steer=review.get('steering_delta_deg');pickup=review.get('pickup_m')
    if metric=='braking distance' and brake is not None:
        if brake<0:return 'Braking earlier can leave time spent slowing or coasting before rotation. A small later-marker experiment tests whether you can preserve entry speed without sacrificing the exit. The trace shows a difference, not its cause.'
        return 'A late braking point can leave less room to release the brake and establish the cornering line. Trying an earlier marker may make the transition and exit more repeatable; compare the whole section before keeping the change.'
    if metric=='brake input percentage points':
        if review.get('brake_delta_pp',0)>0:return 'Extra brake input can reduce speed more than needed or disturb the transition into steering. A smaller peak may help if available grip and the reference line are comparable. Input percentage is not brake force, and ABS intervention is not established here.'
        return 'Too little brake input can extend the braking phase and leave less time for rotation. A small increase tests that possibility, provided the tires have grip. If it creates lock-up or instability, back out of the experiment.'
    if steer is not None and abs(steer)>=8:return 'Steering asks the front tires to generate cornering force. Extra wheel angle can scrub speed if the tires are already saturated; too little can miss the intended path. Compare speed, line and steering ratio before changing lock. Angle alone does not prove understeer.'
    if pickup is not None and pickup>=8:return 'Later sustained throttle can reduce acceleration along the next straight. The useful goal is a repeatable exit that allows progressive power, rather than an early throttle stab followed by a lift.'
    return 'Corner time reflects the whole sequence of braking, rotation and acceleration. Compare the input traces and exit before choosing a cause. Change one item and repeat several clean laps.'

class InputStyleMonitor:
    def __init__(self):self.previous=None;self.counts=dict(abrupt_brake_release=0,abrupt_throttle=0,rapid_steering=0);self.last={};self.driving_seconds=0.
    def update(self,d):
        previous=self.previous;self.previous=dict(d)
        if not previous or not driving(d) or not driving(previous):return
        dt=d.get('SessionTime',0)-previous.get('SessionTime',0)
        if not .01<=dt<=.2:return
        self.driving_seconds+=dt;t=d['SessionTime'];angle=abs(d.get('SteeringWheelAngle',0));speed=d.get('Speed',0)
        candidates=[]
        if speed>8 and angle>.12 and previous.get('Brake',0)-d.get('Brake',0)>.3 and dt<=.15:candidates.append('abrupt_brake_release')
        if speed>8 and angle>.15 and d.get('Throttle',0)-previous.get('Throttle',0)>.45 and dt<=.15:candidates.append('abrupt_throttle')
        if speed>15 and abs(d.get('SteeringWheelAngle',0)-previous.get('SteeringWheelAngle',0))/dt>4:candidates.append('rapid_steering')
        for key in candidates:
            if t-self.last.get(key,-1e9)>2:self.counts[key]+=1;self.last[key]=t
    def summary(self):
        n=sum(self.counts.values());minutes=self.driving_seconds/60
        if self.driving_seconds<20:return 'Insufficient continuous on-track data to assess input patterns.'
        label='Repeated abrupt inputs are worth reviewing for possible over-driving.' if n/max(minutes,1e-6)>=4 else 'No frequent abrupt-input pattern crossed this detector’s thresholds.'
        return label+f' Over {minutes:.1f} driving minutes: {self.counts["abrupt_brake_release"]} abrupt brake releases while turning, {self.counts["abrupt_throttle"]} sharp throttle applications while turning, and {self.counts["rapid_steering"]} rapid steering events. These are input observations, not proof of sliding or tire overheating. Chicanes, corrections and traffic can explain events.'

def tire_snapshot(d):
    tires=[]
    for wheel in ('LF','RF','LR','RR'):
        temps=[d.get(wheel+'tempC'+s) for s in ('L','M','R')]
        temps=[v for v in temps if isinstance(v,(int,float)) and math.isfinite(v) and 0<v<250]
        wears=[d.get(wheel+'wear'+s) for s in ('L','M','R')]
        wears=[v for v in wears if isinstance(v,(int,float)) and math.isfinite(v) and 0<=v<=1]
        if not any(wears):wears=[]
        if temps or wears:tires.append(dict(wheel=wheel,temp_min=min(temps) if temps else None,temp_max=max(temps) if temps else None,tread_min=min(wears)*100 if wears else None))
    return tires

def tire_text(tires):
    if not tires:return 'Tire temperature and wear readings unavailable. Do not infer current grip or overheating from missing data.'
    parts=[]
    for tire in tires:
        values=[]
        if tire['temp_min'] is not None:values.append(f'{tire["temp_min"]:.0f}–{tire["temp_max"]:.0f}°C reported carcass')
        if tire['tread_min'] is not None:values.append(f'{tire["tread_min"]:.0f}% minimum reported tread remaining')
        parts.append(tire['wheel']+': '+', '.join(values))
    return '; '.join(parts)+'. Reported/pit snapshots; freshness is not guaranteed and these are not live tire-grip measurements.'

class TireMonitor:
    def __init__(self):self.current=[];self.fingerprint=None;self.pending=None;self.last_voice=-1e9
    def update(self,d):
        tires=tire_snapshot(d);self.current=tires
        fingerprint=json.dumps(tires,sort_keys=True)
        if tires and fingerprint!=self.fingerprint and (d.get('OnPitRoad') or not d.get('IsOnTrack')):
            self.pending=(d.get('SessionTime',0),tires)
        self.fingerprint=fingerprint
    def voice(self,d):
        t=d.get('SessionTime',0)
        if not self.pending or not safe_straight(d) or t-self.last_voice<120:return None
        created,tires=self.pending
        if not 0<=t-created<=120:self.pending=None;return None
        self.pending=None;self.last_voice=t
        wear=[v['tread_min'] for v in tires if v['tread_min'] is not None]
        temps=[v['temp_max'] for v in tires if v['temp_max'] is not None]
        parts=['Tire pit report.']
        if wear:parts.append(f'Lowest reported tread remaining is {min(wear):.0f} percent.')
        if temps:parts.append(f'Highest reported carcass temperature is {max(temps):.0f} degrees Celsius.')
        parts.append('Those are reported pit readings, not live temperatures. Keep your transitions smooth.')
        return ' '.join(parts)

def build_recap(database,session_id,cancel=None):
    if cancel and cancel.is_set():return 'Analysis canceled.'
    db=sqlite3.connect(str(database));db.row_factory=sqlite3.Row
    try:
        session=db.execute('SELECT * FROM sessions WHERE id=?',(session_id,)).fetchone()
        if not session:raise ValueError('Recorded session not found.')
        meta=json.loads(session['profile']);laps=list(db.execute('SELECT * FROM laps WHERE session_id=? ORDER BY id',(session_id,)))
        text=[f'SESSION {session_id}  /  {session["mode"]}'+('  /  PARTIAL — still recording' if not session['ended'] else ''),meta.get('car','Unknown car')+' • '+meta.get('track','Unknown track')+' / '+str(meta.get('config','')),session['started'],'']
        clean=[r for r in laps if r['clean']];times=[r['lap_time'] for r in clean]
        text.append(f'{len(laps)} completed recorded laps, {len(clean)} clean.')
        if times:
            from .time_format import elapsed
            text.append(f'Clean-lap best {elapsed(min(times),3)}; average {elapsed(statistics.mean(times),3)}; spread {max(times)-min(times):.3f}s. Fuel, traffic and changing conditions can affect these numbers.')
        monitor=InputStyleMonitor();last_tires=[];tire_when=None
        for row in db.execute('SELECT data,sim_time FROM samples WHERE session_id=? ORDER BY sim_time,id',(session_id,)):
            if cancel and cancel.is_set():return 'Analysis canceled.'
            d=json.loads(row['data']);monitor.update(d);tires=tire_snapshot(d)
            if tires:last_tires=tires;tire_when=row['sim_time']
        text.extend(['','INPUT STYLE',monitor.summary(),'','WHY SMOOTH INPUTS MATTER','Abrupt transitions can change tire loading faster than the car settles. Smoother release and power application can improve repeatability. These traces do not establish that grip was exceeded. Review the replay before treating an emergency correction as a technique fault.','','TIRES',tire_text(last_tires)])
        if tire_when is not None:
            from .time_format import elapsed
            text.append(f'Last observed in the recording at simulator time {elapsed(tire_when)}; this is observation time, not a guarantee of measurement freshness.')
        reviews=[r for lap in clean for r in json.loads(lap['reviews']) if r.get('loss',0)>=.15]
        groups={}
        for r in reviews:groups.setdefault(r['name'],[]).append(r)
        ranked=sorted(groups.items(),key=lambda item:statistics.mean(r['loss'] for r in item[1]),reverse=True)
        text.extend(['','PRIORITIES FOR THE NEXT SESSION'])
        if not ranked:text.append('There are not enough comparable corner losses for a numerical practice plan. Record a clean reference and several repeat laps. Start with consistent visual markers.')
        for name,items in ranked[:3]:
            r=max(items,key=lambda v:v['loss']);average=statistics.mean(v['loss'] for v in items)
            text.extend([f'\n{name} — average observed loss {average:.2f}s across {len(items)} comparable passages.', 'Evidence: '+r['evidence'],'Try: '+(r.get('tip') or 'Repeat this section with consistent inputs.'),'Why: '+r.get('why',explain(r)),'Practice: change only this item for three clean laps. Compare the full section and exit, then keep or reject the change.'])
        try:pit_reports=list(db.execute('SELECT payload FROM pit_reports WHERE session_id=? ORDER BY id DESC LIMIT 3',(session_id,)))
        except sqlite3.OperationalError:pit_reports=[]
        if pit_reports:
            text.extend(['','PIT STOP DEBRIEFS'])
            for row in reversed(pit_reports):
                from .time_format import elapsed
                report=json.loads(row[0]);text.append(f"Stop {report['stop_id']} at recorded simulator time {elapsed(report['sim_time'])}");text.extend(report.get('facts',[]))
        text.extend(['','INTERPRETATION','Losses are relative to the reference active on each lap; references may change. They are not a guaranteed recoverable time sum. Input-event thresholds are heuristics, not a validated aggression score. Tire condition, setup, fuel and traffic can also explain pace.','Further learning: Training → Racecraft library.'])
        return '\n'.join(text)
    finally:db.close()
