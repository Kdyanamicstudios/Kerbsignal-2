"""Position-based coaching plans: video notes are not video timestamps at runtime."""
import math

SOURCES=[
 dict(name='iRacing Driving School',url='https://www.youtube.com/playlist?list=PLqZLBOpI5JFKQBrhCnOQHRCfm1aVY3wo4',note='Official video lessons on corner approach, braking and driving technique. Source: iRacing Driving School page.'),
 dict(name='Driver61 circuit guides',url='https://driver61.com/circuit-guide/',note='Circuit walkthroughs and visual landmarks; align a landmark to the exact simulator layout before using a timed call.'),
 dict(name='Driver61 braking references',url='https://www.youtube.com/watch?v=sZG1P5hS5u4',note='Use a repeatable visual braking reference and make deliberate changes rather than relying on a lap timer. Linked from Driver61’s braking lesson.'),
 dict(name='Almeida: brake release / rotation',url='https://www.youtube.com/watch?v=RrfVAtAUhrE',note='Linked from the coach’s Spa/Radical case study: brake release and steering must work together. Technique example, not a universal braking-marker dataset.')]


def profile_key(meta):return tuple(str(meta.get(k,'')) for k in ('track_id','config','car_path','car_id'))


def validate_guide(payload,meta):
    if not isinstance(payload,dict) or not isinstance(payload.get('profile'),dict):raise ValueError('Guide and profile must be JSON objects.')
    if payload.get('format')!='race-engineer-coach-v1':raise ValueError('Expected a position coaching guide.')
    if profile_key(payload.get('profile',{}))!=profile_key(meta):raise ValueError('Guide does not match the exact current car and track/layout IDs.')
    if abs(float(payload['profile'].get('length',0))-meta['length'])>5:raise ValueError('Guide track length differs.')
    plans=payload.get('corners')
    if not isinstance(plans,list) or not 1<=len(plans)<=200:raise ValueError('Guide needs 1–200 corner plans.')
    output=[]
    for i,plan in enumerate(plans):
        if not isinstance(plan,dict):raise ValueError('Each corner must be a JSON object.')
        row={'name':str(plan.get('name') or f'Corner {i+1}')[:80]}
        for k in ('brake','hold','release','turn','unwind','throttle','end'):
            v=plan.get(k)
            if v is not None and (not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<=1):raise ValueError('Cue positions must be lap fractions between zero and one.')
            row[k]=v
        start=row['brake'] if row['brake'] is not None else row['turn']
        if start is None or row['end'] is None or row['end']<=start:raise ValueError('Each corner needs a brake/turn marker and a later end marker. Split start/finish-spanning corners.')
        if any(v is not None and not start<=v<=row['end'] for k,v in row.items() if k in ('hold','release','turn','unwind','throttle')):raise ValueError('Phase markers must be inside their corner.')
        for label,allowed in (('direction',('left','right','left-right')),('kind',('turn','hairpin','sweeper','chicane','slow turn','medium turn','fast turn'))):
            if label in plan:
                value=str(plan[label]).casefold()
                if value not in allowed:raise ValueError('Unknown corner direction/type')
                row[label]=value
        output.append(row)
    result=dict(payload);result['corners']=sorted(output,key=lambda p:p['brake'] if p['brake'] is not None else p['turn'])
    return result
