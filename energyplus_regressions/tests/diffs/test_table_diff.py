import os
import tempfile
import unittest

from energyplus_regressions.diffs.table_diff import table_diff
from energyplus_regressions.diffs.thresh_dict import ThreshDict


class TestTableDiff(unittest.TestCase):

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

    def test_weird_unicode_issue(self):
        # There is something about these particular table files that causes an ascii encoding issue
        # I did not take the time to trim these files down to minimal table outputs, so this also exercises
        #  table diff more heavily than the other tests here
        response = table_diff(
            self.thresh_dict,
            os.path.join(self.diff_files_dir, 'eplustbl_weird_unicode_base.htm'),
            os.path.join(self.diff_files_dir, 'eplustbl_weird_unicode_issue_mod.htm'),
            os.path.join(self.temp_output_dir, 'abs_diff.htm'),
            os.path.join(self.temp_output_dir, 'rel_diff.htm'),
            os.path.join(self.temp_output_dir, 'math_diff.log'),
            os.path.join(self.temp_output_dir, 'summary.htm'),
        )
        self.assertEqual('', response[0])  # diff status
        self.assertEqual(155, response[1])  # count_of_tables
        self.assertEqual(334, response[2])  # big diffs
        self.assertEqual(67, response[3])  # small diffs
        self.assertEqual(3763, response[4])  # equals
        self.assertEqual(21, response[5])  # string diffs
        self.assertEqual(0, response[6])  # size errors
        self.assertEqual(0, response[7])  # in file 2 but not in file 1
        self.assertEqual(0, response[8])  # in file 1 but not in file 2

    def test_unicode_but_not_utf8_encoded_table(self):
        # degree symbol issue
        response = table_diff(
            self.thresh_dict,
            os.path.join(self.diff_files_dir, 'eplustbl_weird_unicode_base.htm'),
            os.path.join(self.diff_files_dir, 'eplustbl_unicode_contents_but_not_utf8_encoded.htm'),
            os.path.join(self.temp_output_dir, 'abs_diff.htm'),
            os.path.join(self.temp_output_dir, 'rel_diff.htm'),
            os.path.join(self.temp_output_dir, 'math_diff.log'),
            os.path.join(self.temp_output_dir, 'summary.htm'),
        )
        self.assertEqual('', response[0])  # diff status
        self.assertEqual(155, response[1])  # count_of_tables
        self.assertEqual(334, response[2])  # big diffs
        self.assertEqual(67, response[3])  # small diffs
        self.assertEqual(3763, response[4])  # equals
        self.assertEqual(21, response[5])  # string diffs
        self.assertEqual(0, response[6])  # size errors
        self.assertEqual(0, response[7])  # in file 2 but not in file 1
        self.assertEqual(0, response[8])  # in file 1 but not in file 2

    def test_second_file_has_table_with_different_headings(self):
        # Basically, if a column heading changed, but no data changed, that column was
        # ignored, and therefore no diffs, so the column heading change doesn't get noticed.
        # In fact, if data changed in that ignored column, it got totally ignored.
        # If a diff is encountered in a different column, the diff calculations ended up hitting
        # a key error because that column was never added to diff_dict.

        # We have four files, each with one table, two data columns (FanEnergyIndex and "End Use"), and two rows of data
        # eplustbl_heading_change_base.htm -- This has a column heading of End Use Subcategory and FEI = 6.21
        # eplustbl_heading_change_mod_with_no_other_diffs.htm -- This only has the column name changed to 'End Use'
        # eplustbl_heading_change_mod_with_diff_in_that_column.htm -- This has 'End Use' and End Use value modified
        # eplustbl_heading_change_mod_with_diff_in_other_column.htm -- This has 'End Use' and FEI modified to 6.14

        # First the only-name-change instance
        # It should trigger a size change and a string diff
        # The two FEI values are the same, so there should be two equal values
        # The heading change should trigger one big diff, and each row (2) should trigger another, so 3 big diffs
        response = table_diff(
            self.thresh_dict,
            os.path.join(self.diff_files_dir, 'eplustbl_heading_change_base.htm'),
            os.path.join(self.diff_files_dir, 'eplustbl_heading_change_mod_with_no_other_diffs.htm'),
            os.path.join(self.temp_output_dir, 'abs_diff.htm'),
            os.path.join(self.temp_output_dir, 'rel_diff.htm'),
            os.path.join(self.temp_output_dir, 'math_diff.log'),
            os.path.join(self.temp_output_dir, 'summary.htm'),
        )
        self.assertEqual('', response[0])  # diff status
        self.assertEqual(1, response[1])  # count_of_tables
        self.assertEqual(3, response[2])  # big diffs
        self.assertEqual(0, response[3])  # small diffs
        self.assertEqual(2, response[4])  # equals
        self.assertEqual(1, response[5])  # string diffs
        self.assertEqual(1, response[6])  # size errors
        self.assertEqual(0, response[7])  # in file 2 but not in file 1
        self.assertEqual(0, response[8])  # in file 1 but not in file 2

        # For the case where a value in the changed column changes, it should be identical to the just column change
        # The value will be reported as a big diff because it can't do a comparison due to the heading change
        # So 3 big diffs still, along with the single size and single string diffs
        response = table_diff(
            self.thresh_dict,
            os.path.join(self.diff_files_dir, 'eplustbl_heading_change_base.htm'),
            os.path.join(self.diff_files_dir, 'eplustbl_heading_change_mod_with_diff_in_that_column.htm'),
            os.path.join(self.temp_output_dir, 'abs_diff.htm'),
            os.path.join(self.temp_output_dir, 'rel_diff.htm'),
            os.path.join(self.temp_output_dir, 'math_diff.log'),
            os.path.join(self.temp_output_dir, 'summary.htm'),
        )
        self.assertEqual('', response[0])  # diff status
        self.assertEqual(1, response[1])  # count_of_tables
        self.assertEqual(3, response[2])  # big diffs
        self.assertEqual(0, response[3])  # small diffs
        self.assertEqual(2, response[4])  # equals
        self.assertEqual(1, response[5])  # string diffs
        self.assertEqual(1, response[6])  # size errors
        self.assertEqual(0, response[7])  # in file 2 but not in file 1
        self.assertEqual(0, response[8])  # in file 1 but not in file 2

        # Finally the one that was actually causing the issue, where a diff occurred in a different column
        # We should have the string diff and size diff due to the heading change
        # We should have a big diff due to the heading change
        # We should have a big diff for the two values in the changed heading column that can't be compared
        # And we should have a big diff for the actual change in the other column
        # So 4 big diffs total, and none equals
        # Most importantly, it shouldn't crash.
        response = table_diff(
            self.thresh_dict,
            os.path.join(self.diff_files_dir, 'eplustbl_heading_change_base.htm'),
            os.path.join(self.diff_files_dir, 'eplustbl_heading_change_mod_with_diff_in_other_column.htm'),
            os.path.join(self.temp_output_dir, 'abs_diff.htm'),
            os.path.join(self.temp_output_dir, 'rel_diff.htm'),
            os.path.join(self.temp_output_dir, 'math_diff.log'),
            os.path.join(self.temp_output_dir, 'summary.htm'),
        )
        self.assertEqual('', response[0])  # diff status
        self.assertEqual(1, response[1])  # count_of_tables
        self.assertEqual(4, response[2])  # big diffs
        self.assertEqual(0, response[3])  # small diffs
        self.assertEqual(1, response[4])  # equals
        self.assertEqual(1, response[5])  # string diffs
        self.assertEqual(1, response[6])  # size errors
        self.assertEqual(0, response[7])  # in file 2 but not in file 1
        self.assertEqual(0, response[8])  # in file 1 but not in file 2

    def test_nbsp(self):
        # This table has a numeric difference.
        # It also has a row full of `<td>&nbsp;</td>` to separate between bulk
        # of table and the total row.
        # nbsp won't be decoded nicely by ascii, and it would throw an error:
        # ```
        # UnicodeEncodeError: 'ascii' codec can't encode character u'\xa0'
        # in position 0: ordinal not in range(128)
        # ```
        response = table_diff(
            self.thresh_dict,
            os.path.join(self.diff_files_dir, 'eplustbl_nbsp_base.htm'),
            os.path.join(self.diff_files_dir, 'eplustbl_nbsp_mod.htm'),
            os.path.join(self.temp_output_dir, 'abs_diff.htm'),
            os.path.join(self.temp_output_dir, 'rel_diff.htm'),
            os.path.join(self.temp_output_dir, 'math_diff.log'),
            os.path.join(self.temp_output_dir, 'summary.htm'),
        )
        self.assertEqual('', response[0])  # diff status
        self.assertEqual(1, response[1])  # count_of_tables
        self.assertEqual(8, response[2])  # big diffs
        self.assertEqual(0, response[3])  # small diffs
        self.assertEqual(72, response[4])  # equals
        self.assertEqual(0, response[5])  # string diffs
        self.assertEqual(0, response[6])  # size errors
        self.assertEqual(0, response[7])  # in file 2 but not in file 1
        self.assertEqual(0, response[8])  # in file 1 but not in file 2

    def test_ignore_version_diff(self):
        # This table has a version number difference
        response = table_diff(
            self.thresh_dict,
            os.path.join(self.diff_files_dir, 'eplustbl_versiondiff_base.htm'),
            os.path.join(self.diff_files_dir, 'eplustbl_versiondiff_mod.htm'),
            os.path.join(self.temp_output_dir, 'abs_diff.htm'),
            os.path.join(self.temp_output_dir, 'rel_diff.htm'),
            os.path.join(self.temp_output_dir, 'math_diff.log'),
            os.path.join(self.temp_output_dir, 'summary.htm'),
        )
        self.assertEqual('', response[0])  # diff status
        self.assertEqual(4, response[1])  # count_of_tables
        self.assertEqual(0, response[2])  # big diffs  # TODO This is zero
        self.assertEqual(0, response[3])  # small diffs
        self.assertEqual(18, response[4])  # equals
        self.assertEqual(0, response[5])  # string diffs
        self.assertEqual(0, response[6])  # size errors
        self.assertEqual(0, response[7])  # in file 2 but not in file 1
        self.assertEqual(0, response[8])  # in file 1 but not in file 2
