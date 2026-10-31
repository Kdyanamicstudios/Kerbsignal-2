"""Live SDK lap position with GPS validation and a persisted, observed route map."""
from collections import deque
import hashlib
import json
import math
from pathlib import Path
import time
from .map_atlas import MapAtlas

MPH=2.2369362920544


def finite(v):return isinstance(v,(int,float)) and math.isfinite(v)


class PositionTracker:
    def __init__(self,folder):
        self.folder=Path(folder);self.key=None;self.route={};self.trace=deque(maxlen=2400)
        self.current={};self.last_wall=0.;self.last_gps=None;self.gps_changed=0.;self.saved=False
        self.sdk_age=0.;self.layout={};self.map_source='Observed GPS route'

    def select(self,meta):
        key=(str(meta.get('track_id','')),str(meta.get('config','')))
        if key==self.key:return
        self.key=key;self.route={};self.trace.clear();self.current={};self.last_gps=None;self.saved=False
        atlas=MapAtlas().load(meta)
        self.layout={round(p*1000):(p,lat,lon) for p,lat,lon in atlas['points']} if atlas else {}
        self.map_source=atlas['source'] if atlas else 'Observed GPS route'
        self.file=self.folder/(hashlib.sha256(json.dumps(key).encode()).hexdigest()+'.json')
        try:
            points=json.loads(self.file.read_text())['points']
            for p,lat,lon in points:
                if all(finite(v) for v in (p,lat,lon)) and 0<=p<=1 and -90<=lat<=90 and -180<=lon<=180:
                    self.route[round(p*1000)]=(p,lat,lon)
            self.saved=True
        except (OSError,ValueError,KeyError,TypeError):pass

    def seed(self,samples):
        for s in samples:
            if finite(s.lat) and finite(s.lon) and (abs(s.lat)+abs(s.lon))>.001:
                self.route.setdefault(round(s.p*1000),(s.p,s.lat,s.lon))

    def update(self,d,meta,now=None):
        now=time.monotonic() if now is None else now;self.select(meta)
        p=d.get('LapDistPct');length=meta.get('length',0)
        valid=finite(p) and 0<=p<=1 and finite(length) and length>100
        lat,lon=d.get('Lat'),d.get('Lon');gps=all(finite(v) for v in (lat,lon)) and -90<=lat<=90 and -180<=lon<=180 and abs(lat)+abs(lon)>.001
        if gps:
            if self.last_gps!=(lat,lon):self.gps_changed=now;self.last_gps=(lat,lon)
            if d.get('Speed',0)>5 and now-self.gps_changed>.6:gps=False
        source='SDK GPS + lap distance' if gps and valid else 'SDK lap distance' if valid else 'position unavailable'
        if gps and valid:
            self.route[round(p*1000)]=(p,lat,lon);self.trace.append((p,lat,lon))
        elif valid:
            lat=lon=None
            near=self.route.get(round(p*1000)) or self.layout.get(round(p*1000))
            if near and self.has_geometry():
                _,lat,lon=near;source='SDK lap distance on map (estimated XY)'
        else:lat=lon=None
        self.current=dict(valid=valid,track_id=meta.get('track_id'),track=meta.get('track'),layout=meta.get('config') or 'Default layout',
            lap=d.get('Lap'),lap_fraction=p if valid else None,lap_percent=round(p*100,2) if valid else None,
            distance_m=round(p*length,1) if valid else None,latitude=lat,longitude=lon,source=source,gps_live=bool(gps))
        self.last_wall=now
        self.sdk_age=max(0,d.get('TelemetryAgeSeconds',0))
        if not self.saved and len(self.route)>880 and self.has_geometry():
            self.folder.mkdir(parents=True,exist_ok=True)
            self.file.write_text(json.dumps({'points':sorted(self.route.values())}));self.saved=True
        return self.current

    def has_geometry(self):
        points=list((self.layout or self.route).values())
        return len(points)>5 and (max(x[1] for x in points)-min(x[1] for x in points)>1e-4 or max(x[2] for x in points)-min(x[2] for x in points)>1e-4)

    def snapshot(self,now=None):
        now=time.monotonic() if now is None else now
        result=dict(self.current);age=max(0,now-self.last_wall)+self.sdk_age
        result['age_ms']=round(age*1000)
        if age>.35:result.update(valid=False,source='telemetry stale')
        return result


class SignalTrace:
    def __init__(self):self.points=deque(maxlen=4000)
    def clear(self):self.points.clear()
    def append(self,d):
        if all(finite(d.get(k)) for k in ('SessionTime','Speed','Brake','Throttle')):
            if self.points and d['SessionTime']<=self.points[-1][0]:self.points.clear()
            self.points.append((d['SessionTime'],d['Speed']*MPH,d['Brake'],d['Throttle'],d.get('LapDistPct'),d.get('SteeringWheelAngle')))
    def window(self,seconds=30):
        if not self.points:return []
        start=self.points[-1][0]-seconds
        return [p for p in self.points if p[0]>=start]
