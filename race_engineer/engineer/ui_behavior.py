"""Native desktop input routing and telemetry-derived connection presentation."""
import math,sys
from .core import supported

def connection_state(mode,data,meta,age):
    if mode=='DEMO':return dict(label='SYNTHETIC DEMO',button='Connect iRacing',color='amber')
    if mode!='LIVE':return dict(label='OFFLINE',button='Connect iRacing',color='muted')
    valid=bool(data) and supported(meta) and isinstance(data.get('SessionTime'),(int,float)) and math.isfinite(data['SessionTime'])
    if valid and age<=.35 and data.get('TelemetryAgeSeconds',0)<=.3:return dict(label='IRACING CONNECTED',button='iRacing connected',color='green')
    if data:return dict(label='TELEMETRY LOST',button='Reconnect iRacing',color='amber')
    return dict(label='WAITING FOR IRACING',button='Connecting…',color='amber')

class MouseWheelRouter:
    """Route wheel events using the widget under the pointer, once per app."""
    def __init__(self,root):
        self.root=root;self.remainder={}
        for sequence in ('<MouseWheel>','<Button-4>','<Button-5>'):root.bind_all(sequence,self.route,add='+')
        # Avoid changing a selected option merely by scrolling over its combobox.
        for sequence in ('<MouseWheel>','<Button-4>','<Button-5>'):root.bind_class('TCombobox',sequence,self.combo)
    def combo(self,event):self.route(event);return 'break'
    def route(self,event):
        try:widget=self.root.winfo_containing(event.x_root,event.y_root) or event.widget
        except (AttributeError,TypeError):widget=event.widget
        if widget is None:return
        try:kind=widget.winfo_class()
        except AttributeError:kind=''
        # Native text, lists and tables have their own wheel behavior.
        if kind in ('Text','Listbox','Treeview','TScrollbar','Scrollbar'):return
        owner=widget;target=None
        while owner is not None:
            candidate=getattr(owner,'_wheel_canvas',None)
            if candidate is not None:target=candidate;break
            owner=getattr(owner,'master',None)
        if target is None:return
        button=getattr(event,'num',None);delta=getattr(event,'delta',0)
        if button in (4,5):steps=-3 if button==4 else 3
        elif sys.platform=='darwin':steps=-int(delta)
        else:
            key=id(target);value=self.remainder.get(key,0)-delta/120*3
            steps=int(value);self.remainder[key]=value-steps
        if steps:
            view=target.yview()
            if view and view[0]<=0 and view[1]>=1:return
            target.yview_scroll(steps,'units')
        return 'break'
