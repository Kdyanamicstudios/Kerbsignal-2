"""Shared native cockpit drawing for dashboard and desktop overlay."""
import tkinter as tk
import sys
import json
import textwrap

BG='#0a101b';PANEL='#121e2e';TEXT='#edf5ff';MUTED='#8295ad';CYAN='#53d7ea';GREEN='#8beaaf';AMBER='#ffbe73';RED='#ff687d'

def draw_g_circle(c,x,y,r,model,p):
 for f in (.5,1):c.create_oval(x-r*f,y-r*f,x+r*f,y+r*f,outline=p['grid'],width=1)
 c.create_line(x-r,y,x+r,y,fill=p['grid']);c.create_line(x,y-r,x,y+r,fill=p['grid'])
 g=model.get('g_force') if model.get('fresh') else None
 if g:
  lateral,longitudinal=g;length=(lateral*lateral+longitudinal*longitudinal)**.5
  scale=min(1,2/max(length,.001));dx=-lateral/2*r*scale;dy=longitudinal/2*r*scale
  c.create_oval(x+dx-3,y+dy-3,x+dx+3,y+dy+3,fill=p['accent'],outline='')
  label=f'{length:.2f} g'
 else:label='G —'
 c.create_text(x,y+r+10,text=label,fill=p['text'],font=('Segoe UI',9,'bold'))
 c.create_text(x,y-r-8,text='BRAKE',fill=p['muted'],font=('Segoe UI',7))

def paint(c,model,compact=False):
 from .theme import palette
 p=palette(model.get('theme','Dark'));c.configure(bg=p['panel']);c.delete('all')
 w=max(160 if compact else 240,c.winfo_width());h=max(80 if compact else 96,c.winfo_height());fresh=model.get('fresh',False)
 instruction=model.get('instruction','Ready when you are') if fresh else 'Waiting for iRacing'
 if compact:
  right=68 if w<240 else 78;available=w-right-18
  instruction=textwrap.shorten(instruction.split('. ')[0],width=max(10,int(available/6)) if w<240 else max(24,int(available/6)*2),placeholder='…')
  c.create_text(10,10,anchor='nw',text=instruction,fill=p['text'],width=available,font=('Segoe UI',8 if w<240 else 10,'bold'))
  c.create_text(10,h-34 if w<240 else h-47,anchor='w',text=f'{model.get("speed","—") if fresh else "—"} MPH  ·  G{model.get("gear","—") if fresh else "—"}',fill=p['accent'],font=('Segoe UI',10 if w<240 else 13,'bold'))
  c.create_text(10,h-13 if w<240 else h-23,anchor='w',text=('DEMO · ' if model.get('mode')=='DEMO' else 'LAP ')+model.get('lap_time','—'),fill=p['text'],font=('Segoe UI',9 if w<240 else 11,'bold'))
  draw_g_circle(c,w-42,h/2-1,min(20 if w<240 else 24,h*.22),model,p)
  return
 c.create_text(18,17,anchor='w',text='SYNTHETIC DEMO' if model.get('mode')=='DEMO' else 'ENGINEER RADIO',fill=p['accent'],font=('Segoe UI',9,'bold'))
 c.create_text(18,39,anchor='nw',text=instruction,fill=p['text'],width=max(150,w-150),font=('Segoe UI',15,'bold'))
 c.create_text(18,h-29,anchor='nw',text=textwrap.shorten(model.get('coach_state','Waiting for telemetry'),width=45,placeholder='…'),width=max(150,w-140),fill=p['muted'],font=('Segoe UI',9))
 c.create_text(w-64,12,text='G FORCE',fill=p['accent'],font=('Segoe UI',8,'bold'))
 draw_g_circle(c,w-64,h/2+2,min(34,h*.25),model,p)

