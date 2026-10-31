import unittest,queue
from engineer.voice import Speech
from engineer.microphone import MicrophoneCapture
class MicrophoneTests(unittest.TestCase):
 def test_test_recognition_cannot_execute_command(self):
  s=Speech();s.recognized('engineer mute','0.90',test=True)
  self.assertEqual(s.events.get()[0],'heard');self.assertTrue(s.events.empty())
 def test_recognized_command_normal_mode(self):
  s=Speech();s.recognized('engineer microphone check','0.92')
  self.assertEqual(s.events.get()[0],'heard');self.assertEqual(s.events.get(),('command','mic_check'))
 def test_echo_suppressed_during_speech(self):
  s=Speech();s.speaking=True;s.recognized('engineer mute','0.9')
  self.assertEqual(s.events.get()[0],'heard');self.assertTrue(s.events.empty())
 def test_meter_initially_silent_and_gain_bounded(self):
  s=MicrophoneCapture(gain=5);self.assertEqual(s.level_db,-80);self.assertEqual(s.gain,3);s.close()
