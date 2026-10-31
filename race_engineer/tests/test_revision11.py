import array,json,math,tempfile,unittest,wave
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from engineer.audio import AudioOutput
from engineer.cockpit import Overlay,paint
from engineer.driving import FlowCoach,Encouragement
from engineer.situation import RelativeTraffic,SituationCoach
from engineer.devices import role
from engineer.demo import frame,META
from engineer.cues import DrivingCues
from engineer.core import Coach
from engineer.guides import validate_guide
import test_driving_features as fixtures

class Canvas:
 def __init__(self,w,h):self.w=w;self.h=h;self.text=[];self.ovals=[]
 def configure(self,**kw):pass
 def delete(self,*a):pass
 def winfo_width(self):return self.w
 def winfo_height(self):return self.h
 def create_text(self,*a,**kw):self.text.append(kw.get('text',''))
 def create_oval(self,*a,**kw):self.ovals.append(a)
 def create_line(self,*a,**kw):pass
 def create_rectangle(self,*a,**kw):pass

class Revision11(unittest.TestCase):
 def test_straight_cruise_no_longer_repeats_generic_praise(self):
  flow=FlowCoach();calls=[]
  for i in range(4000):
   d=frame(i*.05);d.update(Brake=0,Throttle=1,SteeringWheelAngle=0,Speed=40)
   call=flow.update(d,True,False)
   if call:calls.append(call)
  self.assertEqual(len(calls),1);self.assertIn('Learning',calls[0])
 def test_pause_and_short_stall_do_not_repeat_greeting(self):
  f=FlowCoach();d={**frame(1),'Speed':40};self.assertIsNotNone(f.update(d,True))
  f.update({**d,'SessionTime':1.1},False)
  self.assertIsNone(f.update({**d,'SessionTime':2},True))
  self.assertIsNone(f.update({**d,'SessionTime':3},True))
 def test_input_feedback_not_praise_is_limited_per_lap_and_pattern(self):
  f=FlowCoach();f.update(frame(1),True)
  d={**frame(20),'Brake':.5,'Throttle':.4,'Speed':40}
  f.update({**d,'SessionTime':19.9,'Throttle':1,'Brake':0},True)
  call=f.update(d,True);self.assertIn('throttle',call)
  for i in range(1,401):self.assertIsNone(f.update({**d,'SessionTime':20+i*.1,'Lap':99 if i>100 else d['Lap']},True))
 def test_praise_is_only_once_for_clean_lap_and_has_long_cooldown(self):
  e=Encouragement();lap=dict(lap=1,lap_time=90,clean=True,context=[False,1,2,2])
  e.completed(lap,92,'LIVE',1);d={**frame(2),'Brake':0,'Throttle':1,'SteeringWheelAngle':0}
  self.assertIsNotNone(e.take(d));self.assertIsNone(e.take(d))
  self.assertIsNone(e.completed({**lap,'lap':2,'lap_time':89},90,'LIVE',60))
  self.assertIsNone(e.completed({**lap,'lap':3,'lap_time':90},90,'LIVE',180))
  self.assertIsNotNone(e.completed({**lap,'lap':4,'lap_time':88},90,'LIVE',200))
 def test_relative_passage_gap_and_trend_wrap_finish_line(self):
  r=RelativeTraffic()
  for i in range(601):
   t=i*.1;p=(.93+t*.008)%1
   # Ahead's offset shrinks: at 60 sec the time gap is 1.25 sec rather than 2.5.
   ahead=(p+.02-t*.0001666667)%1
   d={**frame(t),'SessionTime':t,'PlayerCarIdx':0,'CarIdxLapDistPct':[p,ahead,(p-.012)%1], 'CarIdxTrackSurface':[3,3,3],'CarIdxOnPitRoad':[False]*3}
   r.update(d)
  self.assertIn('ahead',r.latest);self.assertIn('behind',r.latest)
  self.assertAlmostEqual(r.latest['ahead']['gap_s'],1.28,delta=.15)
  self.assertGreater(r.latest['ahead']['gain_s'],.15)
  self.assertAlmostEqual(r.latest['behind']['gap_s'],1.5,delta=.05)
 def test_relative_missing_pits_and_discontinuities_clear_estimates(self):
  r=RelativeTraffic();d={**frame(1),'PlayerCarIdx':0,'CarIdxLapDistPct':[.3,.31],'CarIdxTrackSurface':[3,3],'CarIdxOnPitRoad':[False,False]}
  for i in range(100):r.update({**d,'SessionTime':1+i*.1,'CarIdxLapDistPct':[.3+i*.001,.31+i*.001]})
  self.assertIn('ahead',r.latest)
  self.assertEqual(r.update({**d,'SessionTime':30,'IsReplayPlaying':True}),{})
  self.assertEqual(r.update({**frame(31)}),{})
 def test_session_intro_is_not_repeated_and_never_claims_measured_cold(self):
  s=SituationCoach();d={**frame(1),'Speed':40,'Brake':0,'Throttle':1,'SteeringWheelAngle':0}
  s.update(d,{**META,'session_type':'Practice'});text=s.take(d)
  self.assertIn('Practice session',text);self.assertIn('unavailable',text);self.assertNotIn('are cold',text)
  s.update({**d,'SessionTime':100},META);self.assertIsNone(s.take({**d,'SessionTime':100}))
 def test_compact_overlay_240px_has_g_circle_without_radar(self):
  c=Canvas(240,96);paint(c,dict(fresh=True,instruction='Turn in',speed=60,gear=3,lap_time='1:23.456',g_force=(.5,-1.2)),True)
  self.assertTrue(c.ovals);self.assertIn('LAP 1:23.456',c.text)
  self.assertTrue(any('g' in text for text in c.text));self.assertNotIn('ALONGSIDE',c.text)
 def test_overlay_migration_and_small_sizes_are_saved(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder);(path/'overlay.json').write_text(json.dumps(dict(width=780,height=210,opacity=.7,locked=True)))
   overlay=Overlay(None,path);self.assertEqual(overlay.prefs['width'],360)
   overlay.configure(False,.8,240);self.assertEqual(overlay.prefs['height'],96)
   again=Overlay(None,path);self.assertEqual(again.prefs['width'],240)
 def test_audio_callback_volume_and_onset_uses_one_output_buffer(self):
  output=AudioOutput();output.stream=object();output.volume=.5
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'test.wav'
   with wave.open(str(path),'wb') as f:
    f.setnchannels(1);f.setsampwidth(2);f.setframerate(24000);f.writeframes(array.array('h',[1000,-1000,2000,-2000]).tobytes())
   self.assertTrue(output.play(path));raw=bytearray(12)
   output.callback(raw,6,SimpleNamespace(outputBufferDacTime=1.02,currentTime=1),None)
   self.assertEqual(list(array.array('h',raw)),[500,-500,1000,-1000,0,0]);self.assertIsNotNone(output.last_onset)
   output.stop();raw=bytearray(b'xxxxxxxxxxxx');output.callback(raw,6,SimpleNamespace(outputBufferDacTime=1,currentTime=1),None)
   self.assertEqual(raw,b'\0'*12)
 def guide(self):return validate_guide(dict(format='race-engineer-coach-v1',profile=dict(META),corners=[dict(name='Test',brake=.2,release=.215,turn=.22,throttle=.25,end=.28)]),META)
 def test_cue_is_not_marked_delivered_until_audio_acknowledges(self):
  e=DrivingCues(auto_ack=False);e.enabled=True;e.install_guide(self.guide());c=Coach();event=None
  for i in range(300):
   d={**frame(1+i*.05),'Speed':50,'Brake':0,'SteeringWheelAngle':0,'LapDistPct':.14+i*.0005}
   event=e.update(d,META,c)
   if event:break
  self.assertIsNotNone(event);self.assertNotIn(event,e.pending['state']['done'])
  e.acknowledge(False,'audio busy');self.assertIsNotNone(e.pending)
  e.acknowledge(True);self.assertIsNone(e.pending);self.assertTrue(e.history[-1]['played'])
 def test_cue_suppression_records_traffic_instead_of_false_delivery(self):
  e=DrivingCues(auto_ack=False);e.enabled=True;e.install_guide(self.guide())
  for i in range(200):
   d={**frame(i*.05),'Speed':50,'Brake':0,'SteeringWheelAngle':0,'LapDistPct':.14+i*.0005}
   event=e.update(d,META,Coach())
   if event:break
  e.acknowledge(False,'traffic');self.assertFalse(e.history[-1]['played']);self.assertEqual(e.history[-1]['reason'],'traffic')
 def test_device_role_detection_does_not_invent_separate_pedals(self):
  self.assertEqual(role('ClubSport Pedals V3'),'Pedals')
  self.assertIn('Wheel',role('MOZA R9'))
  self.assertIn('confirm',role('Generic USB controller'))

