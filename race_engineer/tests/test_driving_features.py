from test_controller import headless_services
import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from engineer.spotter import Spotter
from engineer.driving import FlowCoach,Encouragement
from engineer.demo import frame,META
from engineer import updater
from engineer.storage import Store
from engineer.core import context

class DrivingFeatures(unittest.TestCase):
 def packet(self,t,state=1,**kw):return {**frame(t),'CarLeftRight':state,**kw}
 def test_spotter_occupancy_and_debounced_clear(self):
  s=Spotter();self.assertIsNone(s.update(self.packet(1)))
  self.assertEqual(s.update(self.packet(1.1,2)),'left')
  self.assertEqual(s.left,1)
  for t in (1.2,1.4,1.6):self.assertIsNone(s.update(self.packet(t)))
  self.assertEqual(s.left,1)
  self.assertEqual(s.update(self.packet(1.81)),'clear_left');self.assertEqual(s.left,0)
 def test_no_false_clear_on_missing_off_replay_or_stale(self):
  for changes in ({'CarLeftRight':None},{'CarLeftRight':0},{'IsReplayPlaying':True},{'TelemetryAgeSeconds':1},{'OnPitRoad':True}):
   s=Spotter();s.update(self.packet(1,3));self.assertIsNone(s.update(self.packet(1.1,1,**changes)))
   self.assertFalse(s.available)
   self.assertIsNone(s.update(self.packet(1.2)))
 def test_both_sides_two_cars_and_repeat(self):
  s=Spotter();self.assertEqual(s.update(self.packet(1,4)),'both');self.assertEqual((s.left,s.right),(1,1))
  self.assertEqual(s.update(self.packet(1.1,5)),'two_left')
  events=[]
  for i in range(1,60):
   e=s.update(self.packet(1.1+i*.1,5))
   if e:events.append(e)
  self.assertEqual(events,['still'])
 def test_clear_flicker_does_not_reannounce_same_occupancy(self):
  s=Spotter();s.update(self.packet(1,2));s.update(self.packet(1.1))
  self.assertIsNone(s.update(self.packet(1.2,2)))
  self.assertEqual(s.left,1)
 def test_gap_and_clock_rewind_do_not_emit_false_clear(self):
  for t in (.5,3):
   s=Spotter();s.update(self.packet(1,2));self.assertIsNone(s.update(self.packet(t)));self.assertFalse(s.left)
 def test_flow_auto_start_pause_and_reconnect(self):
  f=FlowCoach();self.assertIsNone(f.update(self.packet(1,Speed=0),True))
  self.assertIn('Learning',f.update(self.packet(1.1),True));self.assertIsNone(f.update(self.packet(1.2),True))
  self.assertIsNone(f.update(self.packet(1.3),False))
  self.assertIsNone(f.update(self.packet(1.4),True,True))
  self.assertIsNone(f.update(self.packet(1.5,IsReplayPlaying=True),True))
 def test_praise_clean_baseline_best_and_invalid(self):
  p=Encouragement();lap=dict(lap=1,lap_time=90,clean=True,context=[False,1,2,2])
  self.assertIn('baseline',p.completed(lap,None,'LIVE',1))
  self.assertIsNone(p.completed(lap,None,'LIVE',1))
  self.assertIsNone(p.completed({**lap,'lap':2,'clean':False},95,'LIVE',2))
  self.assertIsNone(p.completed({**lap,'lap':2},95,'DEMO',2))
  self.assertIn('2.00',p.completed({**lap,'lap':2,'lap_time':88},90,'LIVE',2))
 def test_praise_waits_for_straight_and_expires(self):
  p=Encouragement();lap=dict(lap=1,lap_time=90,clean=True)
  p.completed(lap,None,'LIVE',1)
  self.assertIsNone(p.take(self.packet(2,SteeringWheelAngle=.2)))
  self.assertIsNone(p.take(self.packet(2),quiet=True))
  self.assertIsNotNone(p.take(self.packet(2,SteeringWheelAngle=0,Brake=0,Throttle=1)))
  self.assertIsNone(p.take(self.packet(3)))
  p.completed({**lap,'lap':2},None,'LIVE',4);self.assertIsNone(p.take(self.packet(41)))
 def test_personal_best_excludes_external_driver_and_other_profiles(self):
  with tempfile.TemporaryDirectory() as folder:
   store=Store(Path(folder)/'history.db');d=frame(1);ctx=context(d)
   store.start('LIVE',META,0)
   def add(t):store.lap(dict(lap=1,lap_time=t,clean=True,reasons=[],samples=[],reviews=[],context=ctx))
   add(90);self.assertEqual(store.personal_best(META,ctx),90)
   store.start('DEMO',META,0);add(70)
   store.start('LIVE',{**META,'track_id':'different'},0);add(65)
   self.assertEqual(store.personal_best(META,ctx),90)
   self.assertIsNone(store.personal_best(META,[True,1,2,2]));store.close()
 def manifest(self):return dict(product='RaceEngineer',platform='windows-x64',version='0.11.0',url='https://release.example/app.exe',size=1026,sha256='a'*64)
 def test_updater_validates_origin_version_hash_and_size(self):
  url='https://release.example/release.json';m=self.manifest();updater.validate_manifest(m,url)
  for change in ({'url':'http://release.example/app.exe'},{'url':'https://other.example/app.exe'},{'sha256':'bad'},{'size':100},{'version':'anything'},{'product':'Other'}):
   with self.assertRaises(ValueError):updater.validate_manifest({**m,**change},url)
  self.assertIsNone(updater.check(''))
 def test_update_rejects_modified_download_keeps_existing_install(self):
  import io
  class Response(io.BytesIO):
   def __enter__(self):return self
   def __exit__(self,*args):self.close()
  data=b'MZ'+b'a'*1024;m=self.manifest();m['sha256']=hashlib.sha256(data).hexdigest()
  with tempfile.TemporaryDirectory() as folder,patch('engineer.updater.opener') as op:
   op.return_value.open.return_value=Response(b'MZ'+b'b'*1024)
   with self.assertRaises(ValueError):updater.download(m,folder,'https://release.example/release.json')
   self.assertFalse(list(Path(folder).glob('*.exe')));self.assertFalse(list(Path(folder).glob('*.part')))
   op.return_value.open.return_value=Response(data)
   p=updater.download(m,folder,'https://release.example/release.json');self.assertEqual(p.read_bytes(),data)

