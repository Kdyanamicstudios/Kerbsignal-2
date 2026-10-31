import io,json,tempfile,threading,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
from engineer.local_engineer import WakeController,LocalEngineer
from engineer.local_ai import download,extract_runtime,LocalAI
from engineer.voice import Speech


class LocalDialogueTests(unittest.TestCase):
    def test_wake_is_anchored_accepts_homophone_and_expires(self):
        now=[100.];w=WakeController(lambda:now[0])
        self.assertIsNone(w.route('someone said hey kerby before'))
        self.assertEqual(w.route('Hey Kerby'),('wake',''))
        self.assertEqual(w.route('what car am I driving'),('question','what car am i driving'))
        self.assertIsNone(w.route('background chatter'))
        self.assertEqual(w.route('hey kirby can you hear me'),('question','can you hear me'))
        w.route('hey kerby');now[0]+=13;self.assertIsNone(w.route('hello'))
        w.enabled=False;self.assertIsNone(w.route('hey kerby'))
    def test_test_mode_and_engineer_echo_never_wake(self):
        speech=Speech();speech.recognized('hey kirby','1',test=True)
        self.assertEqual(speech.events.get()[0],'heard');self.assertTrue(speech.events.empty())
        speech.speaking=True;speech.recognized('hey kerby','1')
        self.assertEqual(speech.events.get()[0],'heard');self.assertTrue(speech.events.empty())
        speech.speaking=False;speech.recognized('hey kirby','1')
        self.assertEqual(speech.events.get()[0],'heard');self.assertEqual(speech.events.get()[0],'wake')
    def test_offline_lesson_and_followup_are_complete_and_local(self):
        engineer=LocalEngineer();r=engineer.answer('explain trail breaking',{})
        self.assertIn('release',r.text);self.assertIn('Practice:',r.text)
        exercise=engineer.answer('how do I practice that',{});self.assertIn('Review:',exercise.text)
        self.assertNotEqual(engineer.acknowledgment(),engineer.acknowledgment())
    def test_no_unmeasured_braking_markers_or_feedback(self):
        engineer=LocalEngineer()
        self.assertIn('fresh',engineer.answer('when do I brake',{}).text)
        self.assertIn('need',engineer.answer('next braking zone',{'mode':'LIVE'}).text)
        self.assertIn('matching clean reference',engineer.answer('where am I losing time',{'mode':'LIVE'}).text)
    def test_fresh_snapshot_markers_and_actual_reviews(self):
        engineer=LocalEngineer();s={'mode':'LIVE','next_braking_zone':{'distance_m':240,'name':'T4','description':'left turn'}}
        self.assertIn('240 meters',engineer.answer('how far until the next braking zone',s).text)
        r={'name':'T4','loss':.4,'tip':'Try a later marker.','action_metric':'braking distance','action_step':10,'brake_m':-12}
        s['recent_sections']=[r]
        answer=engineer.answer('last corner feedback',s)
        self.assertIn('12 meters',answer.text);self.assertIn('10 meters later',answer.text)
        self.assertIn('entry speed',engineer.answer('why',s).text)
    def test_actions_route_without_online_services(self):
        e=LocalEngineer()
        self.assertEqual(e.answer('play focus music',{}).command,'focus_music')
        self.assertEqual(e.answer('what car am I driving',{}).command,'car')
        self.assertEqual(e.answer('unmute',{}).command,'unmute')


class DownloadSafetyTests(unittest.TestCase):
    def test_download_rejects_hash_mismatch_and_cleans_partial(self):
        class Response(io.BytesIO):
            def geturl(self):return 'https://example.test/model'
        with tempfile.TemporaryDirectory() as folder,patch('engineer.local_ai.urllib.request.urlopen',return_value=Response(b'bad')):
            item={'url':'https://example.test/model','file':'model.gguf','size':3,'sha256':'0'*64}
            with self.assertRaisesRegex(OSError,'verification failed'):download(item,folder,threading.Event(),lambda t:None)
            self.assertFalse(list(Path(folder).iterdir()))
    def test_archive_paths_cannot_escape_private_runtime(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder);zpath=p/'runtime.zip'
            with zipfile.ZipFile(zpath,'w') as z:z.writestr('../escape.exe',b'bad')
            with self.assertRaisesRegex(ValueError,'Unsafe'):extract_runtime(zpath,p/'out')
            self.assertFalse((p/'escape.exe').exists())
    def test_no_cloud_endpoint_is_configurable_and_missing_assets_are_clear(self):
        with tempfile.TemporaryDirectory() as folder:
            ai=LocalAI(folder)
            self.assertFalse(ai.installed())
            with self.assertRaisesRegex(OSError,'Install free local AI'):ai._start()
            ai.close()
