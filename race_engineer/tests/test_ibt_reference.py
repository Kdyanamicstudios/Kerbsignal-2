import unittest,tempfile,struct,math
from pathlib import Path
from engineer.ibt_reference import import_ibt,REQUIRED
from engineer.demo import frame
from engineer.core import Coach,Sample
import yaml

def native_file(path,invalid=False,wrong_bounds=False):
 names=sorted(REQUIRED|{'PlayerCarMyIncidentCount','WeatherDeclaredWet','TrackWetness','dcABS','dcTractionControl','Lat','Lon'})
 floats={'SessionTime':5,'LapDistPct':4,'Speed':4,'Brake':4,'Throttle':4,'SteeringWheelAngle':4,'Lat':5,'Lon':5}
 booleans={'OnPitRoad','IsOnTrack','WeatherDeclaredWet'}
 formats={name:'d' if floats.get(name)==5 else 'f' if name in floats else '?' if name in booleans else 'i' for name in names}
 schema={};stride=0
 for name in names:schema[name]=(formats[name],stride);stride+=struct.calcsize('<'+formats[name])
 meta=dict(WeekendInfo=dict(TrackDisplayName='Test track',TrackName='testtrack',TrackConfigName='Full',TrackID=101,TrackLength='5 km'),DriverInfo=dict(Drivers=[dict(CarIdx=0,CarScreenName='Test car',CarPath='testcar',CarID=17)]),SessionInfo=dict(Sessions=[dict(SessionNum=0,SessionType='Practice')]))
 info=yaml.safe_dump(meta).encode()+b'\0';voff=144;soff=voff+144*len(names);offset=soff+len(info);records=8001
 raw=bytearray(offset+records*stride);struct.pack_into('<12i',raw,0,2,0,20,1,len(info),soff,len(names),voff,1,stride,0,0);struct.pack_into('<ii',raw,48,0,offset)
 struct.pack_into('<Qddii',raw,112,0,0,400,3,records+(100 if wrong_bounds else 0));raw[soff:offset]=info
 for n,name in enumerate(names):
  fmt,pos=schema[name];typ=5 if fmt=='d' else 4 if fmt=='f' else 1 if fmt=='?' else 2
  struct.pack_into('<iii',raw,voff+n*144,typ,pos,1);raw[voff+n*144+16:voff+n*144+16+len(name)]=name.encode()
 for i in range(records):
  d=frame(i/20);d.update(PlayerCarIdx=0,SessionNum=0,dcABS=2,dcTractionControl=3)
  if invalid:d['PlayerCarMyIncidentCount']=i//10
  for name,(fmt,pos) in schema.items():struct.pack_into('<'+fmt,raw,offset+i*stride+pos,d.get(name,0))
 path.write_bytes(raw)

class IBTTests(unittest.TestCase):
 def test_complete_clean_lap_keeps_recorded_timing_and_identity(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'run.ibt';native_file(p);result=import_ibt(p)
   self.assertAlmostEqual(result['lap_time'],130,places=2);self.assertEqual(result['profile']['track_id'],'101');self.assertEqual(result['profile']['car_id'],'17');self.assertFalse(result['provenance']['derived_time'])
   c=Coach();c.import_reference(result,result['profile'],result['context']);self.assertTrue(c.reference)
 def test_wrong_layout_is_rejected(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'run.ibt';native_file(p)
   with self.assertRaisesRegex(ValueError,'does not match'):import_ibt(p,dict(car_path='testcar',car_id=17,track_id=999,config='Full',length=5000))
 def test_incident_laps_not_promoted(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'run.ibt';native_file(p,invalid=True)
   with self.assertRaisesRegex(ValueError,'no complete validated clean lap'):import_ibt(p)
 def test_truncated_record_bounds_rejected(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'run.ibt';native_file(p,wrong_bounds=True)
   with self.assertRaisesRegex(ValueError,'record bounds'):import_ibt(p)
 def test_failed_reference_import_keeps_previous_reference(self):
  c=Coach();c.reference=['existing']
  payload=dict(format='race-engineer-reference-v1',profile=dict(car_path='a',car_id=1,track_id=1,config='Full',length=1000),lap_time=float('nan'),context=[None]*4,samples=[dict(t=i*.1,p=i/100,speed=100,brake=0,throttle=1,steer=0) for i in range(101)])
  with self.assertRaises(ValueError):c.import_reference(payload,payload['profile'])
  self.assertEqual(c.reference,['existing'])
