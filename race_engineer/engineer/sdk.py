"""Read-only iRacing shared-memory reader. No network or sim control commands."""
import ctypes
import math
import re
import struct
import sys
import time
import yaml

FORMATS = {0: 'c', 1: '?', 2: 'i', 3: 'I', 4: 'f', 5: 'd'}
WANTED = set('PitSvStatus PitSvFlags SessionTimeRemain SessionLapsRemainEx SessionState PlayerCarPosition PlayerCarClassPosition FuelLevelPct LapBestLapTime LapDeltaToSessionBestLap LapDeltaToSessionBestLap_OK CarIdxLapDistPct CarIdxTrackSurface CarIdxOnPitRoad CarLeftRight SessionTime SessionNum Lap LapCompleted LapDistPct LapDist LapCurrentLapTime LapLastLapTime Speed RPM Gear Throttle Brake SteeringWheelAngle LongAccel LatAccel Yaw YawNorth IsOnTrack OnPitRoad PlayerTrackSurface IsReplayPlaying PlayerCarIdx PlayerCarMyIncidentCount PlayerCarDriverIncidentCount SessionFlags AirTemp TrackTemp TrackTempCrew Precipitation TrackWetness WeatherDeclaredWet Lat Lon Alt dcABS dcTractionControl dcTractionControl2 dcBrakeBias dcThrottleShape dcEnginePower dcFuelMixture dcDiffEntry dcDiffMid dcDiffExit dcFrontWing dcRearWing FuelLevel'.split())
for wheel in ('LF', 'RF', 'LR', 'RR'):
    WANTED.update(wheel + suffix for suffix in ('tempCL', 'tempCM', 'tempCR', 'wearL', 'wearM', 'wearR', 'pressure'))


def fields(text):
    # Deliberately extracts a small whitelist of scalar metadata, not a YAML parser.
    return {m.group(1): m.group(2).strip().strip('\"\'') for m in re.finditer(r'^[ \t]*([A-Za-z][A-Za-z0-9]*):[ \t]*([^\r\n]*)$', text, re.M)}


def setup_scalars(text):
    """Read bounded scalar garage values; never execute YAML tags or parse notes."""
    section=re.search(r'(?m)^CarSetup:[ \t]*\r?$',text)
    if not section:return {}
    stack=[];result={}
    for line in text[section.end():].splitlines():
        if not line.strip():continue
        if not line[0].isspace():break
        m=re.match(r'^( *)([A-Za-z][A-Za-z0-9_-]*):[ \t]*(.*)$',line)
        if not m:continue
        indent,key,value=len(m[1]),m[2],m[3].strip()
        while stack and stack[-1][0]>=indent:stack.pop()
        if not value:
            stack.append((indent,key));continue
        if value.startswith(('!','|','>','{','[')) or any('note' in k.lower() for _,k in stack) or 'note' in key.lower():continue
        result['.'.join([k for _,k in stack]+[key])]=value.strip('\"\'')[:120]
        if len(result)>=120:break
    return result


def legacy_metadata(text, player, session_num):
    weekend = text.split('WeekendInfo:', 1)[-1].split('\nSessionInfo:', 1)[0]
    w = fields(weekend)
    car = {}
    driver_text = text.split('\nDrivers:', 1)[-1] if '\nDrivers:' in text else text
    for block in re.split(r'(?m)^\s*-\s*CarIdx:\s*', driver_text)[1:]:
        if block.splitlines()[0].strip() == str(player):
            car = fields(block)
            break
    session_type = 'Unknown'
    for block in re.split(r'(?m)^\s*-\s*SessionNum:\s*', text)[1:]:
        if block.splitlines()[0].strip() == str(session_num):
            session_type = fields(block).get('SessionType', 'Unknown')
            break
    length = w.get('TrackLength', '')
    try:
        meters = float(length.split()[0]) * (1000 if 'km' in length else 1609.344)
    except (ValueError, IndexError):
        meters = 0
    driver_header=text.split('DriverInfo:',1)[-1].split('Drivers:',1)[0]
    driver=fields(driver_header)
    return dict(pit_speed_mps=pit_speed(w.get('TrackPitSpeedLimit')),track_name=w.get('TrackName',''),track=w.get('TrackDisplayName', w.get('TrackName', 'Unknown')),
                config=w.get('TrackConfigName', 'Unknown'), track_id=w.get('TrackID', ''),
                car=car.get('CarScreenName') or car.get('CarPath') or 'Unknown',
                car_path=car.get('CarPath', ''), car_id=car.get('CarID',''),
                car_class=car.get('CarClassShortName',car.get('CarClassName','')),
                car_class_id=car.get('CarClassID',''),player_car_idx=player,
                setup_name=driver.get('DriverSetupName','').replace('\\','/').split('/')[-1],
                car_setup=setup_scalars(text),length=meters, session_type=session_type,
                sim_session=w.get('SubSessionID', w.get('SessionID', '')))


