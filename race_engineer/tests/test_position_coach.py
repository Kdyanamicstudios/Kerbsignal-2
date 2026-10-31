from test_controller import headless_services
import json
from pathlib import Path
import struct
import tempfile
import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from engineer.position import PositionTracker,SignalTrace,MPH
from engineer.guides import validate_guide
from engineer.core import Coach,context
from engineer.cues import DrivingCues
from engineer.sdk import metadata,decode
from engineer.realtime_voice import RealtimeEngineer
from engineer.cars import car_identity
from engineer.demo import META,frame
import test_engineer as fixtures
import app
from test_controller import Variable,Widget


def guide(meta=META):
    return dict(format='race-engineer-coach-v1',profile=dict(meta),source='Aligned test landmarks',corners=[
        dict(name='Hairpin',brake=.2,hold=.205,release=.22,turn=.225,unwind=.24,throttle=.25,end=.28)])


class PositionCoachTests(unittest.TestCase):
    def test_position_guide_calls_without_any_reference_or_lap_time(self):
        engine=DrivingCues();engine.enabled=True;engine.install_guide(validate_guide(guide(),META))
        coach=Coach();events=[]
        for i in range(1100):
            p=.14+i*50/60/META['length']
            if p>.28:break
            d=frame(i/60);d.update(SessionTime=10000+i/60,LapDistPct=p,Lap=10,Speed=50,Brake=.6 if .201<p<.225 else 0,
                Throttle=0 if p<.26 else 1,SteeringWheelAngle=0 if p<.226 else .1)
            event=engine.update(d,META,coach)
            if event:events.append(event)
        self.assertEqual([x for x in events if x in ('three','two','one','brake')],['three','two','one','brake'])
        self.assertIn('release',events);self.assertIn('turn',events);self.assertIn('throttle',events)
        self.assertFalse(coach.reference)

    def test_elapsed_lap_clock_does_not_change_spatial_brake_marker(self):
        results=[]
        for offset in (0,9000):
            e=DrivingCues();e.enabled=True;e.install_guide(validate_guide(guide(),META));calls=[]
            for i in range(400):
                p=.14+i*50/60/META['length'];d=frame(i/60)
                d.update(SessionTime=offset+i/60,LapDistPct=p,Speed=50,Brake=0,SteeringWheelAngle=0)
                if e.update(d,META,Coach())=='brake':calls.append(p)
            results.append(calls)
        self.assertTrue(results[0]);self.assertEqual(results[0],results[1])

    def test_current_corner_is_not_overwritten_by_a_farther_upcoming_corner(self):
        payload=guide();payload['corners'].append(dict(name='Next bend',brake=.3,end=.38))
        e=DrivingCues();e.enabled=True;e.install_guide(validate_guide(payload,META))
        d=frame(10);d.update(LapDistPct=.24,Speed=50,Brake=0,Throttle=1,SteeringWheelAngle=0)
        e.update(d,META,Coach())
        self.assertEqual(e.diagnostic['corner'],'Hairpin')
        self.assertEqual(e.diagnostic['phase'],'unwind')

    def test_guide_rejects_wrong_layout_car_and_invalid_markers(self):
        for changes in ({'track_id':'other'},{'car_path':'other'},{'config':'other'}):
            with self.assertRaises(ValueError):validate_guide(guide(),{**META,**changes})
        invalid=guide();invalid['corners'][0]['turn']=float('nan')
        with self.assertRaises(ValueError):validate_guide(invalid,META)

    def test_gps_missing_and_frozen_use_explicit_lap_position_source(self):
        with tempfile.TemporaryDirectory() as folder:
            p=PositionTracker(folder);d=frame(10);d.update(Lat=0.,Lon=0.,LapDistPct=.4)
            p.update(d,META,now=1)
            snapshot=p.snapshot(now=1.01)
            self.assertEqual(snapshot['distance_m'],META['length']*.4)
            self.assertEqual(snapshot['source'],'SDK lap distance');self.assertFalse(snapshot['gps_live'])
            d.update(Lat=29.,Lon=-81.);p.update(d,META,now=2)
            self.assertTrue(p.snapshot(now=2)['gps_live'])
            p.update(d,META,now=3)
            self.assertFalse(p.snapshot(now=3)['gps_live'])
            self.assertFalse(p.snapshot(now=4)['valid'])

    def test_gps_maps_are_isolated_by_track_and_survive_car_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            p=PositionTracker(folder)
            for i in range(900):
                d=frame(i*.1);d.update(LapDistPct=i/1000,Lat=29+i*.000001,Lon=-81+i*.000001)
                p.update(d,META,now=i*.1)
            self.assertTrue(list(Path(folder).glob('*.json')))
            route=len(p.route);p.select({**META,'car_path':'other-car'})
            self.assertEqual(len(p.route),route)
            p.select({**META,'track_id':'other-layout'})
            self.assertFalse(p.route)

    def test_mph_graph_conversion_and_track_change_reply_invalidation(self):
        signals=SignalTrace();d=frame(10);d.update(Speed=44.704)
        signals.append(d);self.assertAlmostEqual(signals.window()[-1][1],100,places=2)
        ai=RealtimeEngineer();ai.set_car(car_identity(META,d));generation=ai.car_generation
        ai.set_car(car_identity({**META,'track_id':'another-layout'},d))
        self.assertGreater(ai.car_generation,generation)

    def test_sdk_yaml_handles_missing_configuration_and_nested_duplicate_fields(self):
        text='''---
WeekendInfo:
  TrackName: spa
  TrackDisplayName: "Spa: Test Layout"
  TrackID: 1234
  TrackLength: 7.004 km
SessionInfo:
  Sessions:
    - SessionNum: 2
      SessionType: Practice
DriverInfo:
  Drivers:
    - CarIdx: 8
      CarID: 44
      CarPath: test-car
      CarScreenName: Test car
CarSetup:
  Other:
    TrackID: wrong
'''
        meta=metadata(text,8,2)
        self.assertEqual(meta['track_id'],'1234');self.assertEqual(meta['config'],'')
        self.assertEqual(meta['track'],'Spa: Test Layout');self.assertEqual(meta['length'],7004.)
        self.assertEqual(meta['session_type'],'Practice')

    def test_sdk_metadata_is_cached_between_ticks_and_refreshed_on_update(self):
        raw=fixtures.SDKTests().fixture();cache={}
        with patch('engineer.sdk.metadata',wraps=metadata) as parse:
            decode(raw,cache=cache);decode(raw,cache=cache)
            self.assertEqual(parse.call_count,1)
            struct.pack_into('<i',raw,12,2);decode(raw,cache=cache)
            self.assertEqual(parse.call_count,2)

    def test_conversation_audio_is_ducked_for_corner_calls(self):
        e=RealtimeEngineer();e.pending=True;e.prioritize_driving(True)
        self.assertTrue(e.suspended);self.assertTrue(e.discard_response)
        self.assertFalse(e.coaching('late long message'))
        e.handle({'type':'response.done','response':{'status':'completed'}})
        self.assertFalse(e.discard_response)
        e.prioritize_driving(False);self.assertFalse(e.suspended)

    def test_dashboard_mph_and_position_guide_persist_without_lap_time(self):
        tk=SimpleNamespace(StringVar=Variable,BooleanVar=Variable,Text=Widget,Canvas=Widget,PhotoImage=Widget)
        ttk=SimpleNamespace(**{n:Widget for n in ('Style','Frame','Label','Button','Notebook','Treeview','Scrollbar','Combobox','Entry','Checkbutton')})
        with tempfile.TemporaryDirectory() as folder,headless_services(),patch.object(app,'tk',tk),patch.object(app,'ttk',ttk),patch.dict(os.environ,{'RACE_ENGINEER_DATA':folder}):
            ui=app.App(Widget());ui.start('LIVE');d=frame(160);d['Speed']=44.704
            ui.ingest(d,dict(META));ui.render()
            self.assertEqual(ui.metrics['SPEED mph'].get(),'100')
            spoken=[];ui.speech.say=lambda text,force=False:spoken.append(text)
            ui.command('track');self.assertIn(META['track'],spoken[-1])
            ui.command('position');self.assertIn('23.1 percent',spoken[-1])
            for key,value in dict(name='Test bend',brake='1000',release='1100',turn='1125',throttle='1250',end='1400').items():ui.guide_fields[key].set(value)
            ui.guide_match.set(True);ui.save_corner()
            self.assertEqual(ui.cues.guide['corners'][0]['brake'],.2)
            self.assertNotIn('lap_time',ui.cues.guide)
            ui.close();ui=app.App(Widget());ui.start('LIVE');ui.ingest(d,dict(META))
            self.assertIsNotNone(ui.cues.guide)
            self.assertEqual(ui.telemetry_snapshot()['position']['track_id'],META['track_id'])
            ui.stop();self.assertFalse(ui.signals.points)
            self.assertIn('WAITING',ui.track_display.get());ui.close()

    def test_diagnostic_export_captures_position_but_not_api_key(self):
        tk=SimpleNamespace(StringVar=Variable,BooleanVar=Variable,Text=Widget,Canvas=Widget,PhotoImage=Widget)
        ttk=SimpleNamespace(**{n:Widget for n in ('Style','Frame','Label','Button','Notebook','Treeview','Scrollbar','Combobox','Entry','Checkbutton')})
        with tempfile.TemporaryDirectory() as folder,headless_services(),patch.object(app,'tk',tk),patch.object(app,'ttk',ttk),patch.dict(os.environ,{'RACE_ENGINEER_DATA':folder}):
            ui=app.App(Widget());ui.start('LIVE');ui.ingest(frame(160),dict(META))
            self.assertFalse(hasattr(ui,'api_key'))
            path=Path(folder)/'diagnostics.json'
            with patch.object(app.filedialog,'asksaveasfilename',return_value=str(path)):ui.export_diagnostics()
            text=path.read_text();payload=json.loads(text)
            self.assertNotIn('secret-not-for-export',text)
            self.assertEqual(payload['position']['track_id'],META['track_id'])
            self.assertEqual(payload['version'],app.updater.VERSION);ui.close()

    def test_sdk_wait_does_not_block_voice_commands_or_dashboard_refresh(self):
        tk=SimpleNamespace(StringVar=Variable,BooleanVar=Variable,Text=Widget,Canvas=Widget,PhotoImage=Widget)
        ttk=SimpleNamespace(**{n:Widget for n in ('Style','Frame','Label','Button','Notebook','Treeview','Scrollbar','Combobox','Entry','Checkbutton')})
        with tempfile.TemporaryDirectory() as folder,headless_services(),patch.object(app,'tk',tk),patch.object(app,'ttk',ttk),patch.dict(os.environ,{'RACE_ENGINEER_DATA':folder}):
            ui=app.App(Widget());ui.start('LIVE');opened=[]
            ui.youtube.opener=lambda url,**kwargs:opened.append(url) or True
            ui.speech.events.put(('command','focus_music'))
            with patch.object(ui.reader,'read',side_effect=OSError('Waiting for simulator')):ui.tick()
            self.assertTrue(opened);self.assertGreater(ui.last_draw,0)
            self.assertEqual(ui.mode,'LIVE');ui.close()

    def test_demo_countdown_keeps_real_time_when_live_polling_is_faster(self):
        class Root(Widget):
            def after(self,delay,callback):self.last_delay=delay
        tk=SimpleNamespace(StringVar=Variable,BooleanVar=Variable,Text=Widget,Canvas=Widget,PhotoImage=Widget)
        ttk=SimpleNamespace(**{n:Widget for n in ('Style','Frame','Label','Button','Notebook','Treeview','Scrollbar','Combobox','Entry','Checkbutton')})
        with tempfile.TemporaryDirectory() as folder,headless_services(),patch.object(app,'tk',tk),patch.object(app,'ttk',ttk),patch.dict(os.environ,{'RACE_ENGINEER_DATA':folder}):
            root=Root();ui=app.App(root);ui.start('DEMO');ui.cues.enabled=True
            before=ui.demo_t;ui.tick()
            self.assertAlmostEqual(ui.demo_t-before,.05)
            self.assertEqual(root.last_delay,50)
            ui.close()
