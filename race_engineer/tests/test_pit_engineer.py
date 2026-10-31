from test_controller import headless_services
import unittest,tempfile
from pathlib import Path
from engineer.pit_engineer import PitEngineer,session_kind
from engineer.storage import Store
from engineer.session_review import build_recap
from test_session_review import data
META=dict(car='Test car',track='Test track',config='Full',session_type='Race')
def pit(t,**kw):return data(t,OnPitRoad=True,PlayerTrackSurface=1,Speed=0,**kw)
class PitEngineerTests(unittest.TestCase):
 def test_session_modes_are_explicit(self):
  for raw,expected in [('Practice','practice'),('Lone Qualify','qualifying'),('Race','race'),('','session type unavailable')]:self.assertEqual(session_kind({'session_type':raw}),expected)
 def test_driving_down_pit_lane_does_not_create_stop_recap(self):
  p=PitEngineer()
  for t in range(10):p.update(data(t,OnPitRoad=True,Speed=15,PlayerTrackSurface=2),META)
  self.assertIsNone(p.report);self.assertEqual(p.state,'pit_lane')
 def test_trackside_stop_is_not_pit_stop(self):
  p=PitEngineer()
  for t in range(10):p.update(data(t,Speed=0),META)
  self.assertIsNone(p.report)
 def test_box_confirmation_generates_one_report_per_visit(self):
  p=PitEngineer()
  for n in range(100):p.update(pit(n*.1,PitSvStatus=1),META)
  self.assertEqual(p.report_count,1);self.assertEqual(p.report['session_type'],'race');self.assertEqual(p.state,'box')
  self.assertTrue(p.take(pit(10)));self.assertIsNone(p.take(pit(11)))
 def test_stale_complete_status_is_not_announced_as_new_service(self):
  p=PitEngineer()
  for n in range(30):p.update(pit(n*.1,PitSvStatus=2),META)
  self.assertFalse(any(v['topic']=='complete' for v in p.queue))
 def test_service_completion_requires_observed_service_in_progress(self):
  p=PitEngineer()
  for n in range(20):p.update(pit(n*.1,PitSvStatus=1),META)
  p.update(pit(2,PitSvStatus=2),META)
  self.assertIn('service',p.take(pit(2)).lower());self.assertEqual(p.last_event,'complete')
 def test_missing_pit_channel_does_not_invent_exit(self):
  p=PitEngineer();p.update(pit(0),META);d=data(1);d.pop('OnPitRoad');p.update(d,META)
  self.assertTrue(p.was_pit);self.assertFalse(any(v['topic']=='exit' for v in p.queue))
 def test_moving_away_discards_long_recap(self):
  p=PitEngineer()
  for n in range(20):p.update(pit(n*.1,PitSvStatus=1),META)
  p.update(data(2.1,OnPitRoad=True,PlayerTrackSurface=2,Speed=5),META)
  self.assertEqual(p.state,'pit_lane');self.assertFalse(any(v['topic']=='box' for v in p.queue))
 def test_corrections_precede_recap(self):
  p=PitEngineer()
  for n in range(20):p.update(pit(n*.1,PitSvStatus=100),META)
  self.assertIn('too far left',p.take(pit(2)))
 def test_no_fuel_estimate_without_consumption_measurements(self):
  p=PitEngineer();r=p.build_report(pit(2,FuelLevel=20),META,'Chatty')
  self.assertTrue(any('unavailable' in f and 'Fuel' in f for f in r['facts']));self.assertNotIn('Fuel covers',r['spoken'])
 def test_pit_report_survives_restart_in_session_recap(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'history.db';s=Store(path);sid=s.start('LIVE',META,0);p=PitEngineer();s.save_pit_report(p.build_report(pit(2,FuelLevel=20),META,'Chatty'));s.close()
   self.assertIn('PIT STOP DEBRIEFS',build_recap(path,sid))
 def test_quiet_mode_keeps_important_service_status(self):
  p=PitEngineer()
  for n in range(20):p.update(pit(n*.1,PitSvStatus=1),META,verbosity='Quiet')
  self.assertFalse(p.queue);p.update(pit(2,PitSvStatus=2),META,verbosity='Quiet');self.assertIsNotNone(p.take(pit(2)))

class PitControllerTests(unittest.TestCase):
 def test_stationary_pit_briefing_is_spoken_and_saved_in_race_mode(self):
  import app,os
  from types import SimpleNamespace
  from unittest.mock import patch
  from test_controller import Widget,Variable
  from engineer.demo import META as BASE,frame
  with tempfile.TemporaryDirectory() as folder:
   tk=SimpleNamespace(StringVar=Variable,BooleanVar=Variable,Text=Widget,Canvas=Widget,PhotoImage=Widget)
   ttk=SimpleNamespace(**{n:Widget for n in ('Style','Frame','Label','Button','Notebook','Treeview','Scrollbar','Combobox','Entry','Checkbutton')})
   with headless_services(),patch.object(app,'tk',tk),patch.object(app,'ttk',ttk),patch.dict(os.environ,{'RACE_ENGINEER_DATA':folder}):
    ui=app.App(Widget());ui.start('LIVE');spoken=[];ui.instruct=lambda text,key=None:spoken.append(text) or True
    for n in range(140):
     d=frame(130+n*.05);d.update(OnPitRoad=True,PlayerTrackSurface=1,Speed=0,PitSvStatus=1)
     ui.ingest(d,{**BASE,'session_type':'Race'})
    self.assertTrue(any('This is race' in text for text in spoken));self.assertTrue(ui.car_status.get().startswith('RACE'));self.assertEqual(ui.store.db.execute('SELECT count(*) FROM pit_reports').fetchone()[0],1);ui.close()
