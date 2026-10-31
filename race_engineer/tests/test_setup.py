import unittest
from engineer.setup import assess, recommendation as car_recommendation, verdict


def recommendation(*args):
    return car_recommendation(*args,profile={'car':'Toyota GR86','car_path':'toyotagr86'})


def run(times,**changes):
    return [dict(lap_time=t,wetness=1,track_temp=30.,fuel=30.,abs=2,tc=1,**changes) for t in times]


class SetupTests(unittest.TestCase):
    def test_requires_consistent_multiple_laps(self):
        self.assertFalse(assess(run([130,131]))[0])
        self.assertFalse(assess(run([130,134,131]))[0])
        self.assertTrue(assess(run([130,130.2,130.1]))[0])

    def test_all_car_arb_advice_requires_observed_control(self):
        laps=run([130,130.1,130.2])
        self.assertIn('not proposed until',recommendation(laps,'Mid-corner understeer','Open / adjustable','Soft','1'))
        profile={'car':'Test car','car_path':'test','car_setup':{'Chassis.Front.ARBSetting':'P4'}}
        text=car_recommendation(laps,'Mid-corner understeer','Open / adjustable','Unknown','Unknown',profile)
        self.assertIn('one documented step softer',text)
        self.assertNotIn('1 → 2',text)
        self.assertIn('fixed or unknown',recommendation(laps,'Mid-corner understeer','Unknown / fixed','Soft','1'))

    def test_aids_are_conditional(self):
        text=recommendation(run([130,130.1,130.2]),'Exit wheelspin','Open / adjustable','Soft','1')
        self.assertIn('one documented step toward more assistance',text)
        self.assertIn('does not confirm',text)

    def test_comparison_requires_controlled_conditions(self):
        baseline=run([130,130.1,130.2]);test=run([129,129.1,129.2])
        self.assertIn('pending',verdict(baseline,test,False))
        self.assertIn('faster',verdict(baseline,test,True))
        test[0]['wetness']=3
        self.assertIn('wetness changed',verdict(baseline,test,True))

    def test_small_difference_inconclusive(self):
        self.assertIn('Inconclusive',verdict(run([130,130.1,130.2]),run([130.01,130.11,130.21]),True))


if __name__=='__main__':unittest.main()
