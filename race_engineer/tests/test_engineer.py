import json
import math
from pathlib import Path
import sqlite3
import struct
import tempfile
import unittest

from engineer.core import Coach, Sample, compare, context, line_offset, reference_payload, supported
from engineer.demo import META, frame
from engineer.sdk import decode, metadata
from engineer.storage import Store


class CoachingTests(unittest.TestCase):
    def run_laps(self, change=None, end=391):
        coach=Coach(); laps=[]
        for tick in range(2580,int(end*20)):
            d=frame(tick/20)
            if change:change(d)
            lap,_=coach.update(d,META)
            if lap:laps.append(lap)
        return coach,laps

    def test_full_lap_timing_and_reference(self):
        coach,laps=self.run_laps()
        self.assertEqual(len(laps),2)
        self.assertTrue(all(l['clean'] for l in laps))
        self.assertAlmostEqual(laps[0]['lap_time'],130,places=4)
        self.assertTrue(coach.zones)
        self.assertTrue(laps[-1]['reviews'])
        self.assertTrue(all(abs(r['loss'])<.001 for r in laps[-1]['reviews']))

    def test_incident_excludes_reference(self):
        def change(d):
            if d['SessionTime']>=190:d['PlayerCarMyIncidentCount']=1
        c,laps=self.run_laps(change,end=261)
        self.assertFalse(laps[0]['clean'])
        self.assertIn('incident',laps[0]['reasons'])
        self.assertFalse(c.reference)

    def test_pit_offtrack_and_missing_incidents(self):
        for key,value in [('OnPitRoad',True),('PlayerTrackSurface',0),('PlayerCarMyIncidentCount',None)]:
            def change(d):
                if 180<d['SessionTime']<185:d[key]=value
            c,laps=self.run_laps(change,end=261)
            self.assertFalse(laps[0]['clean'],key)
            self.assertFalse(c.reference,key)

    def test_changed_aids_reset_reference(self):
        c,laps=self.run_laps(end=261)
        self.assertTrue(c.reference)
        d=frame(261);d['dcABS']=3
        c.update(d,META)
        self.assertFalse(c.reference)
        self.assertIn('weather or ABS/TC changed',c.invalid)

    def test_gaps_do_not_create_reference(self):
        c=Coach();laps=[]
        for tick in range(2580,5220):
            if 3600<tick<3650:continue
            lap,_=c.update(frame(tick/20),META)
            if lap:laps.append(lap)
        self.assertFalse(laps[0]['clean'])
        self.assertIn('telemetry gap / reset',laps[0]['reasons'])

    def test_line_separation_is_meters_not_time(self):
        lat=29.
        reference=[Sample(i/10,i/1000,30,0,1,0,lat,-81+i*.000001) for i in range(1000)]
        s=Sample(5,.5,30,0,1,0,lat+3/111320,-80.9995)
        self.assertAlmostEqual(line_offset(s,reference),3,places=5)
        self.assertIsNone(line_offset(Sample(0,0,20,0,1,0),reference))

    def test_compare_reports_observed_loss(self):
        ref=[Sample(p*100,p,30 if .45<p<.55 else 50, .7 if .4<p<.45 else 0,0 if .4<p<.5 else 1,0) for p in [i/1000 for i in range(1001)]]
        cur=[Sample(s.t+max(0,s.p-.35)*2,s.p,s.speed,s.brake,s.throttle,s.steer) for s in ref]
        r=compare(cur,ref,dict(name='Test zone',start=.35,end=.6),5730)
        self.assertAlmostEqual(r['loss'],.5,places=3)
        self.assertEqual(r['brake_m'],0)

    def test_voice_suppressed_during_braking_and_flags(self):
        c=Coach();d=frame(160);d['Brake']=.7
        c.pending=[(160,'Advice')]
        self.assertIsNone(c.voice(d))
        d.update(Brake=0,Throttle=1,SteeringWheelAngle=0,Speed=40,SessionFlags=8)
        self.assertIsNone(c.voice(d))
        d['SessionFlags']=4
        self.assertEqual(c.voice(d),'Advice')
        c.pending=[(120,'stale')]
        self.assertIsNone(c.voice(d))

    def test_reference_roundtrip_and_layout_guard(self):
        c,laps=self.run_laps(end=261)
        payload=reference_payload(laps[0],META)
        restored=Coach();restored.import_reference(payload,META,context(frame(261)))
        self.assertEqual(len(restored.reference),len(c.reference))
        with self.assertRaises(ValueError):restored.import_reference(payload,{**META,'config':'Oval'})
        with self.assertRaises(ValueError):restored.import_reference(payload,META,(False,1,3,2))
        self.assertTrue(supported({**META,'car':'Porsche','car_path':'porsche'}))