def pit_speed(value):
    m=re.search(r'([0-9]+(?:\.[0-9]+)?)\s*(kph|km/h|mph|m/s)',str(value),re.I)
    return float(m[1])*{'kph':1/3.6,'km/h':1/3.6,'mph':.44704,'m/s':1}[m[2].lower()] if m else None

def metadata(text,player,session_num):
    """Parse real SDK YAML by section; a missing config name is not a missing track."""
    try:
        root=yaml.load(text,Loader=getattr(yaml,'CSafeLoader',yaml.SafeLoader))
        if not isinstance(root,dict):raise ValueError('Empty SDK session document')
        w=root.get('WeekendInfo') or {};info=root.get('DriverInfo') or {}
        drivers=info.get('Drivers') or []
        car=next((c for c in drivers if str(c.get('CarIdx'))==str(player)),{})
        sessions=(root.get('SessionInfo') or {}).get('Sessions') or []
        session=next((s for s in sessions if str(s.get('SessionNum'))==str(session_num)),{})
        length=str(w.get('TrackLength') or w.get('TrackLengthOfficial') or '')
        m=re.search(r'([0-9]+(?:\.[0-9]+)?)\s*(km|mi|m)\b',length,re.I)
        meters=float(m[1])*{'km':1000.,'mi':1609.344,'m':1.}[m[2].lower()] if m else 0.
        return dict(pit_speed_mps=pit_speed(w.get('TrackPitSpeedLimit')),track=str(w.get('TrackDisplayName') or w.get('TrackName') or 'Unknown'),
            track_name=str(w.get('TrackName') or ''),config=str(w.get('TrackConfigName') or ''),
            track_id=str(w.get('TrackID') or ''),length=meters,
            car=str(car.get('CarScreenName') or car.get('CarPath') or 'Unknown'),
            car_path=str(car.get('CarPath') or ''),car_id=str(car.get('CarID') or ''),
            car_class=str(car.get('CarClassShortName') or car.get('CarClassName') or ''),
            car_class_id=str(car.get('CarClassID') or ''),player_car_idx=player,
            setup_name=str(info.get('DriverSetupName') or '').replace('\\','/').split('/')[-1],
            car_setup=setup_scalars(text),session_type=str(session.get('SessionType') or 'Unknown'),
            sim_session=str(w.get('SubSessionID') or w.get('SessionID') or ''),metadata_source='SDK session YAML')
    except (yaml.YAMLError,ValueError,TypeError,AttributeError):
        result=legacy_metadata(text,player,session_num)
        if result['config']=='Unknown':result['config']=''
        result['metadata_source']='SDK scalar fallback'
        return result


