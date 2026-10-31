from test_controller import headless_services
"""Actual coaching pipeline: streamed samples -> reference -> measured loss -> speech."""
from types import SimpleNamespace
from unittest.mock import patch
import os,tempfile,unittest
import app
from engineer.demo import frame,META
from test_controller import Variable,Widget

class SpeechSink:
    connected=True
    def __init__(self):self.calls=[]
    def prioritize_driving(self,active):self.suspended=bool(active)
    def set_car(self,identity):self.current_car=identity
    def coaching(self,text,telemetry=None):self.calls.append(text);self.snapshot=telemetry;return True
    def close(self):pass

class LiveTelemetryCoachingTests(unittest.TestCase):
    def exercise_car(self,meta):
        with tempfile.TemporaryDirectory() as tmp:
            tk=SimpleNamespace(StringVar=Variable,BooleanVar=Variable,Text=Widget,Canvas=Widget,PhotoImage=Widget)
            ttk=SimpleNamespace(**{name:Widget for name in ('Style','Frame','Label','Button','Notebook','Treeview','Scrollbar','Combobox','Entry','Checkbutton')})
            with headless_services(),patch.object(app,'tk',tk),patch.object(app,'ttk',ttk),patch.dict(os.environ,{'RACE_ENGINEER_DATA':tmp}):
                ui=app.App(Widget());ui.start('LIVE');sink=SpeechSink();ui.live_voice=sink
                spoken_before=0
                for tick in range(2580,7805):
                    original_time=tick/20
                    d=frame(original_time)
                    if original_time>=260:
                        d['SessionTime']=original_time+(original_time-260)*.05
                        d['Speed']/=1.05
                    ui.ingest(d,dict(meta))
                    if original_time<260:self.assertFalse(sink.calls)
                self.assertTrue(ui.coach.reference)
                self.assertTrue(sink.calls,'No automatic voice call from measured telemetry loss')
                self.assertTrue(any('reference' in s.lower() and 'braking zone' in s.lower() for s in sink.calls))
                self.assertTrue(any(r['loss']>.15 for r in ui.last_lap['reviews']))
                self.assertEqual(sink.snapshot['current_car']['name'],meta['car'])
                self.assertEqual(sink.snapshot['current_car']['path'],meta['car_path'])
                self.assertEqual(sink.snapshot['layout'],meta['config'])
                ui.close()

    def test_driving_time_loss_automatically_reaches_voice_for_all_car_categories(self):
        for i,category in enumerate(('GR86','GT3','Formula','Prototype','Stock','Dirt','Truck')):
            with self.subTest(category=category):
                self.exercise_car({**META,'car':category+' test car','car_path':'test-fixture-'+str(i),'car_id':1000+i,'car_class':category})

if __name__=='__main__':unittest.main()
