import os
import tempfile
import unittest

from epregressions.build_files_to_run import CsvFileEntry


class TestCsvFileEntry(unittest.TestCase):

    def setUp(self):
        cur_dir_path = os.path.dirname(os.path.realpath(__file__))
        self.something_dir = os.path.join(cur_dir_path, 'resources')
        self.new_temp_dir = tempfile.mkdtemp()

    def test_construction_full_line(self):
        row_of_data = ['_filename', 'weather.epw', 'Y']
        c = CsvFileEntry(row_of_data)
        self.assertTrue(c.has_weather_file)
        self.assertTrue(c.external_interface)
        self.assertTrue(c.underscore)

    def test_construction_regular_file(self):
        row_of_data = ['filename', 'weather.epw', 'Y']
        c = CsvFileEntry(row_of_data)
        self.assertTrue(c.has_weather_file)
        self.assertTrue(c.external_interface)
        self.assertFalse(c.underscore)

    def test_construction_not_ext_int(self):
        row_of_data = ['_filename', 'weather.epw', '']
        c = CsvFileEntry(row_of_data)
        self.assertTrue(c.has_weather_file)
        self.assertFalse(c.external_interface)
        self.assertTrue(c.underscore)

    def test_construction_missing_weather(self):
        row_of_data = ['_filename', '', 'Y']
        c = CsvFileEntry(row_of_data)
        self.assertFalse(c.has_weather_file)
        self.assertTrue(c.external_interface)
        self.assertTrue(c.underscore)

    def test_requires_three_columns(self):
        row_of_data = ['_filename', '']
        with self.assertRaises(Exception):
            CsvFileEntry(row_of_data)
