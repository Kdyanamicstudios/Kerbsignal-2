"""Feedback reaches speech as evidence/action/why without eating a countdown."""
import unittest
from engineer.core import Coach
from engineer.technique import spoken_review
from engineer.demo import frame

class LiveExplanationTests(unittest.TestCase):
    def review(self,**kw):
        return dict(name='Braking zone 2',loss=.45,tip='Try a later marker.',action_metric='braking distance',action_step=10,brake_m=-12,**kw)
    def straight(self,t):
        return {**frame(t),'SessionTime':t,'IsOnTrack':True,'OnPitRoad':False,'IsReplayPlaying':False,'PlayerTrackSurface':3,'SteeringWheelAngle':0.,'Brake':0.,'Throttle':1.,'Speed':50.,'SessionFlags':0}
    def test_numerical_braking_feedback_explains_goal(self):
        text=spoken_review(self.review())
        for expected in ('12 meters earlier','10 meters later','reference','entry speed','release the brake smoothly'):
            self.assertIn(expected,text)
    def test_available_straight_delivers_whole_explanation(self):
        c=Coach();r=self.review();text=spoken_review(r);c.pending=[(100,text,r)]
        self.assertEqual(c.voice(self.straight(105),available_seconds=35),text)
        self.assertFalse(c.pending);self.assertEqual(c.last_spoken_review,r)
    def test_short_straight_defers_then_delivers_without_losing_review(self):
        c=Coach();r=self.review();text=spoken_review(r);c.pending=[(100,text,r)]
        self.assertIsNone(c.voice(self.straight(105),available_seconds=4))
        self.assertTrue(c.pending)
        self.assertEqual(c.voice(self.straight(130),available_seconds=35),text)
    def test_medium_window_keeps_remaining_why_for_next_opportunity(self):
        c=Coach();r=self.review();text=spoken_review(r);c.pending=[(100,text,r)]
        first=c.voice(self.straight(105),available_seconds=16)
        self.assertTrue(first);self.assertLessEqual(len(first.split())/2.6+6,16)
        self.assertTrue(c.pending)
        rest=c.voice(self.straight(130),available_seconds=35)
        self.assertIn('entry speed',rest);self.assertFalse(c.pending)
    def test_stale_or_turning_review_is_not_spoken(self):
        for changes in ({'SteeringWheelAngle':.3},{'OnPitRoad':True},{'SessionFlags':0x8}):
            c=Coach();r=self.review();c.pending=[(100,spoken_review(r),r)]
            self.assertIsNone(c.voice({**self.straight(105),**changes},available_seconds=35))
        c=Coach();r=self.review();c.pending=[(10,spoken_review(r),r)]
        self.assertIsNone(c.voice(self.straight(105),available_seconds=35))
    def test_pressure_advice_uses_percentage_points_and_reason(self):
        r=dict(name='Turn 1',loss=.4,tip='Reduce the peak.',action_metric='brake input percentage points',action_step=8,brake_delta_pp=15)
        s=spoken_review(r)
        self.assertIn('15 percentage points more',s);self.assertIn('8 percentage points less',s);self.assertIn('shedding more speed',s)
