import unittest
from engineer.core import Sample
from engineer.technique import correction,live_target
class TechniqueTests(unittest.TestCase):
 def samples(self,brake=.5,speed=40):return [Sample(i*.1,.1+i*.001,speed,brake,0,0) for i in range(8)]
 def test_early_braking_steps_later_with_cap(self):
  r=correction(self.samples(),self.samples(),-40,.5)
  self.assertEqual(r['action_step'],15);self.assertIn('later',r['suggested_action'])
 def test_late_braking_steps_earlier(self):
  r=correction(self.samples(),self.samples(),35,.5)
  self.assertEqual(r['action_step'],20);self.assertIn('earlier',r['suggested_action'])
 def test_peak_input_percentage_points(self):
  r=correction(self.samples(.7),self.samples(.5),0,.5)
  self.assertAlmostEqual(r['brake_delta_pp'],20);self.assertEqual(r['action_step'],8);self.assertIn('less',r['suggested_action'])
 def test_speed_mismatch_has_no_numeric_advice(self):
  r=correction(self.samples(speed=60),self.samples(speed=40),-20,.5)
  self.assertIsNone(r['action_step']);self.assertIsNone(r['brake_delta_pp'])
 def test_live_reference_alignment(self):
  r=live_target(dict(LapDistPct=.103,Speed=40,Brake=.7),self.samples(.5))
  self.assertAlmostEqual(r['difference_pp'],20)
 def test_live_without_reference_or_in_pits(self):
  self.assertIsNone(live_target(dict(LapDistPct=.1,Speed=40),[]))
  self.assertIsNone(live_target(dict(LapDistPct=.103,Speed=40,OnPitRoad=True),self.samples()))

class SteeringTests(unittest.TestCase):
 def test_more_and_less_steering_are_reference_relative(self):
  from engineer.technique import live_steering
  ref=[Sample(i*.1,.1+i*.001,30,0,.5,.3) for i in range(10)]
  more=live_steering(dict(LapDistPct=.104,Speed=30,SteeringWheelAngle=.5),ref)
  less=live_steering(dict(LapDistPct=.104,Speed=30,SteeringWheelAngle=.2),ref)
  self.assertGreater(more['difference_deg'],0);self.assertLess(less['difference_deg'],0)
 def test_opposite_turn_not_compared(self):
  from engineer.technique import live_steering
  ref=[Sample(i*.1,.1+i*.001,30,0,.5,.3) for i in range(10)]
  self.assertIsNone(live_steering(dict(LapDistPct=.104,Speed=30,SteeringWheelAngle=-.5),ref))
 def test_spoken_review_keeps_one_action(self):
  from engineer.technique import spoken_review
  r=spoken_review(dict(name='Braking zone 2',loss=.31,tip='Try braking ten meters later.'))
  self.assertIn('0.3 seconds',r);self.assertIn('ten meters later',r);self.assertNotIn('minimum speed',r)
 def test_racecraft_has_exercises_and_sources(self):
  from engineer.racecraft import LESSONS
  self.assertGreaterEqual(len(LESSONS),20)
  for lesson in LESSONS:
   self.assertTrue(lesson[3].startswith('Practice:'));self.assertTrue(lesson[5].startswith('https://www.iracing.com/'))
