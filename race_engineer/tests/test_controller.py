"""Headless controller smoke check; does not replace Windows visual/live testing."""
import os
import tempfile
from types import SimpleNamespace
import unittest
from contextlib import contextmanager
from unittest.mock import patch

import app
from engineer.demo import META, frame


class Variable:
    def __init__(self, value=None, **kwargs):self.value=value
    def get(self):return self.value
    def set(self,value):self.value=value


class Widget:
    def __init__(self,*args,**kwargs):self.items={};self.selection_value=();self.count=0
    def __getattr__(self,name):return lambda *args,**kwargs:None
    def winfo_width(self):return 1000
    def winfo_height(self):return 460
    def get_children(self):return tuple(self.items)
    def delete(self,*ids):
        for item in ids:self.items.pop(item,None)
    def insert(self,*args,**kwargs):
        self.count+=1;item=kwargs.get('iid',str(self.count));self.items[item]=kwargs;return item
    def selection(self):return self.selection_value
    def selection_set(self,item):self.selection_value=(item,)


@contextmanager
def headless_services():
    """Keep controller tests independent of native windows and audio hardware."""
    with patch.object(app,'StartupAnimation'),patch.object(app,'Overlay',return_value=None), \
         patch.object(app.Speech,'refresh_voices'),patch.object(app.Speech,'say'), \
         patch.object(app.App,'scan_devices'),patch.object(app.CueAudio,'prepare'), \
         patch.object(app.AudioOutput,'prepare'):
        yield


class ControllerTests(unittest.TestCase):
    def test_demo_history_line_and_voice_requests(self):
        with tempfile.TemporaryDirectory() as folder:
            tk=SimpleNamespace(StringVar=Variable,BooleanVar=Variable,Text=Widget,Canvas=Widget,PhotoImage=Widget)
            ttk=SimpleNamespace(**{name:Widget for name in ('Style','Frame','Label','Button','Notebook','Treeview','Scrollbar','Combobox','Entry','Checkbutton')})
            with headless_services(),patch.object(app,'tk',tk),patch.object(app,'ttk',ttk),patch.dict(os.environ,{'RACE_ENGINEER_DATA':folder}):
                ui=app.App(Widget())
                opened=[]
                ui.youtube.opener=lambda url,**kwargs:opened.append(url) or True
                ui.command('focus_music')
                self.assertEqual(len(opened),1)  # Music works before telemetry connects.
                ui.youtube_url.set('https://www.youtube.com/playlist?list=test_playlist')
                ui.save_youtube();ui.command('focus_music')
                self.assertIn('list=test_playlist',opened[-1])
                ui.start('DEMO')
                for tick in range(2580,7820):ui.ingest(frame(tick/20),dict(META))
                self.assertEqual(len(ui.store.history()),2)
                self.assertTrue(ui.coach.reference)
                ui.render()
                lid=str(ui.store.history()[0][0]);ui.laps.selection_set(lid)
                ui.select_lap();ui.show_selected_line();ui.selected_as_reference()
                self.assertTrue(ui.selected_samples)
                spoken=[];ui.speech.say=lambda text,force=False:spoken.append(text)
                for command in ('last_lap','tires','weather','abs','tc','review','line','status'):
                    ui.command(command)
                self.assertEqual(len(spoken),8)
                self.assertIn('Last recorded lap',spoken[0])
                ui.garage.set('Open / adjustable');ui.arb_size.set('Soft');ui.arb_setting.set('1')
                ui.begin_setup('baseline')
                for n in range(4):ui.tag_setup_lap(ui.last_lap,int(lid),ui.data)
                self.assertEqual(len(ui.setup_run['baseline']),3)
                self.assertIsNone(ui.setup_phase)
                self.assertIn('this same car',ui.setup_report.get())
                ui.change_note.set('Front ARB Setting 1 to 2')
                ui.begin_setup('test')
                for n in range(4):ui.tag_setup_lap(ui.last_lap,int(lid),ui.data)
                self.assertEqual(len(ui.setup_run['test']),3)
                self.assertIn('Comparison pending',ui.setup_report.get())
                ui.controlled.set(True);ui.update_setup_report()
                self.assertIn('Inconclusive',ui.setup_report.get())
                self.assertEqual(len(ui.store.latest_test()['baseline']),3)
                ui.stop()
                self.assertIsNone(ui.store.session)
                self.assertEqual(len(ui.store.sessions()),1)
                ui.close()


if __name__=='__main__':unittest.main()

class FakeLive:
    def __init__(self):
        self.connected=False;self.connecting=False;self.recording=False;self.muted=False
        self.events=__import__('queue').Queue();self.received=None
    def connect(self,key,voice,accent,style):
        self.received=(key,voice,accent,style);self.connected=True
    def close(self):self.connected=False;self.recording=False
    def start_recording(self):self.recording=True
    def finish_recording(self,snapshot):self.snapshot=snapshot;self.recording=False;return True
    def prioritize_driving(self,active):self.suspended=bool(active)
    def set_car(self,identity):self.current_car=identity
    def coaching(self,text,telemetry=None):return True

class LiveControllerTests(unittest.TestCase):
    def test_local_chat_never_uses_a_cloud_key_and_prioritizes_driving(self):
        with tempfile.TemporaryDirectory() as folder:
            tk=SimpleNamespace(StringVar=Variable,BooleanVar=Variable,Text=Widget,Canvas=Widget,PhotoImage=Widget)
            ttk=SimpleNamespace(**{name:Widget for name in ('Style','Frame','Label','Button','Notebook','Treeview','Scrollbar','Combobox','Entry','Checkbutton')})
            with headless_services(),patch.object(app,'tk',tk),patch.object(app,'ttk',ttk),patch.dict(os.environ,{'RACE_ENGINEER_DATA':folder,'OPENAI_API_KEY':'example_secret'}):
                ui=app.App(Widget())
                self.assertFalse(hasattr(ui,'api_key'))
                spoken=[];ui.speech.say=lambda text,force=False:spoken.append(text)
                ui.ask_engineer('explain trail braking');ui.speech.quiet=True;ui.pump_driver_reply()
                self.assertEqual(len(ui.reply_queue),1);self.assertEqual(spoken,[])
                ui.speech.quiet=False;ui.pump_driver_reply()
                self.assertEqual(len(ui.reply_queue),0);self.assertIn('release',spoken[0])
                ui.ask_engineer('how do I practice that');ui.pump_driver_reply()
                self.assertIn('Practice:',spoken[-1])
                self.assertFalse(any('example_secret' in f.read_text(errors='ignore') for f in __import__('pathlib').Path(folder).glob('*.json')))
                self.assertEqual(ui.telemetry_snapshot()['mode'],'not connected or telemetry stale')
                ui.disconnect_live();ui.close()
