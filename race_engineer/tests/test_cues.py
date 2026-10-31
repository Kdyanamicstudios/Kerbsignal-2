from types import SimpleNamespace
import unittest

from engineer.core import Sample, at
from engineer.cues import DrivingCues, cue_plans
from engineer.demo import META


def reference():
    result=[]
    for i in range(2001):
        p=i/2000
        brake=.7 if .2<=p<.22 else (.2 if .22<=p<.235 else 0)
        throttle=0 if .2<=p<.235 else (.4 if .235<=p<.25 else 1)
        speed=50 if p<.2 else max(25,50-(p-.2)*1000) if p<.225 else min(50,25+(p-.225)*700)
        result.append(Sample(p*120,p,speed,brake,throttle,.04))
    return result


class CueTests(unittest.TestCase):
    def setUp(self):
        self.coach=SimpleNamespace(reference=reference(),zones=[dict(name='Test braking zone',start=.18,end=.29)],invalid=set())
        self.engine=DrivingCues();self.engine.enabled=True

    def data(self,t,p,**changes):
        speed=at(self.coach.reference,p,'speed')
        d=dict(SessionTime=t,LapDistPct=p,Speed=speed,Lap=2,IsOnTrack=True,OnPitRoad=False,
            PlayerTrackSurface=3,IsReplayPlaying=False,SessionFlags=4,Brake=0,Throttle=1,SteeringWheelAngle=.04)
        d.update(changes);return d

    def test_countdown_and_control_phase_sequence(self):
        t=0.;p=.145;events=[]
        while p<.29:
            brake=at(self.coach.reference,p,'brake')
            throttle=at(self.coach.reference,p,'throttle')
            # Driver delays reaching 65% throttle after the reference pickup.
            if .25<=p<.26:throttle=.4
            d=self.data(t,p,Brake=brake,Throttle=throttle)
            cue=self.engine.update(d,META,self.coach)
            if cue:events.append(cue)
            p+=d['Speed']*.05/META['length'];t+=.05
        self.assertEqual(events,['three','two','one','brake','hold','release','throttle'])

    def test_countdown_survives_start_finish_wrap(self):
        shifted=[]
        for s in reference()[:-1]:
            p=(s.p-.19)%1
            shifted.append(Sample(p*120,p,s.speed,s.brake,s.throttle,s.steer))
        shifted.sort(key=lambda s:s.p)
        first=shifted[0]
        shifted.append(Sample(120.,1.,first.speed,first.brake,first.throttle,first.steer))
        self.coach.reference=shifted
        self.coach.zones=[dict(name='After finish',start=.001,end=.1)]
        t=0.;unwrapped=.972;events=[]
        while unwrapped<1.04:
            p=unwrapped%1
            d=self.data(t,p,Lap=2+int(unwrapped),Speed=at(shifted,p,'speed'),Brake=at(shifted,p,'brake'))
            cue=self.engine.update(d,META,self.coach)
            if cue:events.append(cue)
            unwrapped+=d['Speed']*.05/META['length'];t+=.05
        self.assertEqual([e for e in events if e in ('three','two','one','brake')],['three','two','one','brake'])

    def test_disabled_and_missing_reference_are_silent(self):
        self.engine.enabled=False
        self.assertIsNone(self.engine.update(self.data(0,.18),META,self.coach))
        self.engine.enabled=True;self.coach.reference=[]
        self.assertIsNone(self.engine.update(self.data(0,.18,Speed=50),META,self.coach))

    def test_joining_late_only_plays_future_countdown_thresholds(self):
        events=[]
        for i in range(35):
            cue=self.engine.update(self.data(i*.05,.19+i*.0003),META,self.coach)
            if cue:events.append(cue)
        self.assertNotIn('three',events);self.assertNotIn('two',events)
        self.assertEqual(events,['one','brake'])

    def test_offtrack_flag_and_overspeed_suppress(self):
        for changes in ({'SessionFlags':8},{'OnPitRoad':True},{'Speed':100}):
            engine=DrivingCues();engine.enabled=True;events=[]
            for i in range(120):
                cue=engine.update(self.data(i*.05,.15+i*.0004,**changes),META,self.coach)
                if cue:events.append(cue)
            self.assertFalse(events)

    def test_already_braking_never_gets_brake_countdown(self):
        events=[]
        for i in range(140):
            cue=self.engine.update(self.data(i*.05,.15+i*.0004,Brake=.5),META,self.coach)
            if cue:events.append(cue)
        self.assertFalse({'three','two','one','brake'}&set(events))

    def test_telemetry_gap_drops_countdown(self):
        self.engine.update(self.data(0,.16),META,self.coach)
        self.assertIsNone(self.engine.update(self.data(1,.18),META,self.coach))
        self.assertIsNone(self.engine.update(self.data(1.05,.181),META,self.coach))

    def test_throttle_not_called_with_brake_held(self):
        events=[]
        for i in range(100):
            cue=self.engine.update(self.data(i*.05,.245+i*.0003,Brake=.3,Throttle=0),META,self.coach)
            if cue:events.append(cue)
        self.assertNotIn('throttle',events)

    def test_audio_lead_moves_brake_trigger_within_one_telemetry_tick(self):
        for lead in (0.,.15,.5):
            engine=DrivingCues();engine.enabled=True;engine.lead_seconds=lead
            t=0.;p=.14;triggers=[]
            while p<.205:
                d=self.data(t,p,Brake=0)
                event=engine.update(d,META,self.coach)
                if event=='brake':triggers.append((.2-p)*META['length']/d['Speed'])
                p+=d['Speed']*.05/META['length'];t+=.05
            self.assertEqual(len(triggers),1)
            self.assertLessEqual(abs(triggers[0]-lead),.055)

    def test_turn_in_guidance_also_works_without_braking(self):
        self.coach.reference=[Sample(i*.05,i/4000,50,0,1,.2 if .2<=i/4000<.23 else 0) for i in range(4001)]
        self.coach.zones=[]
        t=0.;p=.18;events=[]
        while p<.24:
            event=self.engine.update(self.data(t,p,SteeringWheelAngle=0),META,self.coach)
            if event:events.append(event)
            p+=50*.05/META['length'];t+=.05
        self.assertEqual(events.count('turn'),1)
        self.assertNotIn('brake',events)


if __name__=='__main__':unittest.main()
