"""Synthetic demonstration, not a real circuit, car, lap or benchmark."""
import math
from .core import Sample

META = dict(track='Synthetic test circuit',config='Demo layout',track_id='demo-circuit',
            car='Demonstration vehicle',car_path='demo-vehicle',length=5000.,session_type='Demo',sim_session='demo')


def frame(t):
    lap = int(t//130)+1
    p = (t % 130)/130
    brake = 0.
    speed = 49.
    throttle = 1.
    steer = 0.
    # Deliberately illustrative zone positions; never used by the live coach.
    for apex in (.07,.19,.30,.43,.74):
        rel = p-apex
        if -.03 < rel < 0:
            brake = .65; throttle = 0.; speed = 24+25*(-rel/.03)
            steer = .15
        elif 0 <= rel < .045:
            speed = 24+25*(rel/.045); throttle = min(1,.25+rel*20); steer = .13
    # A modest artificial lateral variation for the line viewer.
    lateral = 0 if lap == 1 else 3*math.sin(p*math.pi*12)
    lat = 29.185+(.009+lateral/111320)*math.sin(p*math.tau)
    lon = -81.07+.016*math.cos(p*math.tau)
    return dict(SessionTime=t,SessionNum=0,Lap=lap,LapDistPct=p,LapCurrentLapTime=t%130,
                LapLastLapTime=130. if lap>1 else 0.,Speed=speed,Brake=brake,Throttle=throttle,
                LatAccel=steer*speed*.6,LongAccel=-6.4 if brake else 4.2 if throttle<.9 else 0.,SteeringWheelAngle=steer,RPM=5500.,Gear=4,IsOnTrack=True,OnPitRoad=False,
                PlayerTrackSurface=3,IsReplayPlaying=False,PlayerCarMyIncidentCount=0,
                SessionFlags=4,WeatherDeclaredWet=False,TrackWetness=1,AirTemp=24.,TrackTemp=31.,
                Precipitation=0.,Lat=lat,Lon=lon,dcABS=2,dcTractionControl=2,FuelLevel=35.-t*.003)
