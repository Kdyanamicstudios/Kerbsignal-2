"""Distance-aligned reference comparison and conservative lap validation."""
from dataclasses import dataclass, asdict
import math
import statistics


@dataclass
class Sample:
    t: float
    p: float
    speed: float
    brake: float
    throttle: float
    steer: float
    lat: float | None = None
    lon: float | None = None

    @classmethod
    def from_data(cls, d):
        return cls(d['SessionTime'], d['LapDistPct'], d['Speed'], d['Brake'], d['Throttle'],
                   d.get('SteeringWheelAngle', 0), d.get('Lat'), d.get('Lon'))


def at(samples, p, field):
    """Linear interpolation at the same distance, never align by elapsed time."""
    import bisect
    if not samples or p < samples[0].p or p > samples[-1].p:
        return None
    i = bisect.bisect_left(samples,p,key=lambda s:s.p)
    a, b = samples[max(0, i-1)], samples[min(i, len(samples)-1)]
    av, bv = getattr(a, field), getattr(b, field)
    if av is None or bv is None or b.p-a.p > .008:
        return None
    f = (p-a.p)/(b.p-a.p) if b.p > a.p else 0
    return av+(bv-av)*f


def zones(samples, length=5000.):
    # Distances are meters, so the same detector works on short and long layouts.
    groups=[]
    for sample in samples:
        if sample.brake>.08:
            if not groups or sample.t-groups[-1][-1].t>.6 or (sample.p-groups[-1][-1].p)*length>40:
                groups.append([])
            groups[-1].append(sample)
    seeds=[group for group in groups if group[-1].t-group[0].t>=.35]
    result=[]
    for i,group in enumerate(seeds):
        start=max(.00001,group[0].p-max(45,group[0].speed*.8)/length)
        end=min(.99999,group[-1].p+max(160,group[0].speed*5)/length)
        if i+1<len(seeds):end=min(end,seeds[i+1][0].p-max(20,seeds[i+1][0].speed*.35)/length)
        if end>start:result.append(dict(name=f'Braking zone {i+1}',start=start,end=end))
    return result


def compare(current, reference, zone, length):
    start, end = zone['start'], zone['end']
    a = [s for s in current if start <= s.p <= end]
    b = [s for s in reference if start <= s.p <= end]
    if len(a) < 5 or len(b) < 5:
        return None
    times = [at(seq, p, 't') for seq in (current, reference) for p in (start, end)]
    if any(v is None for v in times):
        return None
    loss = (times[1]-times[0])-(times[3]-times[2])
    amin, bmin = min(a, key=lambda s:s.speed), min(b, key=lambda s:s.speed)
    abrake = next((s for s in a if s.brake > .08), None)
    bbrake = next((s for s in b if s.brake > .08), None)
    brake_m = (abrake.p-bbrake.p)*length if abrake and bbrake else None
    # Require sustained throttle, not a transient blip.
    def pickup(seq, apex):
        after = [s for s in seq if s.p > apex.p]
        for i, s in enumerate(after):
            if s.throttle >= .7:
                following = [v for v in after[i:] if v.t-s.t <= .3]
                if following[-1].t-s.t >= .25 and all(v.throttle >= .7 for v in following):
                    return s.p
        return None
    ap, bp = pickup(a, amin), pickup(b, bmin)
    pickup_m = (ap-bp)*length if ap is not None and bp is not None else None
    evidence = f'{zone["name"]}: {loss:+.2f}s versus reference; minimum speed {(amin.speed-bmin.speed)*2.236936292:+.1f} mph.'
    tip = ''
    if loss >= .15:
        if brake_m is not None and abs(brake_m) >= 8:
            tip = f'You braked {abs(brake_m):.0f} meters {"later" if brake_m > 0 else "earlier"} than your reference. Try its braking marker next lap.'
        elif pickup_m is not None and pickup_m >= 8:
            tip = f'You reached seventy percent throttle {pickup_m:.0f} meters later. Work on a smooth exit before adding more throttle.'
        else:
            tip = 'Review this section against your reference after the session.'
    from .technique import correction,steering_review
    quantified=correction(a,b,brake_m,loss)
    tip=quantified.pop('suggested_action',tip)
    steering=steering_review(a,b)
    quantified['steering_delta_deg']=steering
    if not quantified.get('action_metric') and loss>=.15 and steering is not None and abs(steering)>=8 and (pickup_m is None or pickup_m<8):
        tip=f'You used about {abs(steering):.0f} degrees {"more" if steering>0 else "less"} steering-wheel angle than the reference at similar speed. If your steering ratio and line match, try a little {"less" if steering>0 else "more"} steering next lap.'
    from .session_review import explain
    quantified['why']=explain(dict(**quantified,brake_m=brake_m,pickup_m=pickup_m))
    return dict(**quantified,name=zone['name'], loss=round(loss, 3), brake_m=brake_m, pickup_m=pickup_m,
                speed_delta_mph=(amin.speed-bmin.speed)*2.236936292, evidence=evidence, tip=tip)


