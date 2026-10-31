import unittest
from engineer.opponents import OpponentScout
from test_session_review import data
class OpponentTests(unittest.TestCase):
 def test_repeated_segment_pace_advantage(self):
  s=OpponentScout()
  for n in range(1,1801):
   t=n*.2
   s.update(data(t,PlayerCarIdx=0,CarIdxLapDistPct=[(t/100)%1,(.4+t/110)%1],CarIdxTrackSurface=[3,3],CarIdxOnPitRoad=[False,False]),{'ahead':dict(car_idx=1,gap_s=8)})
  self.assertTrue(s.latest);self.assertGreater(s.latest['gain_s'],.15);self.assertGreaterEqual(s.latest['other_passages'],3)
 def test_no_advice_without_opponent_positions(self):
  s=OpponentScout();s.update(data(1),{'ahead':dict(car_idx=1,gap_s=.7)});self.assertEqual(s.latest,{})
 def test_passing_call_is_conditional_and_deduplicated(self):
  s=OpponentScout();s.latest=dict(car_idx=1,sector=4,gain_s=.3,gap_s=.8)
  text=s.voice(data(100));self.assertIn('if the space is clear',text)
  self.assertIsNone(s.voice(data(210)))
 def test_no_pass_call_in_traffic_or_under_braking(self):
  s=OpponentScout();s.latest=dict(car_idx=1,sector=4,gain_s=.3,gap_s=.8)
  self.assertIsNone(s.voice(data(100),occupied=True));self.assertIsNone(s.voice(data(101,Brake=.5)))
 def test_no_pass_call_when_gap_is_large(self):
  s=OpponentScout();s.latest=dict(car_idx=1,sector=4,gain_s=.3,gap_s=3)
  self.assertIsNone(s.voice(data(100)))
