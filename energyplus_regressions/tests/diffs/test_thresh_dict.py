import tempfile
import unittest

from energyplus_regressions.diffs.thresh_dict import ThreshDict


class TestThreshDict(unittest.TestCase):

    def setUp(self):
        self.typical_thresholds = """#comment line
C, Timestep = 0.2, 100  # comments ok here
C, Hourly = 0.2, 100
C, Monthly = 1.0, 100
C, * = 0.25, 100
F, Timestep = 0.2, 100
F, Hourly = 0.2, 100
F, Monthly = 1.0, 100
F, * = 0.2, 100
W, * = 0.1, 0.005
J, Hourly = 360, 0.005
J, Daily = 8640, 0.005
J, Monthly = 250000, 0.005
hr, TIMESTAMP = 2.0, 0.1
hr, * = 0.5, 0.005
min, TIMESTAMP = 45.0, 0.1
min, * = 10, 0.1
min, * = 10, 0.1  # duplicated line
invalid line
"""

    def test_construction(self):
        thresh_file = tempfile.mkstemp(suffix='.config')[1]
        with open(thresh_file, 'w') as f_thresh:
            f_thresh.write(self.typical_thresholds)
        t = ThreshDict(thresh_file)
        self.assertEqual(16, len(t.thresholds))

    def test_lookup(self):
        thresh_file = tempfile.mkstemp(suffix='.config')[1]
        with open(thresh_file, 'w') as f_thresh:
            f_thresh.write(self.typical_thresholds)
        t = ThreshDict(thresh_file)

        # looking up thresholds for the date/time should return zero leniency
        self.assertTupleEqual((0.0, 0.0), t.lookup('Date/Time'))

        # make sure the values are similar to the above definition
        # TODO: The ThreshDict seems to want the aggregation in curly braces...I'll play along right now,
        #       but I don't think that mathdiff or tablediff are converting the E+ report headers to curly,
        #       in which case the aggregation is ignored

        # here is what I think mathdiff is passing, and seeing on the way back
        # they all get whatever is in the * aggregation level
        self.assertTupleEqual((0.25, 100.0), t.lookup('My Variable Name [C](Hourly)'))
        self.assertTupleEqual((0.25, 100.0), t.lookup('My Variable Name [C](Monthly)'))
        self.assertTupleEqual((0.25, 100.0), t.lookup('My Variable Name [C](Annual)'))

        # here is what I think threshdict is expecting to get, and will give the right values back
        self.assertTupleEqual((0.2, 100.0), t.lookup('My Variable Name [C]{Hourly}'))
        self.assertTupleEqual((1.0, 100.0), t.lookup('My Variable Name [C]{Monthly}'))
        self.assertTupleEqual((0.25, 100.0), t.lookup('My Variable Name [C]{Annual}'))

        # check some other variations using this assumed curly brace form
        self.assertTupleEqual((0.0, 0.0), t.lookup('My Variable Name {Hourly}'))
        self.assertTupleEqual((8640, 0.005), t.lookup('My Variable Name [J]{Daily}'))

        # check some that don't exist in the list - first call it, and it will use the natural default
        self.assertTupleEqual((0.0, 0.0), t.lookup('My Variable Name [Q]{Daily}'))
        # then add a global default to the list of thresholds and retry - it will use the user-defined default
        t.thresholds['*|*'] = (2, 2)
        self.assertTupleEqual((2, 2), t.lookup('My Variable Name [Q]{Daily}'))

        # check an invalid line
        # self.assertTupleEqual((0.0, 0.0), t.lookup('My Variable Name ][{Daily}'))
