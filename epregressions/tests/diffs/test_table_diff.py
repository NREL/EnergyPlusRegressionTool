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
        self.assertEqual(3, response[1])  # count_of_tables
        self.assertEqual(0, response[2])  # big diffs
        self.assertEqual(0, response[3])  # small diffs
        self.assertEqual(17, response[4])  # equals
        self.assertEqual(0, response[5])  # string diffs
        self.assertEqual(0, response[6])  # size errors
        self.assertEqual(0, response[7])  # in file 2 but not in file 1
        self.assertEqual(0, response[8])  # in file 1 but not in file 2

    def test_invalid_file_1(self):
        response = table_diff(
            self.thresh_dict,
            os.path.join(self.diff_files_dir, 'eplustbl-DOESNOTEXIST.htm'),
            os.path.join(self.diff_files_dir, 'eplustbl.htm'),
            os.path.join(self.temp_output_dir, 'abs_diff.htm'),
            os.path.join(self.temp_output_dir, 'rel_diff.htm'),
            os.path.join(self.temp_output_dir, 'math_diff.log'),
            os.path.join(self.temp_output_dir, 'summary.htm'),
        )
        self.assertIn('unable to open file', response[0])  # diff status
        self.assertEqual(0, response[1])  # count_of_tables
        self.assertEqual(0, response[2])  # big diffs
        self.assertEqual(0, response[3])  # small diffs
        self.assertEqual(0, response[4])  # equals
        self.assertEqual(0, response[5])  # string diffs
        self.assertEqual(0, response[6])  # size errors
        self.assertEqual(0, response[7])  # in file 2 but not in file 1
        self.assertEqual(0, response[8])  # in file 1 but not in file 2

    def test_invalid_file_2(self):
        response = table_diff(
            self.thresh_dict,
            os.path.join(self.diff_files_dir, 'eplustbl.htm'),
            os.path.join(self.diff_files_dir, 'eplustbl-DOESNOTEXIST.htm'),
            os.path.join(self.temp_output_dir, 'abs_diff.htm'),
            os.path.join(self.temp_output_dir, 'rel_diff.htm'),
            os.path.join(self.temp_output_dir, 'math_diff.log'),
            os.path.join(self.temp_output_dir, 'summary.htm'),
        )
        self.assertIn('unable to open file', response[0])  # diff status
        self.assertEqual(0, response[1])  # count_of_tables
        self.assertEqual(0, response[2])  # big diffs
        self.assertEqual(0, response[3])  # small diffs
        self.assertEqual(0, response[4])  # equals
        self.assertEqual(0, response[5])  # string diffs
        self.assertEqual(0, response[6])  # size errors
        self.assertEqual(0, response[7])  # in file 2 but not in file 1
        self.assertEqual(0, response[8])  # in file 1 but not in file 2

    def test_second_file_missing_a_table(self):
        response = table_diff(
            self.thresh_dict,
            os.path.join(self.diff_files_dir, 'eplustbl.htm'),
            os.path.join(self.diff_files_dir, 'eplustbl_missing_a_table.htm'),
            os.path.join(self.temp_output_dir, 'abs_diff.htm'),
            os.path.join(self.temp_output_dir, 'rel_diff.htm'),
            os.path.join(self.temp_output_dir, 'math_diff.log'),
            os.path.join(self.temp_output_dir, 'summary.htm'),
        )
        self.assertEqual('', response[0])  # diff status
        self.assertEqual(3, response[1])  # count_of_tables
        self.assertEqual(0, response[2])  # big diffs
        self.assertEqual(0, response[3])  # small diffs
        self.assertEqual(14, response[4])  # equals
        self.assertEqual(0, response[5])  # string diffs
        self.assertEqual(0, response[6])  # size errors
        self.assertEqual(0, response[7])  # in file 2 but not in file 1
        self.assertEqual(1, response[8])  # in file 1 but not in file 2

    def test_second_file_has_extra_table(self):
        response = table_diff(
            self.thresh_dict,
            os.path.join(self.diff_files_dir, 'eplustbl.htm'),
            os.path.join(self.diff_files_dir, 'eplustbl_extra_table.htm'),
            os.path.join(self.temp_output_dir, 'abs_diff.htm'),
            os.path.join(self.temp_output_dir, 'rel_diff.htm'),
            os.path.join(self.temp_output_dir, 'math_diff.log'),
            os.path.join(self.temp_output_dir, 'summary.htm'),
        )
        self.assertEqual('', response[0])  # diff status
        self.assertEqual(4, response[1])  # count_of_tables
        self.assertEqual(0, response[2])  # big diffs
        self.assertEqual(0, response[3])  # small diffs
        self.assertEqual(17, response[4])  # equals
        self.assertEqual(0, response[5])  # string diffs
        self.assertEqual(0, response[6])  # size errors
        self.assertEqual(1, response[7])  # in file 2 but not in file 1
        self.assertEqual(0, response[8])  # in file 1 but not in file 2

    def test_second_file_has_table_with_different_size(self):
        response = table_diff(
            self.thresh_dict,
            os.path.join(self.diff_files_dir, 'eplustbl.htm'),
            os.path.join(self.diff_files_dir, 'eplustbl_table_with_different_length.htm'),
            os.path.join(self.temp_output_dir, 'abs_diff.htm'),
            os.path.join(self.temp_output_dir, 'rel_diff.htm'),
            os.path.join(self.temp_output_dir, 'math_diff.log'),
            os.path.join(self.temp_output_dir, 'summary.htm'),
        )
        self.assertEqual('', response[0])  # diff status
        self.assertEqual(3, response[1])  # count_of_tables
        self.assertEqual(0, response[2])  # big diffs
        self.assertEqual(0, response[3])  # small diffs
        self.assertEqual(14, response[4])  # equals
        self.assertEqual(0, response[5])  # string diffs
        self.assertEqual(1, response[6])  # size errors
        self.assertEqual(0, response[7])  # in file 2 but not in file 1
        self.assertEqual(0, response[8])  # in file 1 but not in file 2

    def test_big_numeric_diff(self):
        response = table_diff(
            self.thresh_dict,
            os.path.join(self.diff_files_dir, 'eplustbl.htm'),
            os.path.join(self.diff_files_dir, 'eplustbl_has_big_numeric_diff.htm'),
            os.path.join(self.temp_output_dir, 'abs_diff.htm'),
            os.path.join(self.temp_output_dir, 'rel_diff.htm'),
            os.path.join(self.temp_output_dir, 'math_diff.log'),
            os.path.join(self.temp_output_dir, 'summary.htm'),
        )
        self.assertEqual('', response[0])  # diff status
        self.assertEqual(3, response[1])  # count_of_tables
        self.assertEqual(1, response[2])  # big diffs
        self.assertEqual(0, response[3])  # small diffs
        self.assertEqual(16, response[4])  # equals
        self.assertEqual(0, response[5])  # string diffs
        self.assertEqual(0, response[6])  # size errors
        self.assertEqual(0, response[7])  # in file 2 but not in file 1
        self.assertEqual(0, response[8])  # in file 1 but not in file 2

    def test_small_numeric_diff(self):
        response = table_diff(
            self.thresh_dict,
            os.path.join(self.diff_files_dir, 'eplustbl.htm'),
            os.path.join(self.diff_files_dir, 'eplustbl_has_small_numeric_diff.htm'),
            os.path.join(self.temp_output_dir, 'abs_diff.htm'),
            os.path.join(self.temp_output_dir, 'rel_diff.htm'),
            os.path.join(self.temp_output_dir, 'math_diff.log'),
            os.path.join(self.temp_output_dir, 'summary.htm'),
        )
        self.assertEqual('', response[0])  # diff status
        self.assertEqual(3, response[1])  # count_of_tables
        self.assertEqual(0, response[2])  # big diffs
        self.assertEqual(1, response[3])  # small diffs
        self.assertEqual(16, response[4])  # equals
        self.assertEqual(0, response[5])  # string diffs
        self.assertEqual(0, response[6])  # size errors
        self.assertEqual(0, response[7])  # in file 2 but not in file 1
        self.assertEqual(0, response[8])  # in file 1 but not in file 2

    def test_string_diff(self):
        response = table_diff(
            self.thresh_dict,
            os.path.join(self.diff_files_dir, 'eplustbl_has_string_diff_base.htm'),
            os.path.join(self.diff_files_dir, 'eplustbl_has_string_diff_mod.htm'),
            os.path.join(self.temp_output_dir, 'abs_diff.htm'),
            os.path.join(self.temp_output_dir, 'rel_diff.htm'),
            os.path.join(self.temp_output_dir, 'math_diff.log'),
            os.path.join(self.temp_output_dir, 'summary.htm'),
        )
        self.assertEqual('', response[0])  # diff status
        self.assertEqual(3, response[1])  # count_of_tables
        self.assertEqual(0, response[2])  # big diffs
        self.assertEqual(0, response[3])  # small diffs
        self.assertEqual(16, response[4])  # equals
        self.assertEqual(1, response[5])  # string diffs
        self.assertEqual(0, response[6])  # size errors
        self.assertEqual(0, response[7])  # in file 2 but not in file 1
        self.assertEqual(0, response[8])  # in file 1 but not in file 2

    def test_second_file_has_table_with_different_headings(self):
        response = table_diff(
            self.thresh_dict,
            os.path.join(self.diff_files_dir, 'eplustbl.htm'),
            os.path.join(self.diff_files_dir, 'eplustbl_table_has_different_heading.htm'),
            os.path.join(self.temp_output_dir, 'abs_diff.htm'),
            os.path.join(self.temp_output_dir, 'rel_diff.htm'),
            os.path.join(self.temp_output_dir, 'math_diff.log'),
            os.path.join(self.temp_output_dir, 'summary.htm'),
        )
        self.assertEqual('', response[0])  # diff status
        self.assertEqual(3, response[1])  # count_of_tables
        self.assertEqual(0, response[2])  # big diffs
        self.assertEqual(0, response[3])  # small diffs
        self.assertEqual(13, response[4])  # equals
        self.assertEqual(0, response[5])  # string diffs
        self.assertEqual(0, response[6])  # size errors
        self.assertEqual(0, response[7])  # in file 2 but not in file 1
        self.assertEqual(0, response[8])  # in file 1 but not in file 2

    def test_malformed_table_heading_in_file_1(self):
        response = table_diff(
            self.thresh_dict,
            os.path.join(self.diff_files_dir, 'eplustbl_missing_table_header_comment.htm'),
            os.path.join(self.diff_files_dir, 'eplustbl.htm'),
            os.path.join(self.temp_output_dir, 'abs_diff.htm'),
            os.path.join(self.temp_output_dir, 'rel_diff.htm'),
            os.path.join(self.temp_output_dir, 'math_diff.log'),
            os.path.join(self.temp_output_dir, 'summary.htm'),
        )
        self.assertIn('malformed', response[0])  # diff status
        self.assertEqual(0, response[1])  # count_of_tables
        self.assertEqual(0, response[2])  # big diffs
        self.assertEqual(0, response[3])  # small diffs
        self.assertEqual(0, response[4])  # equals
        self.assertEqual(0, response[5])  # string diffs
        self.assertEqual(0, response[6])  # size errors
        self.assertEqual(0, response[7])  # in file 2 but not in file 1
        self.assertEqual(0, response[8])  # in file 1 but not in file 2

    def test_malformed_table_heading_in_file_2(self):
        response = table_diff(
            self.thresh_dict,
            os.path.join(self.diff_files_dir, 'eplustbl.htm'),
            os.path.join(self.diff_files_dir, 'eplustbl_missing_table_header_comment.htm'),
            os.path.join(self.temp_output_dir, 'abs_diff.htm'),
            os.path.join(self.temp_output_dir, 'rel_diff.htm'),
            os.path.join(self.temp_output_dir, 'math_diff.log'),
            os.path.join(self.temp_output_dir, 'summary.htm'),
        )
        self.assertIn('malformed', response[0])  # diff status
        self.assertEqual(0, response[1])  # count_of_tables
        self.assertEqual(0, response[2])  # big diffs
        self.assertEqual(0, response[3])  # small diffs
        self.assertEqual(0, response[4])  # equals
        self.assertEqual(0, response[5])  # string diffs
        self.assertEqual(0, response[6])  # size errors
        self.assertEqual(0, response[7])  # in file 2 but not in file 1
        self.assertEqual(0, response[8])  # in file 1 but not in file 2

    def test_empty_cell(self):
        response = table_diff(
            self.thresh_dict,
            os.path.join(self.diff_files_dir, 'eplustbl.htm'),
            os.path.join(self.diff_files_dir, 'eplustbl_empty_cell.htm'),
            os.path.join(self.temp_output_dir, 'abs_diff.htm'),
            os.path.join(self.temp_output_dir, 'rel_diff.htm'),
            os.path.join(self.temp_output_dir, 'math_diff.log'),
            os.path.join(self.temp_output_dir, 'summary.htm'),
        )
        self.assertEqual('', response[0])  # diff status
        self.assertEqual(3, response[1])  # count_of_tables
        self.assertEqual(0, response[2])  # big diffs
        self.assertEqual(0, response[3])  # small diffs
        self.assertEqual(16, response[4])  # equals
        self.assertEqual(1, response[5])  # string diffs
        self.assertEqual(0, response[6])  # size errors
        self.assertEqual(0, response[7])  # in file 2 but not in file 1
        self.assertEqual(0, response[8])  # in file 1 but not in file 2