class IntegrationFeatures(unittest.TestCase):
 def make_app(self,folder):
  import app,os
  from types import SimpleNamespace
  from test_controller import Widget,Variable
  tk=SimpleNamespace(StringVar=Variable,BooleanVar=Variable,Text=Widget,Canvas=Widget,PhotoImage=Widget)
  ttk=SimpleNamespace(**{name:Widget for name in ('Style','Frame','Label','Button','Notebook','Treeview','Scrollbar','Combobox','Entry','Checkbutton')})
  self.enterContext(headless_services());self.enterContext(patch.object(app,'tk',tk));self.enterContext(patch.object(app,'ttk',ttk));self.enterContext(patch.dict(os.environ,{'RACE_ENGINEER_DATA':folder}))
  return app.App(Widget())
 def test_auto_coach_preference_survives_restart_and_voice_change(self):
  with tempfile.TemporaryDirectory() as folder:
   ui=self.make_app(folder);self.assertTrue(ui.cues.enabled)
   ui.set_cues(False);ui.close()
   ui=self.make_app(folder);self.assertFalse(ui.cues.enabled)
   ui.save_free_voice();self.assertFalse(ui.cues.enabled)
   ui.set_cues(True);ui.start('LIVE');ui.stop();self.assertTrue(ui.cues.enabled);ui.close()
 def test_traffic_preempts_coach_and_stale_hud_hides_occupancy(self):
  import time
  with tempfile.TemporaryDirectory() as folder:
   ui=self.make_app(folder);ui.start('LIVE');calls=[]
   ui.instruct=lambda text,key=None:calls.append((text,key))
   ui.ingest({**frame(160),'CarLeftRight':2},dict(META))
   self.assertEqual(calls[-1][1],'traffic_left')
   self.assertTrue(ui.speech.quiet);self.assertEqual(ui.cockpit_model()['traffic']['left'],1)
   ui.last_seen=time.monotonic()-2;self.assertFalse(ui.cockpit_model()['fresh']);ui.close()
 def test_low_speed_turn_guide_is_not_suppressed(self):
  from engineer.cues import DrivingCues
  from engineer.core import Coach
  from engineer.guides import validate_guide
  guide=dict(format='race-engineer-coach-v1',profile=dict(META),corners=[dict(name='Slow turn',turn=.2,end=.25)])
  engine=DrivingCues();engine.enabled=True;engine.install_guide(validate_guide(guide,META));events=[]
  for i in range(500):
   d=frame(20+i*.05);d.update(Speed=5,LapDistPct=.197+i*.00005,Brake=0,SteeringWheelAngle=0)
   call=engine.update(d,META,Coach())
   if call:events.append(call)
  self.assertIn('turn',events)