def line_offset(sample, reference):
    """2D separation to nearby reference segments; not time lost or optimality."""
    if sample.lat is None or sample.lon is None or not reference:
        return None
    import bisect
    left=bisect.bisect_left(reference,sample.p-.015,key=lambda s:s.p)
    right=bisect.bisect_left(reference,sample.p+.015,key=lambda s:s.p)
    candidates = [s for s in reference[left:right] if abs(s.p-sample.p) < .015 and s.lat is not None and s.lon is not None]
    if len(candidates) < 2:
        return None
    scale_x = 111320*math.cos(math.radians(sample.lat))
    scale_y = 111320
    best = math.inf
    for a, b in zip(candidates, candidates[1:]):
        if b.p-a.p > .008:
            continue
        ax, ay = (a.lon-sample.lon)*scale_x, (a.lat-sample.lat)*scale_y
        bx, by = (b.lon-sample.lon)*scale_x, (b.lat-sample.lat)*scale_y
        dx, dy = bx-ax, by-ay
        u = max(0, min(1, -(ax*dx+ay*dy)/(dx*dx+dy*dy))) if dx*dx+dy*dy else 0
        best = min(best, math.hypot(ax+u*dx, ay+u*dy))
    return best if math.isfinite(best) else None


def supported(meta):
    # Any track/layout and car with identified, usable SDK metadata can be coached.
    length=meta.get('length')
    return (isinstance(length,(int,float)) and math.isfinite(length) and length>100
        and bool(str(meta.get('track_id','')).strip())
        and meta.get('track') not in (None,'','Unknown')
        and meta.get('config')!='Unknown'
        and bool(meta.get('car_path')))


def incident(d):
    return d.get('PlayerCarMyIncidentCount', d.get('PlayerCarDriverIncidentCount'))


def context(d):
    # Exact aid settings and broad weather regime; reset reference on changes.
    return (d.get('WeatherDeclaredWet'), d.get('TrackWetness'), d.get('dcABS'), d.get('dcTractionControl'))