class NewControllerFeatures(unittest.TestCase):
 make_app=fixtures.IntegrationFeatures.make_app
 def test_tutorial_settings_lap_timer_and_g_units(self):
  with tempfile.TemporaryDirectory() as folder:
   ui=self.make_app(folder);ui.start('LIVE');d={**frame(160),'LapCurrentLapTime':12.345,'LatAccel':9.80665,'LongAccel':-19.6133}
   ui.ingest(d,dict(META));ui.render()
   self.assertEqual(ui.metrics['CURRENT LAP'].get(),'0:12.345')
   self.assertEqual(ui.g_force(),(1.,-2.))
   ui.relatives.latest={'ahead':dict(gap_s=1.8,gain_s=.4,window_s=10)};ui.render()
   self.assertEqual(ui.gap_values['ahead'].get(),'~1.8s');self.assertIn('You gained',ui.gap_trends['ahead'].get())
   ui.relatives.latest['ahead']['gap_s']=153.7;ui.render()
   self.assertEqual(ui.gap_values['ahead'].get(),'~2:33.7')
   ui.show_tutorial();ui.tutorial_move(2);self.assertIn('corner',ui.tutorial_title.get())
   ui.finish_tutorial();self.assertTrue(ui.options['tutorial_completed'])
   ui.theme_choice.set('Light');ui.setting_praise.set(False);ui.apply_settings();ui.close()
   ui=self.make_app(folder);self.assertEqual(ui.options['theme'],'Light');self.assertFalse(ui.options['praise']);self.assertTrue(ui.options['tutorial_completed']);ui.close()
 def test_controller_assignments_and_missing_device_status(self):
  with tempfile.TemporaryDirectory() as folder:
   ui=self.make_app(folder)
   rows=[dict(name='Test wheel',role='Wheel base / combined controller',source='Windows HID'),dict(name='Test pedals',role='Pedals',source='Windows HID')]
   ui.receive_devices(dict(controllers=rows,outputs=['System default']))
   self.assertIn('Test wheel',ui.hardware_status.get());self.assertIn('Test pedals',ui.hardware_status.get())
   ui.wheel_choice.set('Test wheel');ui.save_device_settings();ui.receive_devices(dict(controllers=[],outputs=None))
   self.assertIn('not detected',ui.hardware_status.get());ui.close()

 def test_simultaneous_spotter_success_does_not_falsely_acknowledge_corner_audio(self):
  with tempfile.TemporaryDirectory() as folder:
   ui=self.make_app(folder);ui.start('LIVE');ui.cue_audio.ready=True
   acknowledgements=[];spoken=[]
   ui.cues.update=lambda *a:'brake'
   ui.cues.acknowledge=lambda played,reason:acknowledgements.append((played,reason))
   ui.instruct=lambda text,key=None:spoken.append(key) or True
   ui.ingest({**frame(160),'CarLeftRight':2},dict(META))
   self.assertEqual(spoken,['traffic_left']);self.assertEqual(acknowledgements,[(False,'traffic')]);ui.close()

