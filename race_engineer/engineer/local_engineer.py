"""Fast grounded racing answers and a final-transcript local wake gate."""
from collections import deque
from dataclasses import dataclass
import json
import queue
import re
import time
from .racecraft import LESSONS
from .technique import spoken_review,live_reason


def words(text):return ' '.join(re.sub(r'[^a-z0-9 ]',' ',str(text).lower()).split())


class WakeController:
    def __init__(self,clock=time.monotonic):self.clock=clock;self.until=0.;self.enabled=True
    def reset(self):self.until=0.
    def route(self,phrase):
        text=words(phrase)
        match=re.match(r'^hey (?:kerby|kirby)\b\s*(.*)$',text)
        if match and self.enabled:
            self.until=self.clock()+12
            if match[1]:self.until=0.;return 'question',match[1]
            return 'wake',''
        if text.startswith('engineer '):return 'question',text[9:]
        if self.enabled and text and self.clock()<self.until:
            self.until=0.;return 'question',text
        return None


@dataclass(frozen=True)
class Reply:
    text:str=''
    topic:str=''
    command:str=''


class LocalEngineer:
    # Speech owns the single audio channel; this controller never sends audio.
    connected=connecting=recording=pending=muted=False
    def __init__(self,clock=time.monotonic):
        self.clock=clock;self.events=queue.Queue();self.current_car=None
        self.turns=deque(maxlen=8);self.counts={};self.suspended=False
    def set_car(self,identity):
        if identity!=self.current_car:self.turns.clear()
        self.current_car=identity
    def prioritize_driving(self,active):self.suspended=bool(active)
    def close(self):self.turns.clear()
    def choose(self,topic,items):
        n=self.counts.get(topic,0);self.counts[topic]=n+1;return items[n%len(items)]
    def acknowledgment(self):
        return self.choose('wake',('I’m here. What do you need?','Go ahead. I’m listening.','I’m with you. What are we working on?'))
    def lessons(self,question):
        text=words(question).replace('breaking','braking')
        aliases={'trail':'Trail braking & release','weight':'Weight transfer & load sensitivity',
            'red string':'Red string / steering-pedal analogy','friction':'Red string / steering-pedal analogy',
            'draft':'Drafting / slipstream','tire':'Tire management','tyre':'Tire management',
            'late apex':'Racing line & late apex','threshold':'Threshold braking'}
        ranked=[]
        for lesson in LESSONS:
            score=len(set(words(lesson[0]).split())&set(text.split()))
            if any(k in text and v==lesson[0] for k,v in aliases.items()):score+=5
            if score:ranked.append((score,lesson))
        return [l for _,l in sorted(ranked,key=lambda x:x[0],reverse=True)[:2]]
    def context(self,question,snapshot):
        return json.dumps({'telemetry':snapshot,'related_lessons':[l[:5] for l in self.lessons(question)]},ensure_ascii=False,default=str)
    def answer(self,question,snapshot):
        text=words(question).replace('trail breaking','trail braking')
        previous=self.turns[-1][1] if self.turns and self.clock()-self.turns[-1][0]<90 else None
        result=self._answer(text,snapshot or {},previous)
        self.turns.append((self.clock(),result));return result
    def _answer(self,text,s,previous):
        if re.search(r'hear me|microphone (?:check|test)|mic (?:check|test)',text):
            return Reply(self.choose('mic',('Loud and clear. Your microphone and local recognition are working.','You’re coming through. What would you like to work on?','I can hear you clearly. Let’s work on the lap.')),'mic')
        if text in ('thanks','thank you','cheers'):
            return Reply(self.choose('thanks',('Anytime. Let’s keep it tidy.','You’ve got it. One change at a time.','I’m with you. Keep building that rhythm.')),'thanks')
        if re.search(r'what can (?:you|i)|what do i say|help me',text):
            return Reply('Ask about the next braking zone, your last corner, steering, tires, gaps or the current session. You can also ask why a technique works or request a practice exercise. Extended chat is available after installing the free local model.','help')
        if previous and text in ('why','explain that','tell me more','how do i practice that','give me an exercise'):
            lesson=next((l for l in LESSONS if l[0]==previous.topic),None)
            if lesson:return Reply(lesson[3]+' '+lesson[4] if 'practice' in text or 'exercise' in text else lesson[2]+' '+lesson[3],lesson[0])
            if previous.topic=='review' and s.get('recent_sections'):
                return Reply(live_reason(s['recent_sections'][-1]),'review')
        educational=re.search(r'what is|what are|how (?:do|does|can)|teach|explain|practice|tips for',text)
        matches=self.lessons(text)
        if educational and matches:
            l=matches[0];return Reply(l[2]+' '+l[3],l[0])
        commands=(
            (r'^(?:please )?(?:unmute|turn (?:the )?voice on)$','unmute'),
            (r'^(?:please )?(?:mute|be quiet|turn (?:the )?voice off)$','mute'),
            (r'(?:play|start|open).*(?:music|youtube)','focus_music'),
            (r'(?:enable|start|turn on).*brak.*(?:cue|countdown)','enable_cues'),
            (r'(?:disable|stop|turn off).*brak.*(?:cue|countdown)','disable_cues'),
            (r'session recap|session report|debrief','recap'),
            (r'what.*track|which.*track|which circuit','track'),
            (r'what.*car|which.*car|identify.*car','car'),
            (r'^where am i$|where am i on track|my position','position'),
            (r'tire|tyre','tires'),(r'weather|rain|temperature','weather'),
            (r'\babs\b','abs'),(r'traction control|\btc\b','tc'),
            (r'last lap|lap time','last_lap'),(r'setup|set up','setup'),
            (r'passing|pass|overtak|ahead|behind|catch|gap','opportunities'))
        for pattern,command in commands:
            if re.search(pattern,text):return Reply(command=command)
        if s.get('mode') not in ('LIVE','DEMO') and re.search(r'losing|lost|feedback|last corner|last turn|next corner|next turn|brak|steer|throttle',text):
            return Reply('I don’t have fresh driving telemetry yet. Connect iRacing for measured lap feedback. You can still ask me to explain a racing technique.','offline')
        if re.search(r'next (?:corner|turn|brak)|until.*brak|when.*brak|how far',text):
            z=s.get('next_braking_zone') or {};distance=z.get('distance_m')
            if isinstance(distance,(int,float)):
                return Reply(f'{z.get("name","The next braking zone")} is {distance:.0f} meters ahead. '+str(z.get('description') or '')+'. This marker comes from your matched guide or reference; allow for grip and traffic.','next')
            return Reply('I need a matched reference or aligned guide before calling that braking distance. I won’t invent a marker from lap time.','next')
        if re.search(r'why|explain|losing|lost|improv|last corner|last turn|feedback|steer|throttle|brak.*(?:earl|late|more|less)',text):
            reviews=s.get('recent_sections') or []
            if reviews:
                r=max(reviews,key=lambda r:r.get('loss',0)) if 'los' in text else reviews[-1]
                n=self.counts.get('review',0);self.counts['review']=n+1
                return Reply(live_reason(r) if 'why' in text else spoken_review(r,n) or str(r.get('evidence') or 'This corner does not have a reliable comparison yet.'),'review')
            return Reply('I need a complete comparable corner and a matching clean reference before recommending a different braking marker or steering input. Keep this lap consistent, then we can test one measured change.','review')
        return Reply(topic='free')
