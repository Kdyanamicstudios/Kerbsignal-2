"""Native, offline lesson reader and original topic-specific Canvas diagrams."""
import tkinter as tk
from tkinter import ttk

from .racecraft import lesson_detail
from .theme import palette


class LessonDiagram(tk.Canvas):
    """Responsive conceptual illustrations; never presented as measured telemetry."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, height=360, highlightthickness=0, **kwargs)
        self.detail = None
        self.colors = palette('Dark')
        self.bind('<Configure>', lambda event: self.redraw())

    def show(self, detail, theme='Dark'):
        self.detail = detail
        self.colors = palette(theme)
        self.redraw()

    def redraw(self):
        self.delete('all')
        if not self.detail:
            return
        self.configure(bg=self.colors['panel'])
        self.w = max(240, self.winfo_width())
        self.left, self.top = 26, 40
        self.pw, self.ph = self.w-52, 175
        self._draw(self.detail['diagram'])
        self.create_text(16, 10, anchor='nw', text='CONCEPT DIAGRAM · not live data',
                         fill=self.colors['muted'], font=('Segoe UI', 9, 'bold'), width=self.w-32)
        y = 239
        self.annotation_ids = []
        for role, label in self.notes:
            self.create_line(18, y+7, 36, y+7, fill=self.colors[role], width=3)
            item = self.create_text(45, y, anchor='nw', text=label, width=self.w-60,
                                    fill=self.colors['text'], font=('Segoe UI', 10))
            self.annotation_ids.append(item)
            # Native font metrics determine line wrapping at compact widths.
            y = self.bbox(item)[3]+12
        self.configure(height=max(340,y+8))

    def point(self, x, y):
        return self.left + self.pw*x, self.top + self.ph*y

    def line(self, points, role='accent', width=3, dash=None, arrow=None, smooth=False):
        coords = [v for point in points for v in self.point(*point)]
        return self.create_line(*coords, fill=self.colors[role], width=width,
                                dash=dash, arrow=arrow, smooth=smooth)

    def box(self, x, y, w, h, role='accent'):
        a, b = self.point(x, y); c, d = self.point(x+w, y+h)
        return self.create_rectangle(a, b, c, d, fill=self.colors[role], outline='')

    def label(self, x, y, text, role='text', anchor='center', width=None):
        return self.create_text(*self.point(x, y), text=text, fill=self.colors[role],
                                font=('Segoe UI', 10), anchor=anchor,
                                width=width or max(56, self.pw*.35))

    def car(self, x, y, role='accent', horizontal=False):
        width = .1 if horizontal else .065
        height = .13 if horizontal else .24
        self.box(x-width/2, y-height/2, width, height, role)
        self.box(x-width*.35, y-height*.17, width*.7, height*.28, 'panel')

    def road(self, corner=False):
        if corner:
            points=[(.18,.98),(.18,.55),(.22,.18),(.58,.12),(.96,.12)]
            self.line(points, 'grid', width=32, smooth=True)
            self.line(points, 'muted', width=1, dash=(5,5), smooth=True)
        else:
            self.box(.08, .05, .84, .9, 'grid')
            self.line([(.5,.05),(.5,.95)], 'muted', width=1, dash=(5,5))

    def corner_path(self, role='accent', late=False, dash=None):
        points=([(.10,.98),(.10,.55),(.18,.04),(.58,.10),(.98,.16)] if late else
                [(.18,.98),(.18,.53),(.28,.23),(.59,.17),(.98,.10)])
        self.line(points, role, dash=dash, arrow='last', smooth=True)

    def axes(self, xlabel='Corner progression', ylabel='Relative input'):
        self.line([(.08,.06),(.08,.88),(.97,.88)], 'muted', width=1)
        self.label(.08, 0, ylabel, anchor='w', width=self.pw*.8)
        self.label(.52, 1, xlabel, width=self.pw*.85)

    def plot(self, values, role, dash=None):
        self.line([(.10+i*.84/(len(values)-1), .84-value*.67)
                   for i,value in enumerate(values)], role, dash=dash)

    def _draw(self, kind):
        if kind in ('vision','line','balance','late_pass','switchback','wet'):
            self.road(corner=True)
            self.corner_path(late=kind in ('line','switchback','wet'))
            if kind == 'vision':
                for n,(x,y) in enumerate(((.08,.75),(.34,.4),(.82,.08)),1):
                    px,py=self.point(x,y)
                    self.create_oval(px-11,py-11,px+11,py+11,fill=self.colors['accent'],outline='')
                    self.create_text(px,py,text=str(n),fill=self.colors['bg'],font=('Segoe UI',10,'bold'))
                self.notes=[('accent','1 · Braking marker: plan the speed change.'),('accent','2 · Turn-in: move your focus through the corner.'),('accent','3 · Exit: find the next target before you arrive.')]
            elif kind == 'line':
                self.corner_path('speed',dash=(6,4))
                self.notes=[('accent','Solid · Later apex, exit-focused example.'),('speed','Dashed · Earlier apex comparison.'),('muted','Compare time and speed at the following straight.')]
            elif kind == 'balance':
                self.line([(.18,.98),(.18,.40),(.38,.03),(.98,.03)],'brake',dash=(5,4),smooth=True,arrow='last')
                self.line([(.18,.98),(.18,.45),(.39,.28),(.64,.57)],'amber',dash=(2,3),smooth=True,arrow='last')
                self.notes=[('accent','Solid · Intended path.'),('brake','Dashed · Front runs wide: understeer concept.'),('amber','Dotted · Excess rear rotation: oversteer concept.')]
            elif kind == 'late_pass':
                self.line([(.30,.98),(.30,.48),(.38,.27),(.98,.25)],'speed',smooth=True,arrow='last')
                self.line([(.18,.98),(.18,.10),(.35,-.01),(.90,-.01)],'brake',dash=(5,4),smooth=True,arrow='last')
                self.notes=[('accent','Solid green · One controlled cornering path.'),('speed','Solid blue · Separate room for the other car.'),('brake','Dashed · Overshoot crosses the intended space.')]
            elif kind == 'switchback':
                self.corner_path('speed',dash=(6,4))
                self.car(.41,.17,'speed',True)
                self.car(.20,.52)
                self.notes=[('speed','Dashed · Rival commits to the inside.'),('accent','Solid · Patient turn-in opens the exit.'),('muted','Check separation before moving across a lane.')]
            else:
                for x,y in ((.21,.36),(.36,.18),(.68,.12)):
                    a,b=self.point(x,y)
                    self.create_oval(a-13,b-7,a+13,b+7,fill=self.colors['speed'],outline='')
                self.corner_path('muted',dash=(6,4))
                self.notes=[('speed','Blue patches · Conceptual surface water.'),('muted','Dashed · Familiar dry route may be slippery.'),('accent','Solid · Cautious alternative to evaluate.')]
        elif kind in ('threshold','trail','throttle','steering','tires'):
            if kind == 'threshold':
                self.axes('Braking zone progression');self.plot([0,.95,.9,.72,.51,.22,0],'brake');self.plot([0,1,.25,.85,.2,.35,0],'muted',(5,4))
                self.notes=[('brake','Solid · Controlled build, modulation and release.'),('muted','Dashed · Abrupt, inconsistent input example.'),('muted','No prescribed peak pedal value is implied.')]
            elif kind == 'trail':
                self.axes();self.plot([.95,.94,.74,.49,.25,.08,0],'brake');self.plot([0,.05,.20,.42,.67,.85,.82],'steering')
                self.notes=[('brake','Brake · Reduce demand as the corner develops.'),('steering','Steering · Build turning demand progressively.'),('muted','Illustrative overlap; adapt to car and grip.')]
            elif kind == 'throttle':
                self.axes();self.plot([0,0,.08,.30,.55,.8,1],'green');self.plot([0,.35,.65,.1,.35,.8,1],'muted',(5,4))
                self.notes=[('green','Solid · One sustained throttle build.'),('muted','Dashed · Early stab, then a corrective lift.'),('muted','Judge speed beyond the exit, not first touch.')]
            elif kind == 'steering':
                self.axes('Increasing steering request','Turning response (concept)')
                self.plot([0,.23,.47,.62,.66,.66,.64],'steering');self.plot([0,.23,.47,.7,.88,1,1],'muted',(5,4))
                self.notes=[('steering','Solid · Response can flatten near the limit.'),('muted','Dashed · More requested turn is not guaranteed.'),('muted','Wheel angle alone cannot diagnose tire slip.')]
            else:
                self.axes('Consecutive laps','Illustrative lap time · lower is better')
                self.plot([.33,.22,.55,.42,.76,.89,.7],'brake');self.plot([.36,.34,.38,.35,.40,.39,.43],'green')
                self.notes=[('brake','Pink · Variable push-run example.'),('green','Green · More consistent-run example.'),('muted','Compare the stint mean, spread and conditions.')]
        elif kind == 'string':
            x,y=self.point(.5,.48);r=min(self.pw*.34,77)
            self.create_oval(x-r,y-r,x+r,y+r,outline=self.colors['grid'],width=2)
            self.create_line(x-r,y,x+r,y,fill=self.colors['muted'],dash=(3,4))
            self.create_line(x,y-r,x,y+r,fill=self.colors['muted'],dash=(3,4))
            self.create_line(x,y+r*.82,x+r*.70,y+r*.40,x+r*.82,y,x+r*.60,y-r*.53,x,y-r*.82,
                             fill=self.colors['accent'],smooth=True,width=3,arrow='last')
            self.label(.03,.48,'Turn',anchor='w',width=self.pw*.20)
            self.notes=[('brake','Lower region · More braking, less turning.'),('steering','Side region · More turning, less spare pedal demand.'),('green','Upper region · Build drive as turning demand falls.')]
        elif kind == 'load':
            for center,role in ((.27,'brake'),(.73,'steering')):
                self.box(center-.10,.20,.20,.58,'grid')
                for dx,dy in ((-.11,.27),(.11,.27),(-.11,.69),(.11,.69)):
                    px,py=self.point(center+dx,dy)
                    big = dy < .5 if center < .5 else dx > 0
                    r=12 if big else 6
                    self.create_oval(px-r,py-r,px+r,py+r,fill=self.colors[role],outline='')
            self.line([(.27,.70),(.27,.14)],'brake',arrow='last')
            self.line([(.61,.49),(.86,.49)],'steering',arrow='last')
            self.label(.27,.97,'Braking');self.label(.73,.97,'Turning left')
            self.notes=[('brake','Larger front circles · Increased front load.'),('steering','Larger outside circles · Increased outside load.'),('muted','Circle sizes show direction, not actual forces.')]
        elif kind in ('draft','pass','defense','multiclass','start','rejoin'):
            self.road()
            if kind == 'draft':
                self.car(.5,.25,'speed');self.car(.5,.75)
                for dx in (-.13,0,.13):self.line([(.5+dx,.43),(.5+dx*1.7,.94)],'muted',width=1,dash=(4,3))
                self.line([(.73,.90),(.73,.40)],arrow='last')
                self.notes=[('speed','Front car · Airflow changes behind it.'),('accent','Following car · Closing speed may increase.'),('muted','Plan braking margin before the queue compresses.')]
            elif kind == 'pass':
                self.car(.66,.24,'speed');self.car(.33,.64)
                self.line([(.33,.90),(.33,.20)],arrow='last')
                self.line([(.33,.18),(.65,.03)],'muted',dash=(4,3),arrow='last')
                self.notes=[('accent','Choose a lane before braking.'),('speed','Leave the other driver a usable path.'),('muted','Return only after clearance is established.')]
            elif kind == 'defense':
                self.car(.32,.25);self.car(.70,.75,'speed')
                self.line([(.32,.65),(.32,.03)],arrow='last')
                self.line([(.32,.24),(.70,.10)],'brake',dash=(5,4),arrow='last')
                self.notes=[('accent','Solid · Early, preselected defensive lane.'),('speed','Pursuer · Must still have a usable path.'),('brake','Dashed · Reactive closure illustrates blocking.')]
            elif kind == 'multiclass':
                self.car(.66,.30,'speed');self.car(.30,.80)
                self.line([(.66,.70),(.66,.07)],'speed',arrow='last')
                self.line([(.30,.95),(.30,.12)],arrow='last')
                self.notes=[('speed','Slower class · Keep intentions predictable.'),('accent','Faster class · Plan the passing window.'),('muted','Longer arrow denotes relative closing speed.')]
            elif kind == 'start':
                for x,y in ((.32,.21),(.68,.36),(.32,.58),(.68,.74)):
                    self.car(x,y,'speed')
                self.line([(.32,.94),(.32,.78)],arrow='last')
                self.line([(.68,.18),(.68,.03)],'speed',arrow='last')
                self.notes=[('speed','Field · Anticipate early slowing ahead.'),('accent','Open space · Preserve reaction margin.'),('muted','Follow the event’s actual start procedure.')]
            else:
                self.car(.68,.32,'speed');self.car(.02,.82)
                self.line([(.02,.80),(.09,.64),(.23,.40),(.23,.08)],arrow='last',smooth=True)
                self.line([(.02,.80),(.72,.55)],'brake',dash=(5,4),arrow='last')
                self.notes=[('accent','Solid · Wait, check, then merge predictably.'),('speed','Traffic · Check approaching cars and sight lines.'),('brake','Dashed · Direct crossing risks another collision.')]
        elif kind == 'fuel':
            self.box(.08,.25,.72,.25,'green');self.box(.80,.25,.09,.25,'amber')
            self.label(.43,.38,'25 L example',role='bg',width=self.pw*.65)
            self.label(.49,.72,'10 laps × 2.5 L + 3 L reserve = 28 L',width=self.pw*.92)
            self.notes=[('green','Estimated use · Based on representative laps.'),('amber','Reserve · A separate practical allowance.'),('muted','Teaching numbers; not a live fuel recommendation.')]
        elif kind == 'setup':
            self.axes('Baseline A → change B → return A','Illustrative lap time')
            for x,h,role,label in ((.22,.65,'speed','A'),(.51,.58,'accent','B'),(.80,.62,'speed','A')):
                self.box(x-.07,.86-h,.14,h,role);self.label(x,.94,label)
                self.line([(x,.86-h-.07),(x,.86-h+.07)],'text',width=1)
            self.notes=[('speed','A · Repeat the original baseline.'),('accent','B · Change just one adjustable item.'),('muted','Variation bars: several laps, not one best lap.')]
        elif kind == 'practice':
            labels=('Observe','Hypothesis','Review','One test')
            for n,label in enumerate(labels):
                x=.03+(n%2)*.52;y=.12+(n//2)*.52
                a,b=self.point(x,y);c,d=self.point(x+.42,y+.25)
                self.create_rectangle(a,b,c,d,outline=self.colors['accent'],width=2)
                self.label(x+.21,y+.125,label,width=self.pw*.39)
            self.line([(.46,.24),(.54,.24)],arrow='last')
            self.line([(.76,.39),(.76,.60)],arrow='last')
            self.line([(.53,.76),(.45,.76)],arrow='last')
            self.notes=[('accent','Observation · Describe what you can verify.'),('accent','Hypothesis and test · Change one thing.'),('muted','Review · Keep, revise or reject; then repeat.')]
        else:
            raise ValueError('Unknown lesson diagram: '+kind)


class RacecraftLessonView(ttk.Frame):
    """Scrollable native reader with selectable text and a diagram for every topic.

    Integrate with ``view.show_lesson(LESSONS[index])`` and call
    ``view.set_theme(name)`` when the app changes its saved theme.
    """
    def __init__(self, parent, theme='Dark', **kwargs):
        super().__init__(parent, **kwargs)
        self.theme_name = theme
        self.lesson = None
        self.text = tk.Text(self, wrap='word', font=('Segoe UI',11), padx=18, pady=16,
                            relief='flat', width=34, state='disabled', cursor='arrow')
        scroll=ttk.Scrollbar(self, orient='vertical', command=self.text.yview)
        self.text.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right',fill='y');self.text.pack(side='left',fill='both',expand=True)
        self.diagram = None
        self.text.bind('<Configure>',self._resize)
        self.text.tag_configure('title',font=('Segoe UI',20,'bold'),spacing3=8)
        self.text.tag_configure('category',font=('Segoe UI',10,'bold'),spacing3=12)
        self.text.tag_configure('heading',font=('Segoe UI',12,'bold'),spacing1=14,spacing3=5)
        self.text.tag_configure('body',spacing3=8,lmargin2=0)
        self.text.tag_configure('numbered',lmargin1=0,lmargin2=23,spacing3=8)
        self.text.tag_configure('note',font=('Segoe UI',10),spacing3=8)
        self.set_theme(theme)
        self.clear('Choose a technique to read its complete lesson and annotated visual.')

    def _wheel(self,event):
        self.text.yview_scroll(-int(event.delta/120) or (-1 if event.delta>0 else 1),'units')
        return 'break'

    def _resize(self,event=None):
        if self.diagram is not None:
            self.diagram.configure(width=max(240,self.text.winfo_width()-40))

    def set_theme(self,name):
        self.theme_name=name
        p=palette(name)
        self.text.configure(bg=p['panel'],fg=p['text'],insertbackground=p['text'],
                            selectbackground=p['accent'],selectforeground=p['bg'])
        self.text.tag_configure('category',foreground=p['accent'])
        self.text.tag_configure('note',foreground=p['muted'])
        if self.lesson and self.diagram is not None:self.diagram.show(lesson_detail(self.lesson),name)

    def clear(self,message='No matching topics. Try another word or clear the search.'):
        """Clear the selected topic, including its embedded diagram."""
        self.text.configure(state='normal')
        self.text.delete('1.0','end')
        self.diagram=None
        self.lesson=None
        self.text.insert('end',message,'body')
        self.text.configure(state='disabled')
        self.text.yview_moveto(0)

    def show_lesson(self,lesson,theme=None):
        detail=lesson_detail(lesson)
        self.lesson=lesson
        if theme:self.set_theme(theme)
        self.text.configure(state='normal');self.text.delete('1.0','end')
        # Text.delete destroys embedded windows; recreate for every selection.
        self.diagram = LessonDiagram(self.text)
        self.diagram.bind('<MouseWheel>',self._wheel,add='+')
        def insert(text,tag='body'):self.text.insert('end',text+'\n',tag)
        def section(heading,content):
            insert(heading,'heading')
            if isinstance(content,(tuple,list)):
                for n,item in enumerate(content,1):insert(f'{n}. {item}','numbered')
            else:insert(content)
        insert(detail['title'],'title');insert(detail['category'].upper()+' · OFFLINE LESSON','category')
        section('How the technique works',detail['how'])
        section('Why it helps',detail['why'])
        insert('Read the visual','heading')
        self.text.window_create('end',window=self.diagram)
        insert('')
        insert(detail['caption'],'note')
        section('Try it step by step',detail['steps'])
        section('Common mistakes',detail['mistakes'])
        section('Practice exercise',detail['exercise'])
        section('What to compare',detail['review'])
        section('Limits and judgment',detail['caveats'])
        insert('Original KerbSignal teaching text and conceptual diagram. All lesson content is stored inside the app. Optional official background: '+detail['source'],'note')
        self.text.configure(state='disabled')
        self.text.yview_moveto(0)
        self.diagram.show(detail,self.theme_name)
        self._resize()
