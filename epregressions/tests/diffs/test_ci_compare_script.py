import glob
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import contextmanager

try:
    from cStringIO import StringIO  # Python 2, ensures that the overridden bytes-based-stdout is still bytes-based
except ImportError:
    from io import StringIO  # Python 3, will use unicode based overridden stdout

from epregressions.diffs.ci_compare_script import cleanup, get_diff_files, main_function, print_message, process_diffs
from epregressions.runtests import TestEntry
from epregressions.structures import MathDifferences


@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class TestCICompareScriptFunctions(unittest.TestCase):

    def setUp(self):
        self.cur_dir_path = os.path.dirname(os.path.realpath(__file__))
        self.csv_resource_dir = os.path.join(self.cur_dir_path, 'csv_resources')
        self.tbl_resource_dir = os.path.join(self.cur_dir_path, 'tbl_resources')
        self.temp_dir = tempfile.mkdtemp()
        self.temp_base_dir = tempfile.mkdtemp()
        self.temp_mod_dir = tempfile.mkdtemp()

    def test_get_diff_files(self):
        file_names = [
            'eplusout.rdd',
            'eplusout.rdd.diffs',
            'eplusout.csv',
            'eplusout.csv.absdiffs.csv'
        ]
        for file_name in file_names:
            full_path = os.path.join(self.temp_dir, file_name)
            with open(full_path, 'w'):
                pass  # just let it close the file
        self.assertEqual(2, len(get_diff_files(self.temp_dir)))

    def test_cleanup(self):
        file_names = [
            'eplusout.rdd',
            'eplusout.rdd.diffs',
            'eplusout.csv',
            'eplusout.csv.absdiffs.csv'
        ]
        for file_name in file_names:
            full_path = os.path.join(self.temp_dir, file_name)
            with open(full_path, 'w'):
                pass  # just let it close the file
        files_found = glob.glob(os.path.join(self.temp_dir, "*"))
        self.assertEqual(4, len(files_found))
        cleanup(self.temp_dir)
        files_found = glob.glob(os.path.join(self.temp_dir, "*"))
        self.assertEqual(2, len(files_found))

    def test_print_message(self):
        with captured_output() as (out, err):
            print_message("Hello world!")
        # This can go inside or outside the `with` block
        output = out.getvalue().strip()
        self.assertIn('decent_ci:test_result:message', output)
        self.assertIn('Hello', output)

    def test_process_diffs(self):
        # process diffs should never turn a True to a False!
        entry = TestEntry('MyFileName', 'MyWeather.epw')
        # try a blank entry
        initial_has_diffs = False
        initial_has_small_diffs = False
        new_diffs, new_small_diffs = process_diffs("ESO", entry.eso_diffs, initial_has_diffs, initial_has_small_diffs)
        self.assertFalse(new_diffs)
        self.assertFalse(new_small_diffs)
        # now add some only small diff to it
        entry.add_math_differences(MathDifferences(['Small Diffs', 2, 0, 4]), MathDifferences.ESO)
        with captured_output() as (out, err):
            new_diffs, new_small_diffs = process_diffs("ESO", entry.eso_diffs, new_diffs, new_small_diffs)
            self.assertFalse(new_diffs)
            self.assertTrue(new_small_diffs)
            self.assertIn('ESO small diffs', out.getvalue().strip())
        # now add some only big diff to it
        new_small_diffs = False
        new_diffs = False
        entry.add_math_differences(MathDifferences(['Big Diffs', 2, 3, 0]), MathDifferences.ESO)
        with captured_output() as (out, err):
            new_diffs, new_small_diffs = process_diffs("ESO", entry.eso_diffs, new_diffs, new_small_diffs)
            self.assertTrue(new_diffs)
            self.assertFalse(new_small_diffs)
            self.assertIn('ESO big diffs', out.getvalue().strip())
        # now go back to a blank one, any True values should still be True!
        entry.eso_diffs = None
        new_diffs, new_small_diffs = process_diffs("ESO", entry.eso_diffs, new_diffs, new_small_diffs)
        self.assertTrue(new_diffs)
        self.assertFalse(new_small_diffs)

    def test_main_function(self):
        shutil.copy(
            os.path.join(self.csv_resource_dir, 'eplusout.csv'),
            os.path.join(self.temp_base_dir, 'eplusout.csv')
        )
        shutil.copy(
            os.path.join(self.csv_resource_dir, 'eplusout_big_watt_diffs.csv'),
            os.path.join(self.temp_mod_dir, 'eplusout.csv')
        )
        with captured_output() as (out, err):
            # should fail if we don't have any .end files
            main_function(
                file_name='HVACTemplate-5ZoneFanCoil',
                base_dir=self.temp_base_dir,
                mod_dir=self.temp_mod_dir,
                base_sha='base123',
                mod_sha='mod456',
                make_public=True,
                device_id='some_device_id',
                test_mode=True
            )
            self.assertIn('Skipping', out.getvalue().strip())
        end_string = 'EnergyPlus Completed Successfully-- 0 Warning; 0 Severe Errors; Elapsed Time=00hr 00min  3.06sec'
        with open(os.path.join(self.temp_base_dir, 'eplusout.end'), 'w') as f1:
            f1.write(end_string)
        with open(os.path.join(self.temp_mod_dir, 'eplusout.end'), 'w') as f2:
            f2.write(end_string)
        with captured_output() as (out, err):
            # should fail if we don't have any .end files
            main_function(
                file_name='HVACTemplate-5ZoneFanCoil',
                base_dir=self.temp_base_dir,
                mod_dir=self.temp_mod_dir,
                base_sha='base123',
                mod_sha='mod456',
                make_public=True,
                device_id='some_device_id',
                test_mode=True
            )
            self.assertIn('ESO big diffs', out.getvalue().strip())
