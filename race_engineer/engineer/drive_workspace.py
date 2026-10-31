"""The native driving screen: one responsive canvas, no nested scroll containers.

The same painter is used for the desktop and exported design renders. Telemetry
is supplied by App; this module never manufactures session values or a route.
"""
from collections import deque
import math
import textwrap

from .theme import palette


def layout(width, height):
    """Named bounds in the usable driving area. The G meter is always on screen."""
    w, h = max(560, int(width)), max(470, int(height))
    gap = 8 if h < 620 else 12
    metrics_h = 80 if h < 620 else 96
    radio_h = 70 if h < 620 else 92
    graph_h = 108 if h < 620 else 160
    graph_y = h - graph_h
    # Pit Wall keeps the engineer beside the circuit when there is room.
    # Smaller windows retain a shallow radio strip so the map and G meter fit.
    if w >= 1000:
        middle_y = metrics_h + gap
        middle_h = graph_y - gap - middle_y
        radio_w = min(280, round(w * .23))
        g_w = min(330, max(250, round(w * .25)))
        map_w = w - radio_w - g_w - 2*gap
        return dict(metrics=(0, 0, w, metrics_h),
                    radio=(0, middle_y, radio_w, middle_h),
                    map=(radio_w+gap, middle_y, map_w, middle_h),
                    g_force=(w-g_w, middle_y, g_w, middle_h),
                    graph=(0, graph_y, w, graph_h))
    radio_y = metrics_h + gap
    middle_y = radio_y + radio_h + gap
    middle_h = graph_y - gap - middle_y
    side_w = min(330, max(230, round(w * .29)))
    map_w = w - side_w - gap
    return dict(metrics=(0, 0, w, metrics_h), radio=(0, radio_y, w, radio_h),
                map=(0, middle_y, map_w, middle_h),
                g_force=(map_w + gap, middle_y, side_w, middle_h),
                graph=(0, graph_y, w, graph_h))


def text(c, x, y, value, color, size=10, bold=False, anchor='nw', width=None):
    kw = dict(text=str(value), fill=color, anchor=anchor,
              font=('Segoe UI', size, 'bold' if bold else 'normal'))
    if width is not None:kw['width'] = width
    return c.create_text(x, y, **kw)


def short(value, count):
    return textwrap.shorten(str(value).replace('\n', ' '), width=max(5, count), placeholder='…')


def finite(value):
    return isinstance(value, (int, float)) and math.isfinite(value)


def panel(c, bounds, colors):
    x, y, w, h = bounds
    c.create_rectangle(x, y, x+w, y+h, fill=colors['panel'], outline='')


def draw_g_force(c, bounds, model, colors, history=()):
    """Large permanent G-G diagram. Missing acceleration means no plotted dot."""
    x, y, w, h = bounds
    text(c, x+18, y+16, 'G-FORCE', colors['text'], 11, True)
    available_h = h - 80
    r = max(36, min((w-82)/2, available_h/2))
    cx, cy = x+w/2, y+41+available_h/2
    for fraction in (1/3, 2/3, 1):
        c.create_oval(cx-r*fraction, cy-r*fraction, cx+r*fraction, cy+r*fraction,
                      outline=colors['grid'], width=1)
    c.create_line(cx-r, cy, cx+r, cy, fill=colors['grid'])
    c.create_line(cx, cy-r, cx, cy+r, fill=colors['grid'])
    text(c, cx, cy-r-5, 'BRAKING', colors['muted'], 8, anchor='s')
    text(c, cx, cy+r+5, 'ACCELERATION', colors['muted'], 8, anchor='n')
    text(c, cx+r+8, cy, '3g', colors['muted'], 8, anchor='w')
    g = model.get('g_force') if model.get('fresh') else None
    valid = isinstance(g, (tuple, list)) and len(g) == 2 and all(finite(v) for v in g)
    def xy(lat, lon):
        magnitude = math.hypot(lat, lon)
        scale = min(1., 3/max(.001, magnitude))
        return cx-lat/3*r*scale, cy+lon/3*r*scale
    if valid:
        points = [xy(a, b) for a, b in history if finite(a) and finite(b)]
        if len(points) > 1:
            c.create_line(*[v for point in points for v in point], fill=colors['grid'], width=2)
        px, py = xy(*g)
        c.create_oval(px-8, py-8, px+8, py+8, fill=colors['accent'], outline='')
        text(c, x+w-18, y+16, f'{math.hypot(*g):.2f} g', colors['accent'], 12, True, anchor='ne')
        text(c, x+18, y+h-10, f'LAT {g[0]:+.2f} g', colors['muted'], 9, anchor='w')
        text(c, x+w-18, y+h-10, f'LONG {g[1]:+.2f} g', colors['muted'], 9, anchor='e')
    else:
        text(c, cx, cy, '—', colors['muted'], 20, anchor='center')
        text(c, cx, y+h-10, 'Waiting for acceleration telemetry', colors['muted'], 9, anchor='center')
    return cx, cy, r


