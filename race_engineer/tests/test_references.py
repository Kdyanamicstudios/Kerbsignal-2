"""Car/layout isolation and external CSV integrity, without account/network access."""
import csv
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from engineer.core import Sample, zones, supported, Coach
from engineer.demo import META
from engineer.external_reference import Garage61, csv_reference
from engineer.storage import Store


PROFILE={**META,'length':5000.,'car_id':101}
CONTEXT=(False,1,2,3)


def native_csv(skip=None, **overrides):
    out=io.StringIO();writer=csv.DictWriter(out,fieldnames=['Speed','LapDistPct','Brake','Throttle','SteeringWheelAngle','PositionType','Lat','Lon'])
    writer.writeheader()
    for i in range(2001):
        if skip and skip(i):continue
        p=i/2000
        row=dict(Speed=50,LapDistPct=p,Brake=.6 if .2<=p<.23 else 0,Throttle=0 if .2<=p<.23 else 1,SteeringWheelAngle=.1 if .22<=p<.27 else 0,PositionType=3,Lat=29,Lon=-81+p*.01)
        row.update(overrides);writer.writerow(row)
    return out.getvalue()


class ReferenceTests(unittest.TestCase):
    def test_csv_units_timing_and_provenance_roundtrip(self):
        payload=csv_reference(native_csv(),dict(id='lap-123',lapTime=100),PROFILE,CONTEXT)
        self.assertEqual(payload['samples'][0]['speed'],50)  # meters/second, not km/h
        self.assertAlmostEqual(payload['samples'][-1]['t'],100)
        self.assertTrue(payload['provenance']['derived_time'])
        self.assertEqual(payload['provenance']['lap_id'],'lap-123')
        coach=Coach();coach.import_reference(payload,PROFILE,CONTEXT)
        self.assertTrue(coach.zones)

    def test_csv_rejects_missing_section_and_timing_mismatch(self):
        for text,lap_time in ((native_csv(skip=lambda i:100<i<110),100),(native_csv(),70),(native_csv(skip=lambda i:i<20),100)):
            with self.subTest(lap_time=lap_time),self.assertRaises(ValueError):
                csv_reference(text,dict(id='bad',lapTime=lap_time),PROFILE,CONTEXT)

    def test_csv_rejects_pit_nonfinite_and_wrong_controls(self):
        for changes in ({'PositionType':2},{'Speed':'nan'},{'Brake':1.2},{'LapDistPct':-.1}):
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                csv_reference(native_csv(**changes),dict(id='bad',lapTime=100),PROFILE,CONTEXT)

    def test_saved_baselines_separate_demo_car_layout_and_weather(self):
        payload=csv_reference(native_csv(),dict(id='sample',lapTime=100),PROFILE,CONTEXT)
        with tempfile.TemporaryDirectory() as folder:
            store=Store(Path(folder)/'history.db')
            store.save_external_reference(payload,'DEMO')
            self.assertIsNone(store.reference(PROFILE,CONTEXT,'LIVE'))
            self.assertIsNotNone(store.reference(PROFILE,CONTEXT,'DEMO'))
            store.save_external_reference(payload,'LIVE')
            for meta,conditions in (({**PROFILE,'config':'alternate'},CONTEXT),({**PROFILE,'track_id':999},CONTEXT),({**PROFILE,'car_path':'different'},CONTEXT),(PROFILE,(True,3,2,3))):
                self.assertIsNone(store.reference(meta,conditions))
            store.close();store=Store(Path(folder)/'history.db')
            self.assertEqual(store.reference(PROFILE,CONTEXT)['provenance']['lap_id'],'sample')
            store.close()

    def test_short_and_long_tracks_use_meter_based_zones(self):
        for length in (2000.,25000.):
            samples=[Sample(i*.05,(400+i*2.5)/length,50,.6 if 20<=i<=40 else 0,0,0) for i in range(100)]
            found=zones(samples,length)
            self.assertEqual(len(found),1)
            self.assertAlmostEqual(found[0]['start']*length,405.)
            self.assertAlmostEqual(found[0]['end']*length,750.)
            self.assertTrue(supported({**PROFILE,'length':length,'track':'A different track','config':'Full','car_path':'other-car'}))

    def test_api_selects_fastest_clean_visible_exact_match(self):
        client=Garage61('test-token')
        cars={'items':[dict(id=7,platform='iracing',platform_id='101')]}
        tracks={'items':[dict(id=8,platform='iracing',platform_id=str(PROFILE['track_id']))]}
        def lap(id,time,**changes):
            return dict(id=id,lapTime=time,clean=True,canViewTelemetry=True,car={'id':7},track={'id':8},**changes)
        slow=lap('slow',102);fast=lap('fast',100);unclean=lap('offtrack',90,offtrack=True)
        with patch.object(client,'get',side_effect=[cars,tracks,{'items':[slow,unclean,fast],'total':3}]):
            laps,info=client.candidates(PROFILE)
        self.assertEqual([x['id'] for x in laps],['fast','slow'])
        self.assertTrue(info['complete'])


if __name__=='__main__':unittest.main()