class Coach:
    def __init__(self):
        self.reference = []
        self.reference_time = None
        self.reference_label = 'No clean reference yet'
        self.reference_timing_estimated=False
        self.reference_context = None
        self.zones = []
        self.samples = []
        self.previous = None
        self.active = False
        self.invalid = set()
        self.checked = set()
        self.reviews = []
        self.start_incident = None
        self.lap_context = None
        self.track_length = 0
        self.pending = []
        self.last_voice = -1e9
        self.last_spoken_review = None
        self.status = 'Cross the start line, then complete a clean lap.'

    def import_reference(self, payload, meta, live_context=None):
        if payload.get('format') != 'race-engineer-reference-v1':
            raise ValueError('Not a Race Engineer reference file.')
        m = payload.get('profile', {})
        if m.get('car_id') not in (None,'') and meta.get('car_id') not in (None,'') and str(m['car_id'])!=str(meta['car_id']):
            raise ValueError('Reference car ID does not match the current player car.')
        if any(m.get(k) != meta.get(k) for k in ('car_path', 'track_id', 'config')) or abs(m.get('length',0)-meta.get('length',0)) > 5:
            raise ValueError('Reference car and track layout do not match this session.')
        samples = [Sample(**s) for s in payload['samples']]
        if len(samples) < 100 or samples[0].p > .01 or samples[-1].p < .99:
            raise ValueError('Reference needs a complete lap.')
        if any(not all(math.isfinite(v) for v in (s.t,s.p,s.speed,s.brake,s.throttle,s.steer)) for s in samples):
            raise ValueError('Reference contains non-finite values.')
        if any(not 0 <= s.p <= 1 or s.speed < 0 or not 0 <= s.brake <= 1 or not 0 <= s.throttle <= 1 for s in samples):
            raise ValueError('Reference driving values are outside expected ranges.')
        for s in samples:
            if s.lat is not None and (not isinstance(s.lat,(int,float)) or not math.isfinite(s.lat) or not -90 <= s.lat <= 90):
                raise ValueError('Invalid reference latitude.')
            if s.lon is not None and (not isinstance(s.lon,(int,float)) or not math.isfinite(s.lon) or not -180 <= s.lon <= 180):
                raise ValueError('Invalid reference longitude.')
        if any(b.p <= a.p or b.t <= a.t for a,b in zip(samples,samples[1:])):
            raise ValueError('Reference samples must move forward in distance and time.')
        ref_context = tuple(payload.get('context', []))
        if len(ref_context) != 4 or (live_context is not None and ref_context != live_context):
            raise ValueError('Reference weather regime or ABS/TC settings do not match. Use a compatible lap.')
        reference_time=float(payload['lap_time'])
        if not math.isfinite(reference_time) or reference_time<=0:raise ValueError('Invalid reference lap time.')
        elapsed=samples[-1].t-samples[0].t
        if abs(elapsed-reference_time)>max(.5,reference_time*.01):raise ValueError('Reference sample timing does not agree with its lap time.')
        self.reference = samples
        self.reference_time=reference_time
        self.reference_timing_estimated=bool((payload.get('provenance') or {}).get('derived_time'))
        self.reference_label = 'Imported reference (optimality unverified)'
        self.reference_context = ref_context
        self.zones = zones(samples,meta["length"])
        self.checked=set();self.reviews=[]
        self.pending.clear()

    def update(self, d, meta):
        completed, new_reviews = None, []
        required = ('SessionTime','LapDistPct','Speed','Brake','Throttle')
        if not all(isinstance(d.get(k), (int,float)) and math.isfinite(d[k]) for k in required):
            self.active = False
            self.status = 'Missing driving telemetry; coaching paused.'
            return None, []
        if not supported(meta):
            self.active = False
            self.status = 'Waiting for identified car, track layout and track length from iRacing.'
            self.previous = d
            return None, []
        self.track_length = meta['length']
        s = Sample.from_data(d)
        prev = self.previous
        current_context = context(d)
        if self.reference and current_context != self.reference_context:
            self.reference = []; self.zones = []; self.reference_time = None
            self.reference_label = 'Relearning: weather or ABS/TC changed'
            self.pending.clear()
        if prev and s.t < prev['SessionTime']:
            self.active = False; self.samples = []; self.pending.clear()
        crossing = prev and prev['LapDistPct'] > .98 and s.p < .02 and 0 < s.t-prev['SessionTime'] < 1
        if crossing:
            # Interpolate start/finish crossing to avoid variable polling offset.
            fraction = (1-prev['LapDistPct'])/(1-prev['LapDistPct']+s.p)
            cross_t = prev['SessionTime']+fraction*(s.t-prev['SessionTime'])
            if self.active and self.samples:
                self.samples.append(Sample(cross_t, 1., s.speed,s.brake,s.throttle,s.steer,s.lat,s.lon))
                elapsed = cross_t-self.samples[0].t
                if self.samples[-2].p < .98 or len(self.samples) < 100:
                    self.invalid.add('incomplete recording')
                reasons = sorted(self.invalid)
                completed = dict(lap=int(prev.get('Lap',0)), lap_time=elapsed, clean=not reasons,
                                 reasons=reasons, samples=self.samples[:], reviews=self.reviews[:], context=self.lap_context)
                if not reasons and (not self.reference or elapsed < self.reference_time):
                    self.reference = self.samples[:]; self.reference_time = elapsed;self.reference_timing_estimated=False
                    self.reference_context = self.lap_context
                    self.reference_label = 'Your fastest clean lap this session'
                    self.zones = zones(self.reference,meta["length"])
            self.samples = [Sample(cross_t,0.,s.speed,s.brake,s.throttle,s.steer,s.lat,s.lon)]
            self.invalid = set(); self.checked = set(); self.reviews = []
            self.start_incident = incident(d); self.lap_context = current_context
            self.active = True
        if self.active:
            if not d.get('IsOnTrack', False) or d.get('OnPitRoad', True) or d.get('PlayerTrackSurface') != 3:
                self.invalid.add('pit / off track / out of car')
            if d.get('IsReplayPlaying', False):
                self.invalid.add('replay')
            if incident(d) is None or self.start_incident is None:
                self.invalid.add('incident validation unavailable')
            elif incident(d) != self.start_incident:
                self.invalid.add('incident')
            if current_context != self.lap_context:
                self.invalid.add('weather or ABS/TC changed')
            if prev:
                dt, dp = s.t-prev['SessionTime'], s.p-prev['LapDistPct']
                if dt > .5 or (not crossing and (dp < -.001 or dp > .015)):
                    self.invalid.add('telemetry gap / reset')
            if s.p >= 0 and (not self.samples or s.p > self.samples[-1].p):
                self.samples.append(s)
            if self.reference and not self.invalid:
                for i, zone in enumerate(self.zones):
                    if i not in self.checked and s.p > zone['end']:
                        self.checked.add(i)
                        review = compare(self.samples, self.reference, zone, self.track_length)
                        if review:
                            review['timing_estimated']=self.reference_timing_estimated
                            if self.reference_timing_estimated:
                                review['evidence']='Estimated comparison timing. '+review['evidence']
                                review['confidence']='Distance-aligned inputs; section times estimated'
                            self.reviews.append(review); new_reviews.append(review)
                            if review['tip']:
                                from .technique import spoken_review
                                self.pending.append((s.t,spoken_review(review,len(self.reviews)),review))
                                self.pending=self.pending[-3:]
            self.status = ('Lap excluded from reference: '+', '.join(sorted(self.invalid))) if self.invalid else ('Comparing against reference' if self.reference else 'Recording first clean reference lap')
        self.previous = dict(d)
        return completed, new_reviews

    def voice(self, d, available_seconds=None):
        now = d.get('SessionTime',0)
        self.pending = [p for p in self.pending if 0 <= now-p[0] < 90]
        safe = d.get('IsOnTrack') and not d.get('OnPitRoad',True) and not d.get('IsReplayPlaying') and d.get('PlayerTrackSurface') == 3
        safe = safe and abs(d.get('SteeringWheelAngle',99)) < .08 and d.get('Brake',1) < .03 and d.get('Throttle',0) > .6 and d.get('Speed',0) > 20
        safe = safe and not (int(d.get('SessionFlags',0)) & (0x8|0x10|0x100|0x4000|0x8000|0x100000))
        if safe and not self.invalid and self.pending and now-self.last_voice > 20:
            # Include preparation, speech and a clean countdown window. A
            # detailed explanation waits for a long enough straight.
            item=self.pending[0];message=item[1];remainder=''
            needed=len(message.split())/2.6+6
            if available_seconds is not None and needed>available_seconds:
                import re
                sentences=re.split(r'(?<=[.!?])\s+(?=[A-Z])',message)
                chosen=[]
                for sentence in sentences:
                    candidate=' '.join(chosen+[sentence])
                    if len(candidate.split())/2.6+6>available_seconds:break
                    chosen.append(sentence)
                if not chosen:return None
                message=' '.join(chosen);remainder=' '.join(sentences[len(chosen):])
            self.last_voice = now
            self.last_spoken_review=item[2] if len(item)>2 else None
            if remainder:self.pending[0]=(item[0],remainder,*item[2:])
            else:self.pending.pop(0)
            return message
        return None


def reference_payload(lap, meta):
    return dict(format='race-engineer-reference-v1', profile=meta, lap_time=lap['lap_time'],
                context=lap['context'], label='Recorded clean lap; optimality unverified',
                samples=[asdict(s) for s in lap['samples']])