def draw_map(c, bounds, tracker, plans, colors, fresh):
    x, y, w, h = bounds
    text(c, x+18, y+16, 'CIRCUIT / LIVE POSITION', colors['text'], 11, True)
    pos = tracker.snapshot()
    source = 'GPS LIVE' if fresh and pos.get('valid') and pos.get('gps_live') else 'PROJECTED' if fresh and pos.get('valid') else 'WAITING'
    text(c, x+w-18, y+17, source, colors['green'] if source=='GPS LIVE' else colors['muted'], 9, True, anchor='ne')
    route = getattr(tracker, 'layout', {}) or tracker.route
    points = sorted(route.values())
    if tracker.has_geometry() and points:
        lat0, lon0 = points[0][1:3]
        sx = 111320*math.cos(math.radians(lat0))
        base_xy = lambda lat, lon: ((lon-lon0)*sx, (lat-lat0)*111320)
        base = [base_xy(p[1], p[2]) for p in points]
        bx, by = zip(*base)
        span_x, span_y = max(bx)-min(bx), max(by)-min(by)
        normal_scale = min((w-62)/max(span_x,1), (h-112)/max(span_y,1))
        rotated_scale = min((w-62)/max(span_y,1), (h-112)/max(span_x,1))
        rotated = rotated_scale > normal_scale*1.08
        xy = (lambda lat, lon: (-base_xy(lat, lon)[1], base_xy(lat, lon)[0])) if rotated else base_xy
        projected = [xy(p[1], p[2]) for p in points]
        xs, ys = zip(*projected)
        dx, dy = max(xs)-min(xs), max(ys)-min(ys)
        min_x, max_y = min(xs), max(ys)
        scale = min((w-62)/max(dx, 1), (h-112)/max(dy, 1))
        left = x+(w-dx*scale)/2
        top = y+51+(h-112-dy*scale)/2
        def convert(lat, lon):
            a, b = xy(lat, lon)
            return left+(a-min_x)*scale, top+(max_y-b)*scale
        groups = []
        for p in points:
            if not groups or p[0]-groups[-1][-1][0] >= .012:groups.append([])
            groups[-1].append(p)
        for group in groups:
            if len(group) > 1:
                coords = [v for p in group for v in convert(p[1], p[2])]
                c.create_line(*coords, fill=colors['grid'], width=10, capstyle='round', joinstyle='round')
                c.create_line(*coords, fill=colors['muted'], width=3, capstyle='round', joinstyle='round')
        for plan in plans:
            marker = plan.get('brake')
            if marker is None:continue
            near = route.get(round(marker*1000))
            if near:
                px, py = convert(near[1], near[2])
                c.create_oval(px-4, py-4, px+4, py+4, fill=colors['brake'], outline='')
        if fresh and pos.get('valid') and all(finite(pos.get(k)) for k in ('latitude', 'longitude')):
            px, py = convert(pos['latitude'], pos['longitude'])
            color = colors['green'] if pos.get('gps_live') else colors['amber']
            c.create_oval(px-10, py-10, px+10, py+10, outline=color, width=2)
            c.create_oval(px-5, py-5, px+5, py+5, fill=color, outline='')
    else:
        text(c, x+w/2, y+h/2-5, 'Your detected circuit appears here', colors['text'], 12, True, anchor='center')
        text(c, x+w/2, y+h/2+20, 'Exact layout map or a route learned from GPS', colors['muted'], 9, anchor='center')
    text(c, x+18, y+h-37, short(getattr(tracker, 'map_source', 'Observed GPS route')+' / orientation fitted', max(22, int(w/7))), colors['muted'], 8)
    p = pos.get('lap_fraction') if fresh else None
    progress_y = y+h-14
    c.create_line(x+18, progress_y, x+w-18, progress_y, fill=colors['grid'], width=3)
    if finite(p):
        c.create_line(x+18, progress_y, x+18+max(0, min(1, p))*(w-36), progress_y, fill=colors['accent'], width=3)


