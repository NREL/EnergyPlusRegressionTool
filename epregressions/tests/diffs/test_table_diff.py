import os
import tempfile
import unittest

from epregressions.diffs.table_diff import table_diff
from epregressions.diffs.thresh_dict import ThreshDict


class TestMathDiff(unittest.TestCase):

    def setUp(self):
        self.cur_dir_path = os.path.dirname(os.path.realpath(__file__))
        self.diff_files_dir = os.path.join(self.cur_dir_path, 'tbl_resources')
        self.temp_output_dir = tempfile.mkdtemp()
        self.thresh_dict = ThreshDict(os.path.join(self.diff_files_dir, 'test_table_diff.config'))

    def test_identical_files(self):
        response = table_diff(
            self.thresh_dict,
            os.path.join(self.diff_files_dir, 'eplustbl.htm'),
            os.path.join(self.diff_files_dir, 'eplustbl.htm'),
            os.path.join(self.temp_output_dir, 'abs_diff.htm'),
            os.path.join(self.temp_output_dir, 'rel_diff.htm'),
            os.path.join(self.temp_output_dir, 'math_diff.log'),
            os.path.join(self.temp_output_dir, 'summary.htm'),
        )
        self.assertEqual('', response[0])  # diff status
        self.assertEqual(135, response[1])  # count_of_tables
        self.assertEqual(0, response[2])  # big diffs
        self.assertEqual(0, response[3])  # small diffs
        self.assertEqual(13781, response[4])  # equals
        self.assertEqual(0, response[5])  # string diffs
        self.assertEqual(0, response[6])  # size errors
        self.assertEqual(0, response[7])  # in file 2 but not in file 1
        self.assertEqual(0, response[8])  # in file 1 but not in file 2
