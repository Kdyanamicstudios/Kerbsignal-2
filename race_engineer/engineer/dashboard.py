"""Native canvas dashboard. No browser, chart service or network dependency."""
import math

COLORS={'bg':'#0b111b','grid':'#223044','muted':'#91a4ba','text':'#edf4ff','speed':'#55c2ff','brake':'#ff6978','throttle':'#64dba1','map':'#42566c'}


class Dashboard:
    def __init__(self,parent,canvas):
        self.colors=dict(COLORS)
        self.graph=canvas(parent,width=650,height=180,bg=COLORS['bg'],highlightthickness=0)
        self.graph.pack(side='bottom',fill='x',expand=False,pady=(10,0))
        self.map=canvas(parent,width=650,height=360,bg=COLORS['bg'],highlightthickness=0)
        self.map.pack(side='top',fill='both',expand=True)

    def set_theme(self,name):
        from .theme import palette
        p=palette(name);self.colors.update(bg=p['panel'],grid=p['grid'],muted=p['muted'],text=p['text'],speed=p['accent'],brake=p['brake'],throttle=p['green'],map=p['muted'])
        self.graph.configure(bg=p['panel']);self.map.configure(bg=p['panel'])

    def draw(self,signals,tracker,plans=(),reference=()):
        self.draw_graph(signals.window(),reference);self.draw_map(tracker,plans)

    def draw_graph(self,points,reference=()):
        c=self.graph;c.delete('all');w=max(100,c.winfo_width());h=max(100,c.winfo_height())
        c.create_text(14,16,anchor='w',text='LIVE INPUTS  /  30 SEC',fill=self.colors['text'],font=('Segoe UI',10,'bold'))
        c.create_text(w-12,16,anchor='e',text='PEDALS 0–100%',fill=self.colors['muted'],font=('Segoe UI',9))
        if not points:
            c.create_text(w/2,h/2,text='Waiting for live telemetry',fill=self.colors['muted']);return
        left,right,top,bottom=42,w-12,38,h-100
        for f in (0,.25,.5,.75,1):
            y=bottom-f*(bottom-top);c.create_line(left,y,right,y,fill=self.colors['grid'])
        vmax=max(100,math.ceil(max(p[1] for p in points)/25)*25)
        c.create_text(left-5,top,anchor='e',text=str(vmax),fill=self.colors['speed'])
        c.create_text(left-5,bottom,anchor='e',text='0',fill=self.colors['muted'])
        end=points[-1][0];start=end-30
        for field,color,scale in ((1,'speed',vmax),(2,'brake',1),(3,'throttle',1)):
            stride=max(1,len(points)//700);coords=[]
            for p in points[::stride]:coords.extend((left+(p[0]-start)/30*(right-left),bottom-max(0,min(1,p[field]/scale))*(bottom-top)))
            if len(coords)>=4:c.create_line(*coords,fill=self.colors[color],width=2)
        if reference:
            from .core import at
            for field,color,scale in [('speed','speed',vmax/2.236936292),('brake','brake',1),('throttle','throttle',1)]:
                coords=[]
                for p in points[::max(1,len(points)//400)]:
                    value=at(reference,p[4],field) if len(p)>4 and p[4] is not None else None
                    if value is None:
                        if len(coords)>=4:c.create_line(*coords,fill=self.colors[color],width=1,dash=(3,5))
                        coords=[];continue
                    coords.extend((left+(p[0]-start)/30*(right-left),bottom-max(0,min(1,value/scale))*(bottom-top)))
                if len(coords)>=4:c.create_line(*coords,fill=self.colors[color],width=1,dash=(3,5))
        steering=[p for p in points if len(p)>5 and p[5] is not None]
        if steering:
            peak=max(45,math.ceil(max(abs(math.degrees(p[5])) for p in steering)/45)*45);center=h-60;coords=[]
            c.create_line(left,center,right,center,fill=self.colors['grid'])
            for p in steering[::max(1,len(steering)//600)]:coords.extend((left+(p[0]-start)/30*(right-left),center-math.degrees(p[5])/peak*22))
            if len(coords)>=4:c.create_line(*coords,fill='#e9b66f',width=2)
            c.create_text(left,h-88,anchor='w',text=f'STEERING WHEEL ±{peak}°  /  DASHED: MATCHED REFERENCE',fill=self.colors['muted'],font=('Segoe UI',8))
        for x,label,color in ((left,'MPH','speed'),(left+70,'BRAKE %','brake'),(left+165,'THROTTLE %','throttle')):
            c.create_text(x,h-10,anchor='w',text=label,fill=self.colors[color],font=('Segoe UI',9))

    def draw_map(self,tracker,plans):
        c=self.map;c.delete('all');w=max(100,c.winfo_width());h=max(100,c.winfo_height());pos=tracker.snapshot()
        c.create_text(12,16,anchor='w',text='CIRCUIT  /  LIVE POSITION',fill=self.colors['text'],font=('Segoe UI',10,'bold'))
        route=getattr(tracker,'layout',{}) or tracker.route
        points=sorted(route.values())
        if tracker.has_geometry():
            lat0=points[0][1];lon0=points[0][2];sx=111320*math.cos(math.radians(lat0))
            xy=lambda lat,lon:((lon-lon0)*sx,(lat-lat0)*111320)
            coords=[xy(p[1],p[2]) for p in points];xs,ys=zip(*coords)
            scale=min((w-50)/max(max(xs)-min(xs),1),(h-95)/max(max(ys)-min(ys),1))
            xmin,ymin=min(xs),min(ys)
            convert=lambda lat,lon:(25+(xy(lat,lon)[0]-xmin)*scale,h-45-(xy(lat,lon)[1]-ymin)*scale)
            # Break the outline at unobserved sections rather than inventing a route.
            groups=[]
            for p in points:
                if not groups or p[0]-groups[-1][-1][0]>=.012:groups.append([])
                groups[-1].append(p)
            for group in groups:
                if len(group)>1:c.create_line(*[v for p in group for v in convert(p[1],p[2])],fill=self.colors['map'],width=3)
            for plan in plans:
                marker=plan.get('brake') if plan.get('brake') is not None else plan.get('turn')
                if marker is None:continue
                near=route.get(round(marker*1000))
                if near:
                    x,y=convert(near[1],near[2]);c.create_oval(x-3,y-3,x+3,y+3,fill=self.colors['brake'],outline='')
            if pos.get('valid') and pos.get('latitude') is not None:
                x,y=convert(pos['latitude'],pos['longitude']);c.create_oval(x-6,y-6,x+6,y+6,fill=self.colors['throttle'] if pos.get('gps_live') else '#ffb65c',outline='white',width=2)
        else:
            c.create_text(w/2,h/2-5,text='Learning route from GPS\nLap-distance position remains live',fill=self.colors['muted'],justify='center')
        c.create_text(12,34,anchor='w',text=getattr(tracker,'map_source','Observed GPS route')+'  •  Green: GPS / Amber: projected',fill=self.colors['muted'],font=('Segoe UI',9))
        p=pos.get('lap_fraction')
        c.create_line(16,h-27,w-16,h-27,fill=self.colors['grid'],width=5)
        if p is not None:
            c.create_line(16,h-27,16+p*(w-32),h-27,fill=self.colors['speed'],width=5)
            c.create_text(12,h-10,anchor='w',text=f'{p*100:.1f}%  •  {pos.get("distance_m",0):.0f} m  •  {pos.get("age_ms",0)} ms',fill=self.colors['text'])
