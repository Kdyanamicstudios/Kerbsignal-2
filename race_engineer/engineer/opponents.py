"""Opponent pace opportunities from public longitudinal positions, never private inputs."""
import math,statistics
from collections import deque
from .driving import safe_straight,driving
class OpponentScout:
    BINS=40
    def __init__(self):self.states={};self.history={};self.latest={};self.last_voice=-1e9;self.seen=set()
    def update(self,d,relatives):
        self.latest={};t=d.get('SessionTime',0);positions=d.get('CarIdxLapDistPct');surfaces=d.get('CarIdxTrackSurface');pits=d.get('CarIdxOnPitRoad');player=d.get('PlayerCarIdx')
        if not driving(d) or d.get('IsReplayPlaying') or d.get('TelemetryAgeSeconds',0)>.3 or not all(isinstance(v,list) for v in (positions,surfaces,pits)):self.states.clear();return
        for i,p in enumerate(positions):
            if i>=len(surfaces) or i>=len(pits) or pits[i] or surfaces[i]!=3 or not isinstance(p,(int,float)) or not math.isfinite(p) or not 0<=p<1:
                self.states.pop(i,None);continue
            previous=self.states.get(i);u=p
            if previous:
                dt=t-previous['t'];delta=(p-previous['p']+.5)%1-.5
                if not 0<dt<=.5 or not 0<=delta<.025:previous=None
                else:u=previous['u']+delta
            current=dict(t=t,p=p,u=u,boundary=None,edge=None)
            if previous:
                current.update(boundary=previous['boundary'],edge=previous['edge'])
                first=math.floor(previous['u']*self.BINS)+1;last=math.floor(u*self.BINS)
                for edge in range(first,last+1):
                    fraction=(edge/self.BINS-previous['u'])/(u-previous['u']) if u>previous['u'] else 0
                    when=previous['t']+fraction*(t-previous['t'])
                    if current['boundary'] is not None and edge==current['edge']+1:
                        elapsed=when-current['boundary']
                        if .25<=elapsed<=30:self.history.setdefault((i,(edge-1)%self.BINS),deque(maxlen=5)).append(elapsed)
                    current.update(boundary=when,edge=edge)
            self.states[i]=current
        ahead=relatives.get('ahead',{});opponent=ahead.get('car_idx')
        if player not in self.states or opponent not in self.states:return
        currentbin=int(self.states[player]['p']*self.BINS);candidates=[]
        for step in range(1,9):
            sector=(currentbin+step)%self.BINS;own=self.history.get((player,sector),());other=self.history.get((opponent,sector),())
            if len(own)<3 or len(other)<3:continue
            if max(own)-min(own)>1.5 or max(other)-min(other)>1.5:continue
            margin=statistics.median(other)-statistics.median(own)
            if margin>=.15:candidates.append(dict(car_idx=opponent,sector=sector,gain_s=margin,own_passages=len(own),other_passages=len(other),gap_s=ahead.get('gap_s'),estimated=True))
        if candidates:self.latest=max(candidates,key=lambda item:item['gain_s'])
    def voice(self,d,occupied=False):
        item=self.latest;t=d.get('SessionTime',0)
        if not item or occupied or not safe_straight(d) or t-self.last_voice<90:return None
        gap=item.get('gap_s');key=(d.get('Lap'),item['car_idx'],item['sector'])
        if gap is None or not .2<=gap<=1.2 or key in self.seen:return None
        self.seen.add(key);self.last_voice=t
        return f'You’ve been about {item["gain_s"]:.1f} seconds quicker than the car ahead through an upcoming section. Build the exit and look for a pass on the following straight if the space is clear. That is observed pace, not a guarantee of a mistake.'
    def summary(self):
        if not self.latest:return 'Opponent scouting: learning section pace; needs three comparable passages for you and the car ahead.'
        v=self.latest
        return f'Observed opportunity: car index {v["car_idx"]}, section {v["sector"]+1}/40, median gain {v["gain_s"]:.2f}s over {v["own_passages"]}/{v["other_passages"]} passages. Longitudinal positions only; no opponent pedal or steering telemetry.'