class StraightBriefingTests(unittest.TestCase):
 def test_full_straight_briefing_includes_distance_type_and_both_gaps(self):
  from engineer.straight import StraightBriefing
  engine=StraightBriefing();d={**frame(30),'Speed':30,'LapDistPct':.05,'Brake':0,'Throttle':1,'SteeringWheelAngle':0}
  plans=[dict(name='Hairpin',brake=.2,turn=.21,end=.3,direction='right',kind='hairpin')]
  engine.update(d,META,plans,[])
  # 750 m at 30 m/s leaves a long, safe reporting window.
  text=engine.voice(d,dict(ahead=dict(gap_s=1.8),behind=dict(gap_s=2.7)))
  self.assertIn('750 meters',text);self.assertIn('Right hairpin',text)
  self.assertIn('Car ahead',text);self.assertIn('Car behind',text)
  self.assertIsNone(engine.voice({**d,'SessionTime':31},{}))
 def test_briefing_yields_to_countdown_and_has_no_fabricated_turn(self):
  from engineer.straight import StraightBriefing
  engine=StraightBriefing();d={**frame(30),'Speed':50,'LapDistPct':.18,'Brake':0,'Throttle':1,'SteeringWheelAngle':0}
  engine.update(d,META,[dict(name='Turn',brake=.2,end=.3)],[])
  self.assertIsNone(engine.voice(d,{}));self.assertEqual(engine.snapshot['description'],'turn details not learned')
  self.assertEqual(engine.snapshot['distance_m'],100)
 def test_missing_markers_show_learning_and_never_announce_distance(self):
  from engineer.straight import StraightBriefing
  engine=StraightBriefing();d=frame(30);engine.update(d,META,[],[])
  self.assertIsNone(engine.voice(d,{}));self.assertIn('learn',engine.hud({}))
 def test_reference_gps_geometry_identifies_a_right_turn(self):
  from engineer.straight import corner_details
  from engineer.core import Sample
  # A clockwise quarter-circle in local coordinates: northbound, then eastbound.
  samples=[]
  for i in range(101):
   theta=math.pi-i*math.pi/200;x=100*math.cos(theta);y=100*math.sin(theta)
   samples.append(Sample(i*.1,.2+i*.001,25,0,1,0,30+y/111320,-80+x/(111320*math.cos(math.radians(30)))))
  details=corner_details(dict(turn=.2,end=.3),samples,5000)
  self.assertIn('right',details['description']);self.assertEqual(details['minimum_mph'],56)
