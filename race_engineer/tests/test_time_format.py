import unittest
from engineer.time_format import elapsed,lap_time


class TimeFormatTests(unittest.TestCase):
    def test_minutes_and_short_durations(self):
        for value,expected in ((0,'0.0s'),(59.9,'59.9s'),(60,'1:00.0'),(153.7,'2:33.7'),(3600,'60:00.0')):
            with self.subTest(value=value):self.assertEqual(elapsed(value),expected)

    def test_rounding_carries_to_next_minute(self):
        self.assertEqual(elapsed(59.95),'1:00.0')
        self.assertEqual(elapsed(119.999),'2:00.0')
        self.assertEqual(elapsed(59.5,0),'1:00')
        self.assertEqual(lap_time(59.9995),'1:00.000')
        self.assertEqual(lap_time(119.9995),'2:00.000')

    def test_preserves_existing_millisecond_precision(self):
        self.assertEqual(elapsed(153.712,3),'2:33.712')
        self.assertEqual(lap_time(12.345),'0:12.345')

    def test_invalid_times_are_not_measured_zero(self):
        for value in (None,-1,float('nan'),float('inf'),True,'bad'):
            with self.subTest(value=value):
                self.assertEqual(elapsed(value),'—')
                self.assertEqual(lap_time(value),'--:--.---')

    def test_next_brake_panel_uses_minutes(self):
        from engineer.straight import StraightBriefing
        briefing=StraightBriefing()
        briefing.snapshot=dict(distance_m=5000,eta_s=153.7,name='Test corner',description='right turn',minimum_mph=None)
        self.assertIn('~2:33.7',briefing.hud({}))
        self.assertNotIn('153.7s',briefing.hud({}))
