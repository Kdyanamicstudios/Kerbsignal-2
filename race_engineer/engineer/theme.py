"""Shared application and canvas colors, including native accessible switches."""
import math
import tkinter as tk
PALETTES={
 'Dark':dict(bg='#0c1114',rail='#0a0f11',panel='#161e23',text='#eef5f1',muted='#a6bbb1',grid='#30433a',accent='#b8f17c',brake='#fc8a9c',green='#a5dfb0',amber='#edc17b',speed='#8fc9f0',steering='#cfb6f4'),
 'Light':dict(bg='#edf1ed',rail='#f9fbf8',panel='#ffffff',text='#202d25',muted='#5c6c62',grid='#d5dfd7',accent='#39701d',brake='#b62b48',green='#267342',amber='#855b0f',speed='#245da3',steering='#7042a2')}


def palette(name):return PALETTES.get(name,PALETTES['Dark'])


def _switch_images(root,style,p):
 """Keep ttk's checkbutton semantics; replace only its cramped indicator."""
 if not isinstance(root,tk.Misc):return
 # ttk elements belong to the Tcl interpreter, shared by all Toplevels.
 # Keep image lifetime and element numbering on that interpreter's Tk root.
 root=root._root()
 scale=max(1.,float(root.tk.call('tk','scaling'))/1.3333333333)
 width,height=max(44,round(44*scale)),max(24,round(24*scale))
 images=[]
 for enabled,disabled in ((False,False),(True,False),(False,True),(True,True)):
  image=tk.PhotoImage(master=root,width=width+round(12*scale),height=height)
  track=p['grid'] if disabled or not enabled else p['accent']
  knob=p['muted'] if disabled else p['panel'] if enabled else p['text']
  radius=height/2-1
  for y in range(height):
   dy=y-(height-1)/2
   inset=math.ceil(radius-math.sqrt(max(0,radius*radius-dy*dy)))+1
   if width-inset>inset:image.put(track,to=(inset,y,width-inset,y+1))
  center=width-height/2 if enabled else height/2
  radius=height/2-4*scale
  for y in range(height):
   dy=y-(height-1)/2
   if abs(dy)>radius:continue
   span=math.sqrt(max(0,radius*radius-dy*dy))
   image.put(knob,to=(round(center-span),y,round(center+span)+1,y+1))
  images.append(image)
 # The Tcl element name is replaced per interpreter/theme as colors change.
 root._switch_images=images
 element='KerbSignalSwitch'+str(getattr(root,'_switch_generation',0))
 root._switch_generation=getattr(root,'_switch_generation',0)+1
 style.element_create(element,'image',str(images[0]),('disabled','selected',str(images[3])),('disabled',str(images[2])),('selected',str(images[1])),width=width+round(12*scale),sticky='')
 style.layout('Switch.TCheckbutton',[
  ('Checkbutton.padding',{'sticky':'nswe','children':[
   ('Checkbutton.focus',{'sticky':'nswe','children':[
    (element,{'side':'left','sticky':''}),
    ('Checkbutton.label',{'side':'left','sticky':'w'})]})]})])