def decode(mapping, names=WANTED, cache=None):
    """Return a coherent packet or None. Also used with synthetic test fixtures."""
    if len(mapping) < 112:
        raise ValueError('SDK header too short')
    h = struct.unpack_from('<12i', mapping)
    version, status, rate, update, slen, soff, nvars, voff, nbuf, blen = h[:10]
    if not status & 1:
        return None
    if not (1 <= version <= 100 and 1 <= nbuf <= 4 and 0 < nvars < 5000 and 0 < blen <= len(mapping)):
        raise ValueError('Unsupported SDK header')
    if min(soff, slen, voff) < 0 or soff+slen > len(mapping) or voff+nvars*144 > len(mapping):
        raise ValueError('SDK table outside mapping')
    candidates = sorted((struct.unpack_from('<iii', mapping, 48+i*16) + (i,) for i in range(nbuf)), reverse=True)
    for tick, offset, begin, i in candidates:
        if begin not in (0, tick) or not (112 <= offset <= len(mapping)-blen):
            continue
        raw = bytes(mapping[offset:offset+blen])
        end_tick, end_offset, end_begin = struct.unpack_from('<iii', mapping, 48+i*16)
        if (end_tick, end_offset, end_begin) != (tick, offset, begin):
            continue
        data = {}
        schema_key=(update,nvars,voff,blen,id(names))
        schema=cache.get('schema') if cache is not None and cache.get('schema_key')==schema_key else None
        if schema is None:
            schema=[]
            for v in range(nvars):
                pos=voff+v*144
                typ,off,count=struct.unpack_from('<iii',mapping,pos)
                name=bytes(mapping[pos+16:pos+48]).split(b'\0')[0].decode('ascii','replace')
                selected=name in names or (names is WANTED and name.startswith('dc') and typ in (1,2,3,4,5) and count==1)
                if selected and typ in FORMATS and 1<=count<=1000:schema.append((name,typ,off,count))
            if cache is not None:cache.update(schema_key=schema_key,schema=schema)
        for name,typ,off,count in schema:
            fmt = '<' + FORMATS[typ]*count
            if off < 0 or off+struct.calcsize(fmt) > len(raw):
                raise ValueError('SDK variable outside buffer')
            value = struct.unpack_from(fmt, raw, off)
            value = value[0] if count == 1 else list(value)
            if isinstance(value, float) and not math.isfinite(value):
                value = None
            if isinstance(value,list):value=[None if isinstance(v,float) and not math.isfinite(v) else v for v in value]
            data[name] = value
        # Session string has a separate sequence number.
        meta_key=(update,soff,slen,data.get('PlayerCarIdx',-1),data.get('SessionNum',-1))
        meta=cache.get('meta') if cache is not None and cache.get('meta_key')==meta_key else None
        if meta is None:
            session_text=bytes(mapping[soff:soff+slen]).rstrip(b'\0').decode('utf-8-sig','replace')
            meta=metadata(session_text,data.get('PlayerCarIdx',-1),data.get('SessionNum',-1))
            if cache is not None:cache.update(meta_key=meta_key,meta=meta)
        if struct.unpack_from('<i', mapping, 12)[0] != update:
            return None
        data['TelemetryAgeSeconds']=max(0,(candidates[0][0]-tick)/rate) if rate>0 else 0.
        return tick,data,meta
    return None


class LiveReader:
    def __init__(self):
        self.handle = self.view = self.kernel = None
        self.last_tick = None
        self.size = 1164*1024
        self.cache={}

    def close(self):
        if self.view:
            self.kernel.UnmapViewOfFile(self.view)
        if self.handle:
            self.kernel.CloseHandle(self.handle)
        self.handle = self.view = None
        self.last_tick = None
        self.cache.clear()

    def read(self):
        if sys.platform != 'win32':
            raise OSError('Live telemetry needs Windows. Use Demo on this computer.')
        if not self.handle:
            from ctypes import wintypes
            k = ctypes.WinDLL('kernel32', use_last_error=True)
            k.OpenFileMappingW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
            k.OpenFileMappingW.restype = wintypes.HANDLE
            k.MapViewOfFile.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD, ctypes.c_size_t]
            k.MapViewOfFile.restype = ctypes.c_void_p
            k.UnmapViewOfFile.argtypes = [ctypes.c_void_p]
            k.CloseHandle.argtypes = [wintypes.HANDLE]
            self.kernel = k
            self.handle = k.OpenFileMappingW(4, False, 'Local\\IRSDKMemMapFileName')
            if not self.handle:
                raise OSError('Waiting for iRacing. Join a session and enter the car.')
            self.view = k.MapViewOfFile(self.handle, 4, 0, 0, self.size)
            if not self.view:
                self.close()
                raise OSError('Could not map iRacing telemetry.')
        # Only reads existing sim memory. Never creates a named map.
        mapping = (ctypes.c_ubyte*self.size).from_address(self.view)
        begin=time.monotonic()
        packet = decode(memoryview(mapping).cast('B'),cache=self.cache)
        if packet is None:
            self.close()
            raise OSError('Waiting for active iRacing telemetry.')
        tick, data, meta = packet
        data['TelemetryAgeSeconds']+=time.monotonic()-begin
        data['_host_time']=time.monotonic()
        if tick == self.last_tick:
            return None
        self.last_tick = tick
        return data, meta
