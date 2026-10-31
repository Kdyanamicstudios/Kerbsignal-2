from test_controller import headless_services
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from engineer.ui_behavior import MouseWheelRouter,connection_state
from engineer.demo import META,frame
from engineer.cockpit import paint

class ScrollCanvas:
 def __init__(self,view=(0,.5)):self.calls=[];self.view=view
 def yview(self):return self.view
 def yview_scroll(self,*args):self.calls.append(args)
class Node:
 def __init__(self,master=None,kind='TLabel'):self.master=master;self.kind=kind
 def winfo_class(self):return self.kind
class Root:
 def __init__(self,node):self.node=node;self.bindings=[]
 def bind_all(self,*args,**kw):self.bindings.append(args[0])
 def bind_class(self,*args,**kw):pass
 def winfo_containing(self,*args):return self.node
class CanvasRecorder:
 def __init__(self):self.text=[];self.ovals=[]
 def winfo_width(self):return 390
 def winfo_height(self):return 150
 def configure(self,**kw):pass
 def delete(self,*args):pass
 def create_text(self,*args,**kw):self.text.append(kw.get('text',''))
 def create_oval(self,*args,**kw):self.ovals.append(args)
 def create_line(self,*args,**kw):pass
 def create_rectangle(self,*args,**kw):pass
class UIBehaviorTests(unittest.TestCase):
 def test_wheel_routes_from_child_label_under_pointer(self):
  canvas=ScrollCanvas();content=Node();content._wheel_canvas=canvas;child=Node(content);root=Root(child);router=MouseWheelRouter(root)
  with patch('engineer.ui_behavior.sys.platform','win32'):result=router.route(SimpleNamespace(widget=child,x_root=10,y_root=10,delta=-120,num=0))
  self.assertEqual(result,'break');self.assertEqual(canvas.calls,[(3,'units')])
 def test_native_text_does_not_double_scroll_parent(self):
  canvas=ScrollCanvas();content=Node();content._wheel_canvas=canvas;child=Node(content,'Text');router=MouseWheelRouter(Root(child))
  router.route(SimpleNamespace(widget=child,x_root=0,y_root=0,delta=-120,num=0));self.assertFalse(canvas.calls)
 def test_high_resolution_wheel_accumulates(self):
  canvas=ScrollCanvas();content=Node();content._wheel_canvas=canvas;router=MouseWheelRouter(Root(content))
  with patch('engineer.ui_behavior.sys.platform','win32'):
   for _ in range(4):router.route(SimpleNamespace(widget=content,x_root=0,y_root=0,delta=-10,num=0))
  self.assertEqual(canvas.calls,[(1,'units')])
 def test_connection_requires_valid_fresh_sdk_metadata(self):
  d=frame(150)
  self.assertEqual(connection_state('LIVE',d,META,.1)['button'],'iRacing connected')
  self.assertEqual(connection_state('LIVE',d,META,1)['label'],'TELEMETRY LOST')
  self.assertNotEqual(connection_state('LIVE',d,{},.1)['button'],'iRacing connected')
  self.assertEqual(connection_state('DEMO',d,META,.1)['label'],'SYNTHETIC DEMO')
 def test_main_cockpit_draws_labeled_g_meter(self):
  c=CanvasRecorder();paint(c,dict(theme='Dark',fresh=True,g_force=(.5,-.8),mode='LIVE',instruction='Brake in 200 meters'))
  self.assertIn('G FORCE',c.text);self.assertTrue(any('g' in str(v) for v in c.text));self.assertGreaterEqual(len(c.ovals),3)

class NavigationIntegrationTests(unittest.TestCase):
 def test_settings_is_visible_and_audio_timing_controls_work(self):
  import tempfile,os,app
  from unittest.mock import patch
  from test_controller import Widget,Variable
  with tempfile.TemporaryDirectory() as folder:
   tk=SimpleNamespace(StringVar=Variable,BooleanVar=Variable,Text=Widget,Canvas=Widget,PhotoImage=Widget)
   ttk=SimpleNamespace(**{n:Widget for n in ('Style','Frame','Label','Button','Notebook','Treeview','Scrollbar','Combobox','Entry','Checkbutton')})
   with headless_services(),patch.object(app,'tk',tk),patch.object(app,'ttk',ttk),patch.dict(os.environ,{'RACE_ENGINEER_DATA':folder}):
    ui=app.App(Widget());self.assertIn('SETTINGS',[name for name,items in ui.nav_groups]);self.assertIn((10,'Settings'),dict(ui.nav_groups)['SETTINGS'])
    previous=int(ui.cue_lead.get());ui.adjust_cue_lead(50);self.assertEqual(int(ui.cue_lead.get()),min(1000,previous+50));ui.close()
 def test_tiny_overlay_g_circle_is_within_canvas(self):
  c=CanvasRecorder();c.winfo_width=lambda:160;c.winfo_height=lambda:80
  paint(c,dict(fresh=True,g_force=(.4,-.7),instruction='Brake now',speed=60,gear=3,lap_time='1:23.456'),True)
  for x1,y1,x2,y2 in c.ovals:self.assertTrue(0<=x1<x2<=160 and 0<=y1<y2<=80)
