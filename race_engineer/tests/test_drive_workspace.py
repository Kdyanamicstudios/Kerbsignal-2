"""Visible layout bounds and live/stale rendering, using the actual Drive painter."""
import math
import tempfile
import unittest
from pathlib import Path
from engineer.drive_workspace import paint_workspace, draw_g_force, layout
from engineer.theme import palette
from engineer.position import PositionTracker, SignalTrace
from engineer.demo import frame, META


class RecordingCanvas:
    def __init__(self, width=1000, height=620):
        self.width=width;self.height=height;self.items=[]
    def winfo_width(self):return self.width
    def winfo_height(self):return self.height
    def configure(self, **kw):pass
    def delete(self, *args):self.items.clear()
    def create_text(self, *coords, **kw):self.items.append(('text', coords, kw))
    def create_oval(self, *coords, **kw):self.items.append(('oval', coords, kw))
    def create_line(self, *coords, **kw):self.items.append(('line', coords, kw))
    def create_rectangle(self, *coords, **kw):self.items.append(('rectangle', coords, kw))


class DriveWorkspaceTests(unittest.TestCase):
    def test_main_panels_remain_visible_at_supported_driving_sizes(self):
        for w,h in ((780,502),(840,540),(1000,620),(1140,750),(1500,920)):
            boxes=layout(w,h)
            for name,(x,y,pw,ph) in boxes.items():
                with self.subTest(width=w,height=h,panel=name):
                    self.assertGreater(ph,0);self.assertGreater(pw,0)
                    self.assertGreaterEqual(x,0);self.assertGreaterEqual(y,0)
                    self.assertLessEqual(x+pw,w);self.assertLessEqual(y+ph,h)
            self.assertGreaterEqual(boxes['g_force'][2],230)
            c=RecordingCanvas(w,h)
            _,_,r=draw_g_force(c,boxes['g_force'],{},palette('Dark'))
            self.assertGreaterEqual(r,68) # At least 136px diameter, not the old 68px radio badge.
            gx,gy,gw,gh=boxes['g_force']
            for kind,coords,kw in c.items:
                if kind=='oval':
                    x1,y1,x2,y2=coords
                    self.assertTrue(gx<=x1<x2<=gx+gw and gy<=y1<y2<=gy+gh)

    def test_offline_circle_is_present_without_a_fake_live_dot(self):
        with tempfile.TemporaryDirectory() as folder:
            tracker=PositionTracker(Path(folder));c=RecordingCanvas()
            paint_workspace(c,dict(fresh=False),SignalTrace(),tracker)
            labels=[kw.get('text') for kind,coords,kw in c.items if kind=='text']
            self.assertIn('G-FORCE',labels)
            self.assertIn('Waiting for acceleration telemetry',labels)
            rings=[kw for kind,coords,kw in c.items if kind=='oval']
            self.assertEqual(len(rings),3)
            self.assertTrue(all(not item.get('fill') for item in rings))

    def test_live_acceleration_uses_sdk_units_and_stale_removes_dot(self):
        p=palette('Dark');c=RecordingCanvas()
        bounds=layout(1000,620)['g_force']
        draw_g_force(c,bounds,dict(fresh=True,g_force=(1.,-2.)),p)
        labels=[kw.get('text') for kind,coords,kw in c.items if kind=='text']
        self.assertIn('2.24 g',labels);self.assertIn('LAT +1.00 g',labels);self.assertIn('LONG -2.00 g',labels)
        self.assertEqual(sum(kind=='oval' and kw.get('fill')==p['accent'] for kind,coords,kw in c.items),1)
        c.items.clear();draw_g_force(c,bounds,dict(fresh=False,g_force=(1.,-2.)),p)
        self.assertFalse(any(kind=='oval' and kw.get('fill')==p['accent'] for kind,coords,kw in c.items))

    def test_large_g_values_clamp_to_circle_and_nonfinite_values_are_unavailable(self):
        p=palette('Dark');bounds=layout(1000,620)['g_force'];c=RecordingCanvas()
        cx,cy,r=draw_g_force(c,bounds,dict(fresh=True,g_force=(12.,-8.)),p)
        coords=next(coords for kind,coords,kw in c.items if kind=='oval' and kw.get('fill')==p['accent'])
        self.assertAlmostEqual(math.hypot((coords[0]+coords[2])/2-cx,(coords[1]+coords[3])/2-cy),r)
        c.items.clear();draw_g_force(c,bounds,dict(fresh=True,g_force=(float('nan'),1.)),p)
        self.assertFalse(any(kind=='oval' and kw.get('fill')==p['accent'] for kind,coords,kw in c.items))

    def test_production_controller_routes_telemetry_to_the_new_driving_canvas(self):
        from test_driving_features import IntegrationFeatures
        with tempfile.TemporaryDirectory() as folder:
            ui=IntegrationFeatures().make_app(folder);ui.start('LIVE')
            ui.ingest({**frame(160),'LatAccel':9.80665,'LongAccel':-19.6133},dict(META));ui.render()
            self.assertEqual(ui.dashboard.model['g_force'],(1.,-2.))
            self.assertTrue(ui.dashboard.model['fresh'])
            self.assertIn('g_force',ui.dashboard.bounds)
            ui.data['TelemetryAgeSeconds']=.6;ui.render()
            self.assertFalse(ui.dashboard.model['fresh']);self.assertFalse(ui.dashboard.history)
            ui.data['TelemetryAgeSeconds']=0
            ui.last_seen-=2;ui.render()
            self.assertFalse(ui.dashboard.model['fresh']);self.assertFalse(ui.dashboard.history)
            ui.close()

    def test_returning_user_is_not_automatically_taken_away_from_drive(self):
        from test_driving_features import IntegrationFeatures
        from test_controller import Widget
        from unittest.mock import patch
        def after(root,ms,callback):root.__dict__.setdefault('scheduled',[]).append(ms)
        with tempfile.TemporaryDirectory() as folder,patch.object(Widget,'after',after,create=True):
            first=IntegrationFeatures().make_app(folder)
            self.assertIn(800,first.root.scheduled)
            first.close()
            returning=IntegrationFeatures().make_app(folder)
            self.assertFalse(returning.options.get('tutorial_completed'))
            self.assertNotIn(800,returning.root.scheduled)
            returning.close()