def draw_graph(c, bounds, signals, reference, colors, fresh):
    from .core import at
    x, y, w, h = bounds
    text(c, x+18, y+14, 'TELEMETRY / LAST 30 SECONDS', colors['text'], 10, True)
    items = [('MPH', colors['speed']), ('BRAKE', colors['brake']), ('THROTTLE', colors['green']), ('STEERING', colors['steering'])]
    for i, (name, color) in enumerate(items):
        px = x+w-370+i*88
        c.create_line(px, y+21, px+12, y+21, fill=color, width=2)
        text(c, px+17, y+21, name, colors['muted'], 8, anchor='w')
    points = signals.window()
    if not points:
        text(c, x+w/2, y+h/2+10, 'Live speed, pedals and steering appear as you drive', colors['muted'], 10, anchor='center')
        return
    left, right, top, bottom = x+44, x+w-18, y+42, y+h-24
    for f in (0, .5, 1):
        py = bottom-f*(bottom-top)
        c.create_line(left, py, right, py, fill=colors['grid'])
    text(c, left-9, top, '100%', colors['muted'], 8, anchor='e')
    text(c, left-9, bottom, '0', colors['muted'], 8, anchor='e')
    vmax = max(100, math.ceil(max(p[1] for p in points)/25)*25)
    peak = max(45, max(abs(math.degrees(p[5])) for p in points if len(p)>5 and finite(p[5])) if any(len(p)>5 and finite(p[5]) for p in points) else 45)
    end = points[-1][0]
    start = end-30
    step = max(1, len(points)//600)
    for field, color, scale in ((1, 'speed', vmax), (2, 'brake', 1), (3, 'green', 1), (5, 'steering', peak)):
        coords = []
        for point in points[::step]:
            if len(point) <= field or not finite(point[field]):continue
            value = (.5+math.degrees(point[field])/scale*.5) if field==5 else point[field]/scale
            coords.extend((left+max(0, min(1, (point[0]-start)/30))*(right-left), bottom-max(0, min(1, value))*(bottom-top)))
        if len(coords) >= 4:c.create_line(*coords, fill=colors[color], width=1 if field==5 else 2)
    if reference and fresh:
        for field, color, scale in (('speed', 'speed', vmax/2.236936292), ('brake', 'brake', 1), ('throttle', 'green', 1)):
            coords = []
            for point in points[::step]:
                value = at(reference, point[4], field) if len(point)>4 and finite(point[4]) else None
                if value is None:
                    if len(coords)>=4:c.create_line(*coords, fill=colors[color], width=1, dash=(3, 5))
                    coords=[]
                else:coords.extend((left+max(0, min(1, (point[0]-start)/30))*(right-left), bottom-max(0, min(1, value/scale))*(bottom-top)))
            if len(coords)>=4:c.create_line(*coords, fill=colors[color], width=1, dash=(3, 5))
    text(c, left, y+h-10, f'−30s   /   MPH 0–{vmax}   /   steering ±{peak:.0f}°', colors['muted'], 8, anchor='w')
    text(c, right, y+h-10, 'NOW' if fresh else 'STALE / LAST RECEIVED', colors['muted'], 8, anchor='e')


def paint_workspace(c, model, signals, tracker, plans=(), reference=(), history=()):
    """Draw the exact native Drive layout, including its permanent large G meter."""
    p = dict(palette(model.get('theme', 'Dark')))
    c.configure(bg=p['bg']);c.delete('all')
    w, h = max(560, c.winfo_width()), max(470, c.winfo_height())
    boxes = layout(w, h)
    for bounds in boxes.values():panel(c, bounds, p)
    x, y, mw, mh = boxes['metrics']
    widths = (.31, .23, .22, .24)
    labels = ('CURRENT LAP', 'SESSION BEST', 'SESSION DELTA', 'SPEED / GEAR')
    metrics = model.get('metrics', {})
    values = (metrics.get('CURRENT LAP', '—'), metrics.get('BEST LAP', '—'), metrics.get('DELTA', '—'),
              f'{model.get("speed", "—")} mph   /   {model.get("gear", "—")}' if model.get('fresh') else '— mph   /   —')
    px = 0
    for i, (fraction, label, value) in enumerate(zip(widths, labels, values)):
        if i:c.create_line(px, 18, px, mh-18, fill=p['grid'])
        text(c, px+18, 13, label, p['muted'], 9, True)
        font_size=(22 if mh<90 else 25) if i==0 else 18
        font_size=min(font_size,max(11,int((w*fraction-36)/max(1,len(str(value))*.78))))
        text(c, px+18, 31 if mh<90 else 35, value, p['accent'] if i==2 else p['text'], font_size, True)
        if i==0:
            lap=metrics.get('LAP', '—');last=metrics.get('LAST LAP', '—')
            text(c, px+18, mh-11, f'LAP {lap}   /   LAST {last}', p['muted'], 8, anchor='w')
        px += w*fraction
    x, y, rw, rh = boxes['radio']
    c.create_rectangle(x, y, x+4, y+rh, fill=p['accent'], outline='')
    instruction = model.get('instruction', 'Ready when you are') if model.get('fresh') else 'Ready when you are. Connect to iRacing.'
    if rw < w:
        text(c, x+18, y+16, 'ENGINEER RADIO', p['accent'], 10, True)
        text(c, x+18, y+42, 'SYNTHETIC DEMO' if model.get('mode')=='DEMO' else 'LIVE COACH', p['muted'], 8)
        size = 22 if rh >= 400 else 18 if rh >= 340 else 15
        max_lines = 5 if rh >= 340 else 3
        wrapped = textwrap.wrap(instruction, width=max(10, int((rw-36)/(size*.95))))
        if len(wrapped)>max_lines:wrapped=wrapped[:max_lines-1]+[short(' '.join(wrapped[max_lines-1:]), max(10,int((rw-36)/(size*.95))))]
        text(c, x+18, y+76, '\n'.join(wrapped), p['text'], size, True)
        info_y = y+rh-108 if rh>=340 else y+rh-76
        c.create_line(x+18, info_y-16, x+rw-18, info_y-16, fill=p['grid'])
        text(c, x+18, info_y, 'UP NEXT', p['muted'], 8, True)
        briefing = model.get('straight', model.get('coach_state', 'Waiting for telemetry'))
        lines = textwrap.wrap(briefing, width=max(16, int((rw-36)/6.5)))
        text(c, x+18, info_y+22, '\n'.join(lines[:3]), p['muted'], 9)
    else:
        text(c, x+18, y+10, 'ENGINEER / LIVE COACH' if model.get('mode')!='DEMO' else 'ENGINEER / SYNTHETIC DEMO', p['accent'], 9, True)
        size=16 if rh<80 else 17
        text(c, x+18, y+28 if rh<80 else y+31, short(instruction, max(20, int((rw-36)/(size*1.05)))), p['text'], size, True)
        text(c, x+18, y+rh-12, short(model.get('straight', model.get('coach_state', 'Waiting for telemetry')), max(40, int(w/6.4))), p['muted'], 9, anchor='w')
    draw_map(c, boxes['map'], tracker, plans, p, model.get('fresh'))
    draw_g_force(c, boxes['g_force'], model, p, history)
    # On-track estimates remain readable beside the track instead of a hidden pane.
    mx, my, mapw, maph = boxes['map']
    gaps = model.get('gaps', {})
    if mapw >= 430:
        text(c, mx+18, my+40, f'AHEAD {gaps.get("ahead", "—")}    /    BEHIND {gaps.get("behind", "—")}', p['muted'], 9)
    draw_graph(c, boxes['graph'], signals, reference, p, model.get('fresh'))
    return boxes


class DriveWorkspace:
    def __init__(self, parent, canvas):
        self.canvas = canvas(parent, highlightthickness=0, height=620)
        self.canvas.pack(fill='both', expand=True)
        self.model = {};self.last = None;self.history = deque(maxlen=90);self.last_t=None
        self.canvas.bind('<Configure>', self.resize)
    def set_theme(self, name):
        self.model['theme'] = name
    def resize(self, event=None):
        if self.last:self.draw(*self.last, track_history=False)
    def draw(self, signals, tracker, plans=(), reference=(), track_history=True):
        self.last = (signals, tracker, plans, reference)
        t = self.model.get('session_time')
        if not self.model.get('fresh'):
            self.history.clear();self.last_t=None
        elif finite(t) and t!=self.last_t and self.model.get('g_force'):
            if self.last_t is not None and (t<self.last_t or t-self.last_t>.5):self.history.clear()
            if track_history:self.history.append(self.model['g_force']);self.last_t=t
        self.bounds = paint_workspace(self.canvas, self.model, signals, tracker, plans, reference, self.history)
