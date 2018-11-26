import os
import tempfile
import unittest

from epregressions.diffs.math_diff import math_diff
from epregressions.diffs.thresh_dict import ThreshDict


class TestMathDiff(unittest.TestCase):

    def setUp(self):
        self.cur_dir_path = os.path.dirname(os.path.realpath(__file__))
        self.diff_files_dir = os.path.join(self.cur_dir_path, 'resources')
        self.temp_output_dir = tempfile.mkdtemp()
        self.thresh_dict = ThreshDict(os.path.join(self.cur_dir_path, '..', '..', 'diffs', 'math_diff.config'))

    def test_identical_files(self):
        response = math_diff(
            self.thresh_dict,
            os.path.join(self.diff_files_dir, 'eplusout1.csv'),
            os.path.join(self.diff_files_dir, 'eplusout1.csv'),
            os.path.join(self.temp_output_dir, 'abs_diff.csv'),
            os.path.join(self.temp_output_dir, 'rel_diff.csv'),
            os.path.join(self.temp_output_dir, 'math_diff.log'),
            os.path.join(self.temp_output_dir, 'summary.csv'),
        )
        self.assertEqual('All Equal', response[0])  # diff status
        self.assertEqual(48, response[1])  # num records compared
        self.assertEqual(0, response[2])  # big diffs
        self.assertEqual(0, response[3])  # small diffs
