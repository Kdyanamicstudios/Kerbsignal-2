from test_controller import headless_services
"""Synthetic SDK/controller checks for arbitrary cars, including mixed-class grids."""
import base64
import json
import os
import tempfile
import time
import struct
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import app
from engineer.cars import car_identity
from engineer.core import Coach, supported
from engineer.demo import META, frame
from engineer.realtime_voice import RealtimeEngineer
from engineer.sdk import metadata, fields, setup_scalars
from engineer.setup import recommendation
from test_controller import Variable, Widget
from test_realtime_voice import Socket, AudioInput
import test_engineer as sdk_tests
from engineer.sdk import decode
from engineer.storage import Store
from engineer.external_reference import csv_reference
from test_references import native_csv, PROFILE, CONTEXT


class CarTests(unittest.TestCase):
    def test_mixed_grid_selects_player_car_not_first_or_camera_car(self):
        text='''WeekendInfo:
 TrackDisplayName: Test circuit
 TrackConfigName:
 TrackID: 123
 TrackLength: 5.0 km
SessionInfo:
 - SessionNum: 0
   SessionType: Practice
DriverInfo:
 DriverSetupName: C:\\setups\\baseline.sto
 Drivers:
 - CarIdx: 0
   CarID: 10
   CarPath: pacecar
   CarScreenName: Pace car
 - CarIdx: 4
   CarID: 20
   CarPath: gt3-fixture
   CarScreenName: GT3 test car
   CarClassShortName: GT3
   CarClassID: 200
 - CarIdx: 9
   CarID: 30
   CarPath: prototype-fixture
   CarScreenName: Prototype test car
   CarClassShortName: GTP
CarSetup:
 Chassis:
  Front:
   ARBSetting: P4
 Notes: |
  Driver note ignored
'''
        m=metadata(text,9,0)
        self.assertEqual((m['car'],m['car_id'],m['car_class']),('Prototype test car','30','GTP'))
        self.assertEqual(m['config'],'')
        self.assertEqual(m['setup_name'],'baseline.sto')
        self.assertEqual(m['car_setup'],{'Chassis.Front.ARBSetting':'P4'})
        self.assertTrue(supported(m))
        missing=metadata(text,7,0)
        self.assertEqual(missing['car_path'],'');self.assertFalse(supported(missing))

    def test_empty_scalars_never_consume_the_next_metadata_line(self):
        self.assertEqual(fields(' TrackConfigName:\n TrackID: 42\n'),{'TrackConfigName':'','TrackID':'42'})

    def test_identity_reports_observed_controls_without_inventing_abs(self):
        identity=car_identity({**META,'car':'Formula test car','car_path':'formula-fixture','car_id':42},dict(PlayerCarIdx=7,dcBrakeBias=55.5,dcABS=None,dcTractionControl=float('nan')))
        self.assertEqual(identity['name'],'Formula test car')
        self.assertEqual(identity['reported_controls'],{'dcBrakeBias':55.5})
        self.assertIsNone(car_identity({},{}))

    def test_new_car_driver_control_channels_are_discovered_automatically(self):
        raw=sdk_tests.SDKTests().fixture();struct.pack_into('<i',raw,24,6)
        position=128+5*144;struct.pack_into('<iii',raw,position,4,24,1)
        name=b'dcFutureCarControl';raw[position+16:position+16+len(name)]=name
        struct.pack_into('<f',raw,2048+24,9.)
        self.assertEqual(decode(raw)[1]['dcFutureCarControl'],9.)
        self.assertNotIn('dcFutureCarControl',decode(raw,names={'Speed'})[1])

    def test_known_car_ids_isolate_references_and_legacy_history(self):
        payload=csv_reference(native_csv(),dict(id='test',lapTime=100),PROFILE,CONTEXT)
        other={**PROFILE,'car_id':202}
        with self.assertRaises(ValueError):Coach().import_reference(payload,other,CONTEXT)
        with tempfile.TemporaryDirectory() as folder:
            store=Store(os.path.join(folder,'history.db'));store.save_external_reference(payload)
            self.assertIsNone(store.reference(other,CONTEXT))
            self.assertIsNotNone(store.reference(PROFILE,CONTEXT))
            legacy=json.dumps(['LIVE',str(PROFILE['track_id']),PROFILE['config'].casefold(),PROFILE['car_path'].casefold(),list(CONTEXT)],sort_keys=True)
            store.db.execute('DELETE FROM saved_references')
            store.db.execute('INSERT INTO saved_references VALUES (?,?)',(legacy,json.dumps(payload)))
            self.assertIsNotNone(store.reference(PROFILE,CONTEXT))
            self.assertIsNone(store.reference(other,CONTEXT));store.close()

    def test_automatic_ai_observation_includes_current_car_context(self):
        sent=threading.Event()
        class EventSocket(Socket):
            def send(self,event):
                super().send(event)
                if json.loads(event)['type']=='response.create':sent.set()
        e=RealtimeEngineer();e.ws=EventSocket();e.connected=True
        e.set_car(car_identity({**META,'car':'Prototype fixture','car_path':'prototype-fixture','car_id':42},frame(160)))
        self.assertTrue(e.coaching('Observed braking time loss.',{'track':'Test circuit'}))
        self.assertTrue(sent.wait(1))
        packet=json.loads(e.ws.sent[0]['item']['content'][0]['text'].split(': ',1)[1])
        self.assertEqual(packet['current_car']['id'],42)
        self.assertEqual(packet['current_car']['name'],'Prototype fixture')
        self.assertEqual(packet['track'],'Test circuit')

    def test_new_car_invalidates_previous_audio_and_next_turn_uses_new_identity(self):
        e=RealtimeEngineer();e.ws=Socket();e.connected=True
        first=car_identity({**META,'car_id':1},frame(160))
        second=car_identity({**META,'car':'Stock test car','car_path':'stock-fixture','car_id':2},frame(160))
        e.set_car(first);e.recording=True;e.input=AudioInput();e.raw=bytearray(b'\0\0'*3000)
        e.finish_recording({'mode':'LIVE'})
        e.handle({'type':'response.output_audio.delta','delta':base64.b64encode(b'old').decode()})
        self.assertFalse(e.output.empty())
        e.set_car(second);self.assertTrue(e.output.empty())
        e.handle({'type':'response.output_audio.delta','delta':base64.b64encode(b'old').decode()})
        e.handle({'type':'response.output_audio_transcript.done','transcript':'wrong car response'})
        self.assertTrue(e.output.empty())
        self.assertFalse(any(kind=='transcript' for kind,value in list(e.events.queue)))
        e.handle({'type':'response.done','response':{'status':'completed'}})
        e.recording=True;e.input=AudioInput();e.raw=bytearray(b'\0\0'*3000)
        e.finish_recording({'mode':'LIVE'})
        packet=json.loads(e.ws.sent[-5]['item']['content'][0]['text'].split(': ',1)[1])
        self.assertEqual(packet['current_car']['id'],2)
        self.assertEqual(packet['current_car']['path'],'stock-fixture')

    def test_universal_setup_never_reuses_gr86_numeric_ranges(self):
        laps=[dict(lap_time=t,tc=9,abs=None) for t in (100.,100.1,100.2)]
        profile={**META,'car':'GT test car','car_path':'new-car-fixture','car_setup':{'Chassis.Front.ARBSetting':'P4'}}
        text=recommendation(laps,'Mid-corner understeer','Open / adjustable','Soft','1',profile)
        self.assertIn('one documented step softer',text);self.assertIn('GT test car',text)
        self.assertNotIn('1 → 2',text)
        text=recommendation(laps,'Exit wheelspin','Open / adjustable','Soft','1',profile)
        self.assertIn('reported traction control setting is 9',text)
        self.assertNotIn('maximum assistance',text);self.assertNotIn('9 → 10',text)
        text=recommendation(laps,'Braking lockup / instability','Open / adjustable','Soft','1',profile)
        self.assertIn('unavailable or unstable',text)

    def test_all_car_categories_can_record_setup_runs_and_switch_identity(self):
        tk=SimpleNamespace(StringVar=Variable,BooleanVar=Variable,Text=Widget,Canvas=Widget,PhotoImage=Widget)
        ttk=SimpleNamespace(**{name:Widget for name in ('Style','Frame','Label','Button','Notebook','Treeview','Scrollbar','Combobox','Entry','Checkbutton')})
        with tempfile.TemporaryDirectory() as folder,headless_services(),patch.object(app,'tk',tk),patch.object(app,'ttk',ttk),patch.dict(os.environ,{'RACE_ENGINEER_DATA':folder}):
            ui=app.App(Widget());ui.start('LIVE')
            for i,category in enumerate(('GT3','Formula','Prototype','Stock','Dirt','Truck','Future car')):
                meta={**META,'car':category+' fixture','car_path':'fixture-'+str(i),'car_id':1000+i,'car_class':category}
                ui.ingest(frame(160+i),meta)
                self.assertEqual(ui.live_voice.current_car['id'],1000+i)
                self.assertIn(category,ui.car_status.get())
                self.assertFalse(ui.coach.reference)
                ui.begin_setup('baseline')
                self.assertEqual(ui.setup_phase,'baseline')
                self.assertEqual(ui.setup_run['profile']['car_path'],meta['car_path'])
                snapshot=ui.telemetry_snapshot()
                self.assertEqual(snapshot['current_car']['name'],meta['car'])
                self.assertEqual(snapshot['layout'],meta['config'])
            spoken=[];ui.speech.say=lambda text,force=False:spoken.append(text)
            ui.ingest(frame(170),{**META,'car':'Another car','car_path':'another-fixture','car_id':5000})
            ui.command('car');self.assertIn('driving Another car',spoken[-1])
            ui.command('setup');self.assertIn('Start a fresh baseline for Another car',spoken[-1])
            ui.last_seen=time.monotonic()-5
            self.assertEqual(ui.telemetry_snapshot()['mode'],'not connected or telemetry stale')
            self.assertIsNone(ui.live_voice.current_car)
            ui.command('car');self.assertIn('Telemetry is stale',spoken[-1])
            ui.close()