def apply(root,style,name):
 p=palette(name)
 style.configure('.',background=p['panel'],foreground=p['text'],font=('Segoe UI',10))
 for kind in ('TFrame','TLabel','TCheckbutton','TNotebook','Workspace.TNotebook'):
  style.configure(kind,background=p['bg'],foreground=p['text'])
 style.configure('Workspace.TNotebook',borderwidth=0,lightcolor=p['bg'],darkcolor=p['bg'],bordercolor=p['bg'])
 style.configure('Title.TLabel',font=('Segoe UI',23,'bold'),foreground=p['text'])
 style.configure('Brand.TLabel',font=('Segoe UI',19,'bold'),foreground=p['text'],background=p['bg'])
 style.configure('Rail.TFrame',background=p['rail'])
 style.configure('Rail.TLabel',background=p['rail'],foreground=p['text'])
 style.configure('RailBrand.TLabel',background=p['rail'],foreground=p['text'],font=('Segoe UI',14,'bold'))
 style.configure('RailMuted.TLabel',background=p['rail'],foreground=p['muted'],font=('Segoe UI',8))
 style.configure('Subtitle.TLabel',background=p['bg'],foreground=p['muted'],font=('Segoe UI',9))
 style.configure('Metric.TLabel',font=('Bahnschrift',24,'bold'),foreground=p['text'],background=p['panel'])
 style.configure('Card.TFrame',background=p['panel']);style.configure('Card.TLabel',background=p['panel'],foreground=p['muted'])
 style.configure('TButton',padding=(12,8),background=p['panel'],foreground=p['text'],borderwidth=0)
 style.map('TButton',background=[('active',p['grid'])],foreground=[('disabled',p['muted'])])
 style.configure('Nav.TButton',anchor='w',padding=(14,10),background=p['rail'],foreground=p['muted'],font=('Segoe UI',10,'bold'))
 style.configure('ActiveNav.TButton',background=p['panel'],foreground=p['accent'],padding=(14,10),anchor='w',font=('Segoe UI',10,'bold'))
 style.configure('Rail.TButton',background=p['rail'],foreground=p['muted'],padding=(8,6),anchor='w',font=('Segoe UI',9))
 style.configure('Subnav.TButton',anchor='w',padding=(10,6),background=p['rail'],foreground=p['muted'],font=('Segoe UI',9))
 style.configure('SelectedSubnav.TButton',anchor='w',padding=(10,6),background=p['panel'],foreground=p['accent'],font=('Segoe UI',9,'bold'))
 style.configure('TNotebook.Tab',background=p['panel'],foreground=p['muted'],padding=(12,8))
 style.map('TNotebook.Tab',background=[('selected',p['accent'])],foreground=[('selected',p['bg'])])
 style.configure('SettingsRail.TFrame',background=p['panel'])
 style.configure('SettingsCard.TFrame',background=p['panel'],borderwidth=1,relief='flat')
 style.configure('SettingsSection.TLabel',background=p['panel'],foreground=p['text'],font=('Segoe UI',13,'bold'))
 style.configure('SettingsText.TLabel',background=p['panel'],foreground=p['text'],font=('Segoe UI',11))
 style.configure('SettingsMuted.TLabel',background=p['panel'],foreground=p['muted'],font=('Segoe UI',10))
 style.configure('SettingsNav.TButton',anchor='w',padding=(12,14),background=p['panel'],foreground=p['muted'],font=('Segoe UI',10,'bold'),borderwidth=2,relief='flat')
 style.configure('SelectedSettingsNav.TButton',anchor='w',padding=(12,14),background=p['accent'],foreground=p['bg'],font=('Segoe UI',10,'bold'),borderwidth=2,relief='flat')
 for name in ('SettingsNav.TButton','SelectedSettingsNav.TButton'):
  style.map(name,background=[('disabled',p['panel']),('pressed',p['grid']),('active',p['grid'])],foreground=[('disabled',p['muted']),('active',p['text'])],bordercolor=[('focus',p['accent'])],relief=[('focus','solid')])
 style.configure('Switch.TCheckbutton',background=p['panel'],foreground=p['text'],font=('Segoe UI',11),padding=(10,10),focuscolor=p['accent'],focusthickness=2)
 style.map('Switch.TCheckbutton',background=[('active',p['grid'])],foreground=[('disabled',p['muted'])])
 _switch_images(root,style,p)
 style.map('Treeview',background=[('selected',p['accent'])],foreground=[('selected',p['bg'])])
 style.configure('Accent.TButton',background=p['accent'],foreground=p['bg'])
 style.configure('Connected.TButton',background=p['panel'],foreground=p['green']);style.map('Connected.TButton',foreground=[('disabled',p['green'])])
 style.configure('TEntry',fieldbackground=p['panel'],foreground=p['text'],insertcolor=p['text'])
 style.configure('TCombobox',fieldbackground=p['panel'],foreground=p['text'],background=p['grid'],arrowcolor=p['accent'])
 style.map('TCombobox',fieldbackground=[('readonly',p['panel'])],foreground=[('readonly',p['text'])])
 style.configure('Settings.TCombobox',padding=(8,7),borderwidth=1,bordercolor=p['grid'],lightcolor=p['grid'],darkcolor=p['grid'],arrowsize=18)
 style.map('Settings.TCombobox',bordercolor=[('focus',p['accent'])],fieldbackground=[('disabled',p['bg']),('readonly',p['panel'])],foreground=[('disabled',p['muted']),('readonly',p['text'])])
 style.configure('Treeview',background=p['panel'],fieldbackground=p['panel'],foreground=p['text'])
 style.configure('Treeview.Heading',background=p['grid'],foreground=p['text'])
 old={'#99b8d5':'muted','#91a4ba':'muted','#93a5bc':'muted','#627c98':'muted','#8295ad':'muted','#e7edf5':'text','#edf5ff':'text','#ffb65c':'amber','#61caff':'accent','#8beaaf':'green'}
 def visit(widget):
  kind=widget.winfo_class()
  if kind in ('Tk','Toplevel'):widget.configure(bg=p['bg'])
  elif kind=='Canvas':widget.configure(bg=p[getattr(widget,'_theme_background_role','panel')])
  elif kind=='Text':widget.configure(bg=p['panel'],fg=p['text'],insertbackground=p['text'])
  elif kind=='TLabel':
   role=getattr(widget,'_theme_role',None)
   if role is None:role=old.get(str(widget.cget('foreground')).lower());widget._theme_role=role
   if role:widget.configure(foreground=p[role])
  for child in widget.winfo_children() or ():visit(child)
 visit(root)
