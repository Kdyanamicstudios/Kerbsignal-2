"""Shared application and canvas colors."""
PALETTES={
 'Dark':dict(bg='#0c1114',rail='#0a0f11',panel='#161e23',text='#eef5f1',muted='#a6bbb1',grid='#30433a',accent='#b8f17c',brake='#fc8a9c',green='#a5dfb0',amber='#edc17b',speed='#8fc9f0',steering='#cfb6f4'),
 'Light':dict(bg='#edf1ed',rail='#f9fbf8',panel='#ffffff',text='#202d25',muted='#5c6c62',grid='#d5dfd7',accent='#39701d',brake='#b62b48',green='#267342',amber='#855b0f',speed='#245da3',steering='#7042a2')}


def palette(name):return PALETTES.get(name,PALETTES['Dark'])

def apply(root,style,name):
 p=palette(name)
 style.configure('.',background=p['panel'],foreground=p['text'],font=('Segoe UI',10))
 for kind in ('TFrame','TLabel','TCheckbutton','TNotebook','Workspace.TNotebook'):
  style.configure(kind,background=p['bg'],foreground=p['text'])
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
 style.map('Treeview',background=[('selected',p['accent'])],foreground=[('selected',p['bg'])])
 style.configure('Accent.TButton',background=p['accent'],foreground=p['bg'])
 style.configure('Connected.TButton',background=p['panel'],foreground=p['green']);style.map('Connected.TButton',foreground=[('disabled',p['green'])])
 style.configure('TEntry',fieldbackground=p['panel'],foreground=p['text'],insertcolor=p['text'])
 style.configure('TCombobox',fieldbackground=p['panel'],foreground=p['text'],background=p['grid'],arrowcolor=p['accent'])
 style.map('TCombobox',fieldbackground=[('readonly',p['panel'])],foreground=[('readonly',p['text'])])
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
