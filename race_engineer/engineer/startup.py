"""Brief native branded startup animation; no fabricated loading checks."""
import tkinter as tk
from pathlib import Path
import time
from .theme import palette

WIDTH,HEIGHT=520,340

def paint_startup(canvas,logo,fraction,appearance='Dark'):
    p=palette(appearance);fraction=max(0.,min(1.,fraction))
    canvas.configure(bg=p['bg']);canvas.delete('all')
    canvas.create_image(WIDTH/2,100,image=logo)
    canvas.create_text(WIDTH/2,190,text='KERBSIGNAL',fill=p['text'],font=('Segoe UI',26,'bold'))
    canvas.create_text(WIDTH/2,225,text='YOUR LIVE RACE ENGINEER',fill=p['muted'],font=('Segoe UI',10))
    canvas.create_text(WIDTH/2,307,text='Ready when you are  •  Press Escape to skip',fill=p['muted'],font=('Segoe UI',9))
    x=70+380*(1-(1-fraction)**3)
    canvas.create_line(70,270,450,270,fill=p['grid'],width=3)
    canvas.create_line(70,270,x,270,fill=p['accent'],width=3)
    canvas.create_oval(x-5,265,x+5,275,fill=p['text'],outline='')

class StartupAnimation:
    def __init__(self,root,assets,duration=1.4,appearance='Dark'):
        self.root=root;self.duration=duration;self.appearance=appearance;self.started=time.monotonic();self.done=False
        root.withdraw();self.window=tk.Toplevel(root);self.window.overrideredirect(True)
        x=(root.winfo_screenwidth()-WIDTH)//2;y=(root.winfo_screenheight()-HEIGHT)//2
        self.window.geometry(f'{WIDTH}x{HEIGHT}+{max(0,x)}+{max(0,y)}');self.window.configure(bg=palette(appearance)['bg'])
        self.canvas=tk.Canvas(self.window,width=WIDTH,height=HEIGHT,bg=palette(appearance)['bg'],highlightthickness=0);self.canvas.pack(fill='both',expand=True)
        self.logo=tk.PhotoImage(file=str(Path(assets)/'kerbsignal-128.png'))
        paint_startup(self.canvas,self.logo,0,appearance)
        self.window.bind('<Escape>',lambda event:self.finish());self.window.after(0,self.frame)
    def frame(self):
        if self.done:return
        fraction=min(1,(time.monotonic()-self.started)/self.duration)
        paint_startup(self.canvas,self.logo,fraction,self.appearance)
        if fraction>=1:self.finish()
        else:self.window.after(16,self.frame)
    def finish(self):
        if self.done:return
        self.done=True;self.window.destroy();self.root.deiconify();self.root.lift()
