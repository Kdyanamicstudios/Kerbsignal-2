"""Official Garage 61 API reference search. No scraping or embedded credentials."""
import csv
import io
import json
import math
from urllib.parse import urlencode,quote
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from .core import Sample
from dataclasses import asdict

API='https://garage61.net/api/v1'

class Garage61:
    def __init__(self,token):
        self.token=str(token).strip()
        if not self.token or '\n' in self.token or '\r' in self.token:raise ValueError('Enter a valid Garage 61 personal access token.')

    def get(self,path,params=None,csv_data=False):
        url=API+path+('?' + urlencode(params) if params else '')
        req=Request(url,headers={'Authorization':'Bearer '+self.token,'Accept':'text/csv' if csv_data else 'application/json','User-Agent':'RaceEngineer/0.8'})
        try:
            with urlopen(req,timeout=25) as r:
                raw=r.read(20_000_001)
        except HTTPError as exc:
            if exc.code==429:raise ValueError('Garage 61 rate limit reached. Wait before searching again.') from exc
            if exc.code in (401,403):raise ValueError('Garage 61 access denied. Check your token, driving-data permission and lap visibility.') from exc
            raise ValueError('Garage 61 request failed (HTTP '+str(exc.code)+').') from exc
        if len(raw)>20_000_000:raise ValueError('Reference response was too large.')
        return raw.decode('utf-8-sig') if csv_data else json.loads(raw)

    def candidates(self,profile):
        cars=self.get('/cars')['items'];tracks=self.get('/tracks')['items']
        car_id=str(profile.get('car_id',''))
        matched_cars=[c for c in cars if c.get('platform')=='iracing' and car_id and str(c.get('platform_id',''))==car_id]
        if len(matched_cars)!=1:raise ValueError('Could not map the exact iRacing car ID. Enter the car in an active session first.')
        matched_tracks=[t for t in tracks if t.get('platform')=='iracing' and str(t.get('platform_id',''))==str(profile.get('track_id'))]
        if len(matched_tracks)!=1:raise ValueError('Could not map the exact iRacing layout ID. No name-only guessing is used.')
        params=dict(cars=matched_cars[0]['id'],tracks=matched_tracks[0]['id'],unclean='false',lapTypes=1,age=-1,group='driver',limit=1000)
        items=[];total=0
        for offset in range(0,10000,1000):
            response=self.get('/laps',dict(params,offset=offset));page=response.get('items',[]);total=response.get('total',len(page))
            items.extend(page)
            if not page or len(items)>=total:break
        flags=('discontinuity','missing','incomplete','offtrack','pitlane','pitIn','pitOut','joker')
        valid=[x for x in items if x.get('clean') is True and x.get('canViewTelemetry') is True
            and not any(x.get(f,False) for f in flags)
            and isinstance(x.get('lapTime'),(int,float)) and x['lapTime']>0
            and x.get('car',{}).get('id')==matched_cars[0]['id'] and x.get('track',{}).get('id')==matched_tracks[0]['id']]
        valid.sort(key=lambda x:x['lapTime'])
        if not valid:raise ValueError('No downloadable clean reference is visible to this account for the current car/layout. API access may be limited to your own/team laps.')
        return valid,dict(searched=len(items),total=total,complete=len(items)>=total,current_season=True)

    def download(self,lap):return self.get('/laps/'+quote(str(lap['id']),safe='')+'/csv',csv_data=True)


def csv_reference(text,lap,profile,conditions):
    """Import native Garage 61 columns. Missing time is explicitly reconstructed."""
    rows=list(csv.DictReader(io.StringIO(text)))
    required={'Speed','LapDistPct','Brake','Throttle','SteeringWheelAngle'}
    if not rows or not required.issubset(rows[0]):raise ValueError('Unsupported CSV. Expected Garage 61 native Speed/LapDistPct/Brake/Throttle/SteeringWheelAngle columns.')
    if not 100<=len(rows)<=200000:raise ValueError('Reference sample count is invalid.')
    samples=[]
    for row in rows:
        try:
            speed,p,brake,throttle,steer=[float(row[k]) for k in ('Speed','LapDistPct','Brake','Throttle','SteeringWheelAngle')]
            if not all(math.isfinite(v) for v in (speed,p,brake,throttle,steer)):raise ValueError()
            if not 0<=p<=1 or not 0<=brake<=1 or not 0<=throttle<=1 or not 0<speed<150:raise ValueError()
            if row.get('PositionType') and int(row['PositionType'])!=3:raise ValueError('CSV includes pit/off-track/unknown samples.')
            lat=float(row['Lat']) if row.get('Lat') else None;lon=float(row['Lon']) if row.get('Lon') else None
            if lat is not None and (not math.isfinite(lat) or not -90<=lat<=90):raise ValueError()
            if lon is not None and (not math.isfinite(lon) or not -180<=lon<=180):raise ValueError()
            if samples and p==samples[-1].p:continue
            if samples and (p<samples[-1].p or p-samples[-1].p>.008):raise ValueError('CSV has a distance reset or a data gap.')
            dt=0 if not samples else (p-samples[-1].p)*profile['length']/((speed+samples[-1].speed)/2)
            if dt>.25:raise ValueError('CSV has a telemetry gap longer than 250 ms.')
            t=0 if not samples else samples[-1].t+dt
            samples.append(Sample(t,p,speed,brake,throttle,steer,lat,lon))
        except (TypeError,ValueError,KeyError) as exc:raise ValueError('Invalid or incomplete Garage 61 CSV: '+str(exc)) from exc
    if samples[0].p>.003 or samples[-1].p<.997:raise ValueError('CSV does not cover a complete start-to-finish lap.')
    lap_time=float(lap['lapTime'])
    estimated=samples[-1].t+samples[0].p*profile['length']/samples[0].speed+(1-samples[-1].p)*profile['length']/samples[-1].speed
    if abs(estimated-lap_time)>max(1.,lap_time*.03):raise ValueError('CSV speed/distance timing does not agree with the declared lap time. Baseline rejected.')
    prefix=samples[0].p*profile['length']/samples[0].speed
    for s in samples:s.t=(s.t+prefix)*lap_time/estimated
    first,last=samples[0],samples[-1]
    if first.p>0:samples.insert(0,Sample(0,0,first.speed,first.brake,first.throttle,first.steer,first.lat,first.lon))
    if last.p<1:samples.append(Sample(lap_time,1,last.speed,last.brake,last.throttle,last.steer,last.lat,last.lon))
    return dict(format='race-engineer-reference-v1',profile=profile,lap_time=lap_time,context=list(conditions),
        label='Garage 61 accessible reference; world-record status unverified',
        provenance=dict(provider='Garage 61',lap_id=lap['id'],driver=lap.get('driver'),start_time=lap.get('startTime'),
            conditions={k:lap.get(k) for k in ('trackTemp','trackWetness','fuelLevel','tireCompound','weightPenalty','powerAdjust')},
            derived_time=True,conditions_confirmed_by_user=True),samples=[asdict(s) for s in samples])