class SDKTests(unittest.TestCase):
    def fixture(self):
        names=[('SessionTime',5,123.5),('Speed',4,40.),('LapDistPct',4,.25),('PlayerCarIdx',2,0),('SessionNum',2,0)]
        b=bytearray(4096)
        text=b'''WeekendInfo:\n TrackDisplayName: Daytona International Speedway\n TrackConfigName: Road Course\n TrackID: 192\n TrackLength: 5.73 km\n SubSessionID: 123\nSessionInfo:\n Sessions:\n - SessionNum: 0\n   SessionType: Race\nDriverInfo:\n Drivers:\n - CarIdx: 0\n   CarPath: toyotagr86\n   CarScreenName: Toyota GR86\n - CarIdx: 1\n   CarPath: other\n   CarScreenName: Other Car\n'''
        struct.pack_into('<12i',b,0,2,1,60,1,len(text),1024,len(names),128,1,128,0,0)
        struct.pack_into('<4i',b,48,42,2048,42,0)
        b[1024:1024+len(text)]=text
        offset=0
        for i,(name,typ,value) in enumerate(names):
            v=128+i*144
            struct.pack_into('<iii',b,v,typ,offset,1)
            b[v+16:v+16+len(name)]=name.encode()
            fmt='<'+{2:'i',4:'f',5:'d'}[typ]
            struct.pack_into(fmt,b,2048+offset,value);offset+=struct.calcsize(fmt)
        return b

    def test_binary_decode_and_player_identity(self):
        result=decode(self.fixture())
        tick,d,m=result
        self.assertEqual(tick,42);self.assertEqual(d['Speed'],40.)
        self.assertEqual(m['car'],'Toyota GR86');self.assertEqual(m['session_type'],'Race')
        self.assertEqual(m['length'],5730)
        self.assertTrue(supported(m))

    def test_torn_buffer_and_disconnection(self):
        b=self.fixture();struct.pack_into('<i',b,56,43)
        self.assertIsNone(decode(b))
        b=self.fixture();struct.pack_into('<i',b,4,0)
        self.assertIsNone(decode(b))

    def test_invalid_offsets_rejected(self):
        b=self.fixture();struct.pack_into('<i',b,28,99999)
        with self.assertRaises(ValueError):decode(b)


class StorageTests(unittest.TestCase):
    def test_history_survives_reopen(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'history.sqlite3'
            db=Store(path);db.start('DEMO',META,130)
            db.record(frame(131))
            lap=dict(lap=2,lap_time=130,clean=True,reasons=[],samples=[Sample.from_data(frame(131))],reviews=[],context=context(frame(131)))
            db.lap(lap);db.close()
            db=Store(path)
            self.assertEqual(len(db.history()),1)
            self.assertEqual(db.history()[0][5],'DEMO')
            stored=db.get_lap(1)
            self.assertEqual(stored['lap_time'],130)
            self.assertEqual(len(stored['samples']),1)
            self.assertEqual(db.sessions()[0][4],1)
            db.close()


if __name__=='__main__':unittest.main()
