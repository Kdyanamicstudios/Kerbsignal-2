"""All-car setup test hypotheses; numeric mappings require a verified car profile."""
import statistics

SYMPTOMS = ('Mid-corner understeer','Mid-corner oversteer','Exit wheelspin','Braking lockup / instability','Entry understeer','No specific handling issue')


def assess(laps):
    if len(laps)<3:
        return False,f'Need {3-len(laps)} more clean measured laps (plus the initial warm-up lap).'
    times=[l['lap_time'] for l in laps[-5:]]
    median=statistics.median(times)
    if max(times)-min(times)>max(1.5,median*.008):
        return False,'Lap-to-lap variation is too large. Improve consistency before judging a setup change.'
    from .time_format import elapsed
    return True,f'{len(times)} clean laps; median {elapsed(median,3)}; spread {max(times)-min(times):.3f}s.'


def recommendation(laps,symptom,garage,arb_size,arb_setting,profile=None):
    ready,report=assess(laps)
    if not ready:return report
    intro=report+'\nDriver-reported symptom: '+symptom+'. This is a test hypothesis, not an automatic handling diagnosis.\n'
    if garage!='Open / adjustable':
        return intro+'Verify which controls the series permits. Garage hardware changes are not recommended while the setup is fixed or unknown. Review driving inputs first.'
    return intro+universal_recommendation(laps,symptom,profile or {})


def universal_recommendation(laps,symptom,profile):
    name=profile.get('car','Current car')
    intro=name+': '
    if symptom in ('Mid-corner understeer','Mid-corner oversteer'):
        candidates=[]
        for key,value in profile.get('car_setup',{}).items():
            compact=''.join(c for c in key.lower() if c.isalpha())
            if 'front' in compact and any(word in compact for word in ('arb','antiroll','swaybar')):
                candidates.append((key,value))
        if candidates:
            key,value=candidates[0];direction='softer' if symptom=='Mid-corner understeer' else 'stiffer'
            return intro+f'The SDK reports {key} = {value}. If this is a connected adjustable front anti-roll bar, test one documented step {direction}. Confirm the direction in this car’s garage; numeric settings are not assumed. Change nothing else, then repeat the measured run.'
        return intro+'Review steering, minimum speed and throttle against this same car’s clean reference. A front anti-roll bar adjustment is not proposed until an adjustable control is identified in this car’s garage. Record a verified single change and compare another run.'
    if symptom in ('Exit wheelspin','Braking lockup / instability'):
        key='tc' if symptom=='Exit wheelspin' else 'abs'
        label='traction control' if key=='tc' else 'ABS'
        values=[l.get(key) for l in laps]
        stable=values and all(isinstance(v,(int,float)) for v in values) and len(set(values))==1
        technique='Apply throttle progressively as steering unwinds' if key=='tc' else 'Compare peak brake pressure and brake release with this car’s clean reference'
        if stable:
            return intro+f'{technique}. The reported {label} setting is {values[-1]}. If the car and series allow adjustment, test one documented step toward more assistance after confirming its range and direction in this car. A larger number is not assumed to mean more assistance. This does not confirm measured wheelspin or lockup.'
        return intro+technique+'. The relevant aid setting is unavailable or unstable, so an ABS/TC setting change is not proposed. Judge the result with another consistent measured run.'
    return intro+'Use this car’s braking and throttle reference to investigate the reported issue. Lap times alone do not identify a hardware fix. Record a single verified garage change, then compare consistent runs under matching conditions.'


def verdict(baseline,test,controlled):
    for label,group in (('Baseline',baseline),('Changed run',test)):
        ready,reason=assess(group)
        if not ready:return label+': '+reason
    if not controlled:
        return 'Comparison pending: confirm comparable fuel loads, tire condition, and clear traffic for both runs.'
    b,t=baseline[-5:],test[-5:]
    if len({x.get('wetness') for x in b+t})!=1:
        return 'Inconclusive: track wetness changed between the runs.'
    for key,limit,label in (('track_temp',3.,'track temperature'),('fuel',5.,'fuel load')):
        if any(not isinstance(x.get(key),(int,float)) for x in b+t):
            return f'Inconclusive: {label} telemetry is unavailable.'
        if abs(statistics.median(x[key] for x in b)-statistics.median(x[key] for x in t))>limit:
            return f'Inconclusive: {label} differs too much between the runs.'
    bm,tm=statistics.median(x['lap_time'] for x in b),statistics.median(x['lap_time'] for x in t)
    delta=tm-bm
    noise=max(.15,statistics.pstdev(x['lap_time'] for x in b)+statistics.pstdev(x['lap_time'] for x in t))
    from .time_format import elapsed
    result=f'Baseline median {elapsed(bm,3)}; changed-run median {elapsed(tm,3)} ({delta:+.3f}s). '
    if abs(delta)<=noise:
        return result+'Inconclusive: difference is within the run variation. Repeat the test.'
    return result+('The changed run was faster; repeat to confirm before keeping it.' if delta<0 else 'The changed run was slower; consider reverting and repeating.')+' This is an observed result, not proof that the setup caused it.'
