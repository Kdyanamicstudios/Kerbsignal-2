"""Export the production canvas painter using Pillow; not a Windows screenshot.

This developer tool uses illustrative telemetry with a sourced Spa outline.
No generated imagery, live-session claims or hand-drawn track geometry.
"""
from pathlib import Path
import math
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'race_engineer'))
from PIL import Image,ImageDraw,ImageFont
from engineer.drive_workspace import paint_workspace,text
from engineer.theme import palette
from engineer.position import PositionTracker,SignalTrace
from engineer.map_atlas import MapAtlas


class PillowCanvas:
    def __init__(self,width,height):
        self.w=width;self.h=height;self.image=Image.new('RGB',(width,height));self.text_bounds=[]
        self.draw=ImageDraw.Draw(self.image)
    def winfo_width(self):return self.w
    def winfo_height(self):return self.h
    def configure(self,**kw):
        if kw.get('bg'):self.draw.rectangle((0,0,self.w,self.h),fill=kw['bg'])
    def delete(self,*args):pass
    def create_rectangle(self,*xy,**kw):
        self.draw.rectangle(xy,fill=kw.get('fill') or None,outline=kw.get('outline') or None,width=max(1,round(kw.get('width',1))))
    def create_oval(self,*xy,**kw):
        self.draw.ellipse(xy,fill=kw.get('fill') or None,outline=kw.get('outline') or None,width=max(1,round(kw.get('width',1))))
    def create_line(self,*xy,**kw):
        self.draw.line(xy,fill=kw['fill'],width=max(1,round(kw.get('width',1))),joint='curve')
    def create_text(self,x,y,**kw):
        family,size,*style=kw.get('font',('Segoe UI',10))
        bold='bold' in style
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans'+('-Bold' if bold else '')+'.ttf',round(size*4/3))
        value=str(kw.get('text',''))
        width=kw.get('width')
        if width:
            lines=[]
            for original in value.splitlines():
                line=''
                for word in original.split():
                    candidate=(line+' '+word).strip()
                    if line and self.draw.textlength(candidate,font=font)>width:lines.append(line);line=word
                    else:line=candidate
                lines.append(line)
            value='\n'.join(lines)
        box=self.draw.multiline_textbbox((0,0),value,font=font,spacing=3)
        tw,th=box[2]-box[0],box[3]-box[1]
        anchor=kw.get('anchor','center')
        if anchor in ('n','center','s'):x-=tw/2
        elif anchor in ('ne','e','se'):x-=tw
        if anchor in ('w','center','e'):y-=th/2
        elif anchor in ('sw','s','se'):y-=th
        self.text_bounds.append((x,y,x+tw,y+th,value))
        self.draw.multiline_text((x-box[0],y-box[1]),value,font=font,fill=kw['fill'],spacing=3)


def export(output,appearance='Dark',connected=True):
    colors=palette(appearance)
    trace=SignalTrace()
    with tempfile.TemporaryDirectory() as folder:
        tracker=PositionTracker(Path(folder))
        geometry=MapAtlas().load(dict(track_name='spa_2024_up'))
        tracker.layout={round(p*1000):(p,lat,lon) for p,lat,lon in geometry['points']}
        tracker.map_source='Spa 2024 / Grand Prix · sourced layout geometry'
        p,lat,lon=geometry['points'][round(len(geometry['points'])*.61)]
        tracker.current=dict(valid=connected,gps_live=connected,latitude=lat,longitude=lon,lap_fraction=p,distance_m=p*7004,age_ms=25)
        tracker.last_wall=time.monotonic()
        for i in range(601):
            t=i/20;phase=t%12
            brake=max(0,1-abs(phase-7)/1.4)*.82
            throttle=max(0,min(1,(phase-7.8)/2.2)) if phase>6 else 1
            trace.append(dict(SessionTime=t,Speed=48-26*brake,Brake=brake,Throttle=throttle,LapDistPct=.5+t*.003,SteeringWheelAngle=math.sin(t*.5)*.23))
        model=dict(theme=appearance,fresh=connected,mode='LIVE',instruction='Ease off the brake. Turn in.',
                   speed=112,gear=4,g_force=(.84,-1.12),straight='Next braking zone: 420 m. Medium-speed right. Gaps are passage-time estimates.',
                   metrics={'CURRENT LAP':'2:15.382','BEST LAP':'2:18.904','DELTA':'−0.243','LAP':'06','LAST LAP':'2:19.102'},
                   gaps=dict(ahead='~1.8 s',behind='~3.2 s'))
        centre=PillowCanvas(1140,704)
        paint_workspace(centre,model,trace if connected else SignalTrace(),tracker,history=[(.2+i*.016,-.3-i*.022) for i in range(36)] if connected else [])
    # The centre is the exact production painter. The rail/header illustrate the
    # native ttk shell whose structure and styles are in App.build_ui/theme.py.
    full=PillowCanvas(1380,854);full.configure(bg=colors['bg'])
    full.create_rectangle(0,0,184,854,fill=colors['rail'])
    logo=Image.open(Path(__file__).resolve().parents[1]/'race_engineer/engineer/assets/kerbsignal-64.png').convert('RGBA')
    logo=logo.resize((38,38));full.image.paste(logo,(22,22),logo)
    text(full,22,75,'KERBSIGNAL',colors['text'],14,True)
    text(full,22,103,'YOUR RACE ENGINEER',colors['muted'],8)
    text(full,22,153,'WORKSPACE',colors['muted'],8)
    for i,label in enumerate(('DRIVE','ANALYZE','RACECRAFT','GARAGE','ENGINEER','SETTINGS','HELP')):
        yy=184+i*48
        if i==0:full.create_rectangle(12,yy,172,yy+40,fill=colors['panel'])
        text(full,28,yy+12,label,colors['accent'] if i==0 else colors['muted'],10,True)
    full.create_rectangle(12,660,172,699,fill=colors['panel'])
    text(full,26,672,'iRacing connected' if connected else 'Connect iRacing',colors['green'] if connected else colors['accent'],9,True)
    for yy,label in ((718,'Preview cockpit'),(747,'Stop recording'),(786,'Enable microphone'),(815,'Mute voice')):text(full,22,yy,label,colors['muted'],9)
    text(full,210,23,'Live driving',colors['text'],23,True)
    text(full,210,65,'PRACTICE  /  Porsche 992 GT3 R  /  Spa-Francorchamps · Grand Prix',colors['muted'],10)
    text(full,1350,27,'SAMPLE TELEMETRY',colors['amber'],9,True,anchor='ne')
    text(full,1350,52,'PIT WALL / SIDEBAR',colors['muted'],8,anchor='ne')
    text(full,1350,73,'iRacing connected' if connected else 'OFFLINE',colors['green'] if connected else colors['muted'],8,True,anchor='ne')
    full.image.paste(centre.image,(210,99))
    text(full,210,824,'Pause coach     /     Session recap     /     Reference & timing',colors['muted'],9)
    text(full,1350,824,'PIT WALL · LAYOUT PREVIEW',colors['accent'],9,True,anchor='ne')
    full.image.save(output)


if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    export(root/'KerbSignal_New_UI.png')
    export(root/'windows_build/KerbSignal_New_UI_Light.png','Light')
    export(root/'windows_build/KerbSignal_New_UI_Offline.png',connected=False)
    print('Rendered production Drive painter in dark, light and offline states.')