class Overlay:
 def __init__(self,root,folder):
  self.path=folder/'overlay.json';self.window=None;self.root=root;self.drag=None
  self.prefs=dict(visible=True,locked=False,opacity=.9,width=360,height=130,format=2,x=50,y=50)
  try:
   p=json.loads(self.path.read_text());self.prefs.update({k:p[k] for k in self.prefs if k in p})
   if p.get('format')!=2:self.prefs.update(width=360,height=130,format=2)
   for k,lo,hi in (('width',160,1200),('height',80,440),('x',-10000,20000),('y',-10000,20000)):
    self.prefs[k]=max(lo,min(hi,int(self.prefs[k])))
   self.prefs['opacity']=max(.35,min(1.,float(self.prefs['opacity'])))
  except (OSError,ValueError,TypeError):pass
 def save(self):
  if self.window:
   self.prefs.update(x=self.window.winfo_x(),y=self.window.winfo_y())
  self.path.write_text(json.dumps(self.prefs))
 def show(self,visible=True):
  self.prefs['visible']=visible
  if visible and not self.window:
   p=self.prefs;win=tk.Toplevel(self.root);self.window=win
   win.withdraw();win.title('KerbSignal Overlay');win.overrideredirect(True)
   win.configure(bg=BG);win.attributes('-topmost',True);win.attributes('-alpha',p['opacity'])
   win.geometry(f'{p["width"]}x{p["height"]}{p["x"]:+d}{p["y"]:+d}')
   self.canvas=tk.Canvas(win,bg=BG,highlightthickness=1,highlightbackground='#2b4963');self.canvas.pack(fill='both',expand=True)
   self.canvas.bind('<ButtonPress-1>',self.begin);self.canvas.bind('<B1-Motion>',self.move);self.canvas.bind('<ButtonRelease-1>',lambda e:self.save())
  if self.window:
   if visible:self.window.update_idletasks();self.apply_lock();self.window.deiconify();self.apply_lock()
   else:self.window.withdraw()
  self.save()
 def begin(self,event):
  if not self.prefs['locked']:self.drag=(event.x_root,event.y_root,self.window.winfo_x(),self.window.winfo_y())
 def move(self,event):
  if self.drag and not self.prefs['locked']:
   x,y,wx,wy=self.drag;self.window.geometry(f'{event.x_root-x+wx:+d}{event.y_root-y+wy:+d}')
 def apply_lock(self):
  if not self.window or sys.platform!='win32':return
  import ctypes
  from ctypes import wintypes
  u=ctypes.windll.user32
  u.GetParent.argtypes=[wintypes.HWND];u.GetParent.restype=wintypes.HWND
  u.GetWindowLongW.argtypes=[wintypes.HWND,ctypes.c_int];u.GetWindowLongW.restype=ctypes.c_long
  u.SetWindowLongW.argtypes=[wintypes.HWND,ctypes.c_int,ctypes.c_long];u.SetWindowLongW.restype=ctypes.c_long
  u.SetWindowPos.argtypes=[wintypes.HWND,wintypes.HWND,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_int,wintypes.UINT]
  hwnd=u.GetParent(self.window.winfo_id()) or self.window.winfo_id()
  style=u.GetWindowLongW(hwnd,-20)|0x80000|0x8000000|0x80
  style=(style|0x20) if self.prefs['locked'] else (style&~0x20)
  u.SetWindowLongW(hwnd,-20,style);u.SetWindowPos(hwnd,None,0,0,0,0,0x1|0x2|0x4|0x10|0x20)
 def configure(self,locked,opacity,width):
  self.prefs.update(locked=bool(locked),opacity=max(.35,min(1.,float(opacity))),width=max(160,min(1200,int(width))),height=max(96 if int(width)>=240 else 80,round(max(160,min(1200,int(width)))*.36)))
  if self.window:
   p=self.prefs;self.window.geometry(f'{p["width"]}x{p["height"]}');self.window.attributes('-alpha',p['opacity']);self.apply_lock()
  self.save()
 def draw(self,model):
  if self.window and self.prefs['visible']:paint(self.canvas,model,True)
 def close(self):
  self.save()
  if self.window:self.window.destroy();self.window=None
