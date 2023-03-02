import json
import os
import tempfile
import unittest

from energyplus_regressions.build_files_to_run import CsvFileEntry, FileListBuilder, FileListBuilderArgs


class TestCsvFileEntry(unittest.TestCase):

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


class TestFileListBuilder(unittest.TestCase):

    def setUp(self):
        self.cur_dir_path = os.path.dirname(os.path.realpath(__file__))
        self.something_dir = os.path.join(self.cur_dir_path, 'resources')
        self.temp_idf_dir = tempfile.mkdtemp()
        self.temp_csv_file = tempfile.mkstemp(suffix='.csv')[1]

    def test_just_build_all_in_master_file(self):
        with open(self.temp_csv_file, 'w') as f:
            f.write('filename,weather,ext-int\n')
            f.write('NewIDFFile0,weather,\n')
            f.write('NewIDFFile1,weather,\n')
            f.write('NewIDFFile2,weather,\n')
            f.write('NewIDFFile3,weather,\n')
        args = FileListBuilderArgs()
        args.all = True
        args.master_data_file = self.temp_csv_file
        f = FileListBuilder(args)
        return_val = f.build_verified_list()
        success, selected_files, eliminated_files, files_in_dir_found_not_listed_in_csv = return_val
        self.assertTrue(success)
        self.assertEqual(4, len(selected_files))
        self.assertEqual(0, len(eliminated_files))
        self.assertEqual(0, len(files_in_dir_found_not_listed_in_csv))

    def test_verify_all_files_found(self):
        with open(self.temp_csv_file, 'w') as f:
            f.write('filename,weather,ext-int\n')
            f.write('NewIDFFile0,weather,\n')
            f.write('NewIDFFile1,weather,\n')
            f.write('NewIDFFile2,weather,\n')
            f.write('NewIDFFile3,weather,\n')
        for i in range(4):
            file_name = 'NewIDFFile%s.idf' % i
            with open(os.path.join(self.temp_idf_dir, file_name), 'w') as f2:
                f2.write('HI')
        args = FileListBuilderArgs()
        args.all = True
        args.master_data_file = self.temp_csv_file
        args.verify = self.temp_idf_dir
        f = FileListBuilder(args)
        return_val = f.build_verified_list()
        success, selected_files, eliminated_files, files_in_dir_found_not_listed_in_csv = return_val
        self.assertTrue(success)
        self.assertEqual(4, len(selected_files))
        self.assertEqual(0, len(eliminated_files))
        self.assertEqual(0, len(files_in_dir_found_not_listed_in_csv))

    def test_verify_some_files_missing(self):
        with open(self.temp_csv_file, 'w') as f:
            f.write('filename,weather,ext-int\n')
            f.write('NewIDFFile0,weather,\n')
            f.write('NewIDFFile1,weather,\n')
            f.write('NewIDFFile2,weather,\n')
            f.write('NewIDFFile3,weather,\n')
        for i in range(2):
            file_name = 'NewIDFFile%s.idf' % i
            with open(os.path.join(self.temp_idf_dir, file_name), 'w') as f2:
                f2.write('HI')
        args = FileListBuilderArgs()
        args.all = True
        args.master_data_file = self.temp_csv_file
        args.verify = self.temp_idf_dir
        f = FileListBuilder(args)
        return_val = f.build_verified_list()
        success, selected_files, eliminated_files, files_in_dir_found_not_listed_in_csv = return_val
        self.assertTrue(success)
        self.assertEqual(2, len(selected_files))
        self.assertEqual(2, len(eliminated_files))
        self.assertEqual(0, len(files_in_dir_found_not_listed_in_csv))

    def test_verify_extra_files_found(self):
        with open(self.temp_csv_file, 'w') as f:
            f.write('filename,weather,ext-int\n')
            f.write('NewIDFFile0,weather,\n')
            f.write('NewIDFFile1,weather,\n')
        for i in range(4):
            file_name = 'NewIDFFile%s.idf' % i
            with open(os.path.join(self.temp_idf_dir, file_name), 'w') as f2:
                f2.write('HI')
        args = FileListBuilderArgs()
        args.all = True
        args.master_data_file = self.temp_csv_file
        args.verify = self.temp_idf_dir
        f = FileListBuilder(args)
        return_val = f.build_verified_list()
        success, selected_files, eliminated_files, files_in_dir_found_not_listed_in_csv = return_val
        self.assertTrue(success)
        self.assertEqual(2, len(selected_files))
        self.assertEqual(0, len(eliminated_files))
        self.assertEqual(2, len(files_in_dir_found_not_listed_in_csv))

    def test_bad_csv_file(self):
        with open(self.temp_csv_file, 'w') as f:
            f.write('filename\tweather\text-int\n')
            f.write('NewIDFFile0\tweather\t\n')
        args = FileListBuilderArgs()
        args.all = True
        args.master_data_file = self.temp_csv_file
        f = FileListBuilder(args)
        return_val = f.build_verified_list()
        success, selected_files, eliminated_files, files_in_dir_found_not_listed_in_csv = return_val
        self.assertFalse(success)

    def test_print_results_to_file(self):
        with open(self.temp_csv_file, 'w') as f:
            f.write('filename,weather,ext-int\n')
            f.write('NewIDFFile0,weather,\n')
            f.write('NewIDFFile1,,\n')
            f.write('NewIDFFile2,weather,\n')
        args = FileListBuilderArgs()
        args.all = True
        args.master_data_file = self.temp_csv_file
        args.gui = False
        args.output_file = tempfile.mkstemp(suffix='.json')[1]
        f = FileListBuilder(args)
        f.build_verified_list()
        f.print_file_list_to_file()
        with open(args.output_file) as f_out:
            obj = json.load(f_out)
            self.assertIn('files_to_run', obj)
            self.assertEqual(3, len(obj['files_to_run']))

    def test_down_selection(self):
        with open(self.temp_csv_file, 'w') as f:
            f.write('filename,weather,ext-int\n')
            f.write('NewIDFFile0,weather,\n')  # regular with weather
            f.write('NewIDFFile1,,\n')  # regular no weather
            f.write('_NewIDFFile2,weather,\n')  # underscore with weather
            f.write('_NewIDFFile3,,\n')  # underscore no weather
            f.write('NewIDFFile4,weather,Y\n')  # regular with ext-int
            f.write('NewIDFFile5,,Y\n')  # regular with ext-int no weather
            f.write('_NewIDFFile6,weather,Y\n')  # underscore with ext-int with weather
            f.write('_NewIDFFile7,,Y\n')  # underscore with ext-int no weather
            f.write('NewIDFFile8,weather,\n')  # one more regular just for fun
        args = FileListBuilderArgs()
        args.master_data_file = self.temp_csv_file

        # first pass, let's get every file
        args.all = True
        f = FileListBuilder(args)
        f.build_verified_list()
        self.assertEqual(9, len(f.down_select_idf_list()))

        # let's disable external interface
        args.all = False
        args.extinterface = False
        args.weatherless = True
        args.underscore = True
        f = FileListBuilder(args)
        f.build_verified_list()
        self.assertEqual(5, len(f.down_select_idf_list()))

        # let's disable weather-less
        args.all = False
        args.extinterface = True
        args.weatherless = False
        args.underscore = True
        f = FileListBuilder(args)
        f.build_verified_list()
        self.assertEqual(5, len(f.down_select_idf_list()))

        # let's disable underscore
        args.all = False
        args.extinterface = True
        args.weatherless = True
        args.underscore = False
        f = FileListBuilder(args)
        f.build_verified_list()
        self.assertEqual(5, len(f.down_select_idf_list()))

        # let's disable weather-less and underscores
        args.all = False
        args.extinterface = True
        args.weatherless = False
        args.underscore = False
        f = FileListBuilder(args)
        f.build_verified_list()
        self.assertEqual(3, len(f.down_select_idf_list()))

        # let's get a random list of 6
        args.all = True
        args.random = 6
        f = FileListBuilder(args)
        f.build_verified_list()
        self.assertEqual(6, len(f.down_select_idf_list()))

        # but if the random list is higher than the number of idfs, get all of them
        args.all = True
        args.random = 12
        f = FileListBuilder(args)
        f.build_verified_list()
        self.assertEqual(9, len(f.down_select_idf_list()))
