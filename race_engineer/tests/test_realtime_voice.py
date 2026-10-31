import base64
import json
import unittest
from engineer.realtime_voice import RealtimeEngineer, session_event, RATE
from engineer.personality import Personality, VoiceSettings
from pathlib import Path
import tempfile

class Socket:
    def __init__(self):self.sent=[]
    def send(self,event):self.sent.append(json.loads(event))
    def close(self):pass

class AudioInput:
    def stop(self):pass
    def close(self):pass

class RealtimeTests(unittest.TestCase):
    def test_session_is_real_audio_with_selected_voice_and_style(self):
        s=session_event('cedar','Australian','Unfiltered')['session']
        self.assertEqual(s['audio']['input']['format']['rate'],RATE)
        self.assertEqual(s['audio']['output']['voice'],'cedar')
        self.assertIsNone(s['audio']['input']['turn_detection'])
        self.assertIn('Australian',s['instructions'])
        self.assertIn('profanity',s['instructions'])
        with self.assertRaises(ValueError):session_event('not_a_voice','Australian','Clean')

    def test_push_to_talk_sends_context_then_audio_and_response(self):
        e=RealtimeEngineer();e.ws=Socket();e.connected=True;e.recording=True;e.input=AudioInput();e.raw=bytearray(b'\x00\x00'*3000)
        self.assertTrue(e.finish_recording({'lap':2,'speed_kph':75}))
        self.assertEqual([x['type'] for x in e.ws.sent],['conversation.item.create','input_audio_buffer.clear','input_audio_buffer.append','input_audio_buffer.commit','response.create'])
        self.assertEqual(len(base64.b64decode(e.ws.sent[2]['audio'])),6000)
        self.assertIn('"lap": 2',e.ws.sent[0]['item']['content'][0]['text'])
        self.assertTrue(e.pending)
        self.assertFalse(e.coaching('another call'))
        e.handle({'type':'response.done','response':{'status':'completed'}})
        self.assertFalse(e.pending)

    def test_output_audio_and_mute(self):
        e=RealtimeEngineer();e.handle({'type':'session.updated'})
        e.handle({'type':'response.output_audio.delta','delta':base64.b64encode(b'1234').decode()})
        self.assertEqual(e.output.get_nowait(),b'1234');e.output.task_done()
        e.muted=True;e.handle({'type':'response.output_audio.delta','delta':base64.b64encode(b'ab').decode()})
        self.assertTrue(e.output.empty())

    def test_clean_and_unfiltered_preferences_persist(self):
        self.assertNotIn('Fuck',Personality('Clean').decorate('Brake.'))
        self.assertIn('Fuck',Personality('Unfiltered').decorate('Brake.'))
        with tempfile.TemporaryDirectory() as tmp:
            f=Path(tmp)/'voice.json';settings=VoiceSettings(f)
            settings.save('some-voice','Australian male','Unfiltered')
            loaded=VoiceSettings(f)
            self.assertEqual((loaded.voice_id,loaded.style),('some-voice','Unfiltered'))

if __name__=='__main__':unittest.main()
