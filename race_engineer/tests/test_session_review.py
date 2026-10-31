import unittest,tempfile,threading
from pathlib import Path
from engineer.session_review import TireMonitor,InputStyleMonitor,build_recap,explain
from engineer.storage import Store
from engineer.core import Sample

def data(t=0,**kw):
 d=dict(SessionTime=t,IsOnTrack=True,OnPitRoad=False,IsReplayPlaying=False,PlayerTrackSurface=3,SessionFlags=0,Speed=30,SteeringWheelAngle=0,Brake=0,Throttle=1,Lap=1,LapDistPct=.1)
 d.update(kw);return d
class ReviewTests(unittest.TestCase):
 def test_tires_are_pit_reports_and_voice_once(self):
  m=TireMonitor();m.update(data(1,OnPitRoad=True,LFtempCL=91,LFwearL=.81))
  text=m.voice(data(20));self.assertIn('81 percent',text);self.assertIn('not live',text)
  self.assertIsNone(m.voice(data(21)))
 def test_ontrack_temperature_not_live_alert(self):
  m=TireMonitor();m.update(data(1,LFtempCL=140,LFwearL=.7));self.assertIsNone(m.voice(data(2)))
 def test_missing_tires_no_invented_condition(self):
  m=TireMonitor();m.update(data(1));self.assertEqual(m.current,[]);self.assertIsNone(m.voice(data(2)))
 def test_input_events_are_observations(self):
  m=InputStyleMonitor()
  for n in range(601):
   # Repeated sharp releases, separated by several seconds.
   brake=.8 if n%60<30 else 0
   m.update(data(n*.05,Brake=brake,SteeringWheelAngle=.3))
  self.assertGreater(m.counts['abrupt_brake_release'],0)
  self.assertIn('not proof',m.summary())
 def test_pit_inputs_not_counted(self):
  m=InputStyleMonitor();m.update(data(0,OnPitRoad=True,Brake=.9,SteeringWheelAngle=.3));m.update(data(.05,OnPitRoad=True,Brake=0,SteeringWheelAngle=.3))
  self.assertEqual(sum(m.counts.values()),0)
 def test_saved_session_recap_reopens_and_explains(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'history.sqlite3';s=Store(path);sid=s.start('LIVE',dict(car='Test car',track='Test track',config='Test layout'),0)
   for n in range(100):s.record(data(n*.05,LFwearL=.85))
   review=dict(name='Turn 1',loss=.4,evidence='Measured section loss 0.4s',tip='Try braking 10 meters later.',action_metric='braking distance',brake_m=-10)
   s.lap(dict(lap=1,lap_time=100,clean=True,reasons=[],samples=[Sample(0,0,30,0,1,0),Sample(100,1,30,0,1,0)],reviews=[review],context=[]));s.close()
   report=build_recap(path,sid)
   for phrase in ('Test car','INPUT STYLE','TIRES','Why:','10 meters later','85%'):self.assertIn(phrase,report)
 def test_cancel_does_not_create_database(self):
  event=threading.Event();event.set()
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'missing.sqlite';self.assertEqual(build_recap(p,1,event),'Analysis canceled.');self.assertFalse(p.exists())
 def test_explanation_does_not_claim_measured_understeer(self):
  self.assertIn('does not prove understeer',explain(dict(steering_delta_deg=15)))
