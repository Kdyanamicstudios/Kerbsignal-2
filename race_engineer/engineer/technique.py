"""Reference-relative technique advice; pedal input is not measured brake pressure."""
import math

def peak(samples):
    values=[s.brake for s in samples]
    return max((sum(values[i:i+3])/3 for i in range(len(values)-2)),default=None)

def correction(a,b,brake_m,loss):
    result=dict(brake_delta_pp=None,action_step=None,action_metric=None,confidence='Insufficient comparable braking data')
    aa=next((s for s in a if s.brake>.08),None)
    bb=next((s for s in b if s.brake>.08),None)
    if not aa or not bb or bb.speed<5 or not .9<=aa.speed/bb.speed<=1.1:return result
    pa,pb=peak(a),peak(b)
    if pa is None or pb is None:return result
    delta=(pa-pb)*100
    result.update(brake_delta_pp=delta,confidence='Reference comparison; similar approach speed')
    if loss<.15:return result
    if brake_m is not None and abs(brake_m)>=8:
        step=min(abs(brake_m),15 if brake_m<0 else 20)
        result.update(action_step=step,action_metric='braking distance',suggested_action=f'Next lap, try braking {step:.0f} meters {"later" if brake_m<0 else "earlier"}. Change one thing at a time.')
    elif abs(delta)>=5:
        step=min(abs(delta),8)
        result.update(action_step=step,action_metric='brake input percentage points',suggested_action=f'Next lap, try {step:.0f} percentage points {"less" if delta>0 else "more"} peak brake input, with a smooth release.')
    return result

def live_target(data,reference):
    from .core import at
    p=data.get('LapDistPct');speed=data.get('Speed',0);actual=data.get('Brake',0)
    if not reference or p is None or data.get('IsOnTrack') is False or data.get('OnPitRoad'):return None
    target=at(reference,p,'brake');refspeed=at(reference,p,'speed')
    if target is None or refspeed is None or refspeed<5 or not .9<=speed/refspeed<=1.1 or target<.08:return None
    if not all(math.isfinite(v) for v in (target,actual,speed,refspeed)):return None
    return dict(actual=actual*100,target=target*100,difference_pp=(actual-target)*100)

def live_steering(data,reference):
    """Wheel-angle comparison only; cannot establish tire slip or vehicle balance."""
    from .core import at
    p=data.get('LapDistPct');actual=data.get('SteeringWheelAngle')
    if not reference or p is None or actual is None or data.get('OnPitRoad') or data.get('IsOnTrack') is False:return None
    target=at(reference,p,'steer');speed=at(reference,p,'speed');current=data.get('Speed',0)
    if target is None or speed is None or speed<8 or abs(target)<.08 or actual*target<=0 or not .9<=current/speed<=1.1:return None
    if not all(math.isfinite(v) for v in (actual,target,speed,current)):return None
    return dict(actual_deg=math.degrees(abs(actual)),reference_deg=math.degrees(abs(target)),difference_deg=math.degrees(abs(actual)-abs(target)))

def steering_review(a,b):
    values=[]
    for s in a:
        target=live_steering(dict(LapDistPct=s.p,Speed=s.speed,SteeringWheelAngle=s.steer),b)
        if target:values.append(target['difference_deg'])
    if len(values)<5:return None
    import statistics
    return statistics.median(values)

def live_reason(review):
    """One teachable mechanism, phrased as a goal rather than a diagnosis."""
    metric=review.get('action_metric');brake=review.get('brake_m')
    if metric=='braking distance' and brake is not None:
        if brake<0:return 'The aim is to carry more entry speed while leaving room to release the brake smoothly.'
        return 'That gives you more room to bleed off the brake and settle the car onto its cornering line.'
    if metric=='brake input percentage points':
        if review.get('brake_delta_pp',0)>0:return 'A smaller peak may stop you shedding more speed than you need before the car turns.'
        return 'A little more initial braking can shorten the slowing phase and leave more room for a smooth release.'
    steer=review.get('steering_delta_deg')
    if steer is not None and abs(steer)>=8:
        if steer>0:return 'More steering asks more of the front tires. Extra lock may scrub speed once they reach their grip limit.'
        return 'Enough steering helps you hold the intended path, so you can straighten the car and build a cleaner exit.'
    if review.get('pickup_m') is not None and review['pickup_m']>=8:
        return 'Getting the car rotated first lets you build sustained throttle, carrying that acceleration onto the next straight.'
    return 'Entry, rotation and exit work together. Judge the change by the whole section, not just the braking point.'


def spoken_review(review,variant=0):
    """Live finding, one bounded action and its why; numbers stay reference-relative."""
    loss=review['loss'];tip=review.get('tip','')
    if not tip:return ''
    metric=review.get('action_metric');step=review.get('action_step');brake=review.get('brake_m');name=review['name'].lower()
    openings=(f'Into {name}, ',f'Looking back at {name}, ',f'One thing through {name}: ',f'For the next run through {name}, ')
    if metric=='braking distance' and step is not None and brake is not None:
        direction='earlier' if brake<0 else 'later';change='later' if brake<0 else 'earlier'
        finding=f'you braked {abs(brake):.0f} meters {direction} than your reference.'
        action=f'Next lap, move your marker {step:.0f} meters {change}.'
    elif metric=='brake input percentage points' and step is not None:
        delta=review.get('brake_delta_pp',0);direction='more' if delta>0 else 'less';change='less' if delta>0 else 'more'
        finding=f'your peak brake input was {abs(delta):.0f} percentage points {direction} than the reference.'
        action=f'Try {step:.0f} percentage points {change}, keeping the release smooth.'
    elif review.get('steering_delta_deg') is not None and abs(review['steering_delta_deg'])>=8 and (review.get('pickup_m') is None or review['pickup_m']<8):
        delta=review['steering_delta_deg'];direction='more' if delta>0 else 'less'
        finding=f'you used about {abs(delta):.0f} degrees {direction} wheel angle at similar speed.'
        action=f'If your steering ratio and line match, try a little {"less" if delta>0 else "more"} lock.'
    elif review.get('pickup_m') is not None and review['pickup_m']>=8:
        finding=f'you reached sustained throttle {review["pickup_m"]:.0f} meters later than the reference.'
        action='Focus on a smooth rotation and exit next lap.'
    else:
        lead=('We left about {loss:.1f} seconds in {name}. ', 'That section was about {loss:.1f} seconds slower through {name}. ', '{name} cost about {loss:.1f} seconds against the reference. ')
        if review.get('timing_estimated'):return 'Against the imported reference, '+tip[0].lower()+tip[1:]+' '+live_reason(review)
        index=(sum(ord(c) for c in review['name'])+variant)%len(lead)
        return lead[index].format(loss=max(0,loss),name=name)+tip+' '+live_reason(review)
    return openings[variant%len(openings)]+finding+' '+action+' '+live_reason(review)
