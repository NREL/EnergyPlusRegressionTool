from datetime import datetime
import os
import tempfile
import unittest

from epregressions.main_window import RegressionGUI, ResultsTreeRoots, KnownBuildTypes
from epregressions.structures import ForceRunType, ReportingFreq, CompletedStructure
from epregressions.runtests import TestCaseCompleted


class TestResultsTreeRoots(unittest.TestCase):

    def test_length(self):
        # If the length of this changes, the UI must be updated also
        tree_roots = ResultsTreeRoots.list_all()
        self.assertEqual(11, len(tree_roots))


class TestRegressionGUI(unittest.TestCase):

    def setUp(self):
        self.gui = RegressionGUI()
        self.gui.show()

    def tearDown(self):
        self.gui.destroy()

    def test_title_is_initialized(self):
        self.assertEqual("EnergyPlus Regressions", self.gui.get_title())

    def test_gui_fills_with_data(self):
        # don't worry about the exact state of the UI, just make sure it responds to each enum
        values = []
        self.gui.force_run_type = ForceRunType.NONE
        self.gui.gui_fill_with_data()
        values.append(self.gui.run_type_combo_box.get_active())
        self.gui.force_run_type = ForceRunType.DD
        self.gui.gui_fill_with_data()
        values.append(self.gui.run_type_combo_box.get_active())
        self.gui.force_run_type = ForceRunType.ANNUAL
        self.gui.gui_fill_with_data()
        values.append(self.gui.run_type_combo_box.get_active())
        # the list length should be the same when made unique
        self.assertEqual(len(values), len(set(values)))
        # do the same for the reporting frequency
        values = []
        self.gui.report_frequency = ReportingFreq.DETAILED
        self.gui.gui_fill_with_data()
        values.append(self.gui.report_frequency_combo_box.get_active())
        self.gui.report_frequency = ReportingFreq.TIME_STEP
        self.gui.gui_fill_with_data()
        values.append(self.gui.report_frequency_combo_box.get_active())
        self.gui.report_frequency = ReportingFreq.HOURLY
        self.gui.gui_fill_with_data()
        values.append(self.gui.report_frequency_combo_box.get_active())
        self.gui.report_frequency = ReportingFreq.DAILY
        self.gui.gui_fill_with_data()
        values.append(self.gui.report_frequency_combo_box.get_active())
        self.gui.report_frequency = ReportingFreq.MONTHLY
        self.gui.gui_fill_with_data()
        values.append(self.gui.report_frequency_combo_box.get_active())
        self.gui.report_frequency = ReportingFreq.RUN_PERIOD
        self.gui.gui_fill_with_data()
        values.append(self.gui.report_frequency_combo_box.get_active())
        self.gui.report_frequency = ReportingFreq.ENVIRONMENT
        self.gui.gui_fill_with_data()
        values.append(self.gui.report_frequency_combo_box.get_active())
        self.gui.report_frequency = ReportingFreq.ANNUAL
        self.gui.gui_fill_with_data()
        values.append(self.gui.report_frequency_combo_box.get_active())
        # the list length should be the same when made unique
        self.assertEqual(len(values), len(set(values)))

    def test_open_file_browser(self):
        # just make sure it doesn't raise an exception
        p = self.gui.open_file_browser_to_directory(os.environ['HOME'])
        p.terminate()
        p.wait()

    def test_save_log_worker(self):
        i = datetime.now()
        good_path = os.path.join(tempfile.gettempdir(), 'tmpfile.log' + i.strftime('_%Y%m%d_%H%M%S'))
        self.assertFalse(os.path.exists(good_path))
        self.gui.save_log_worker(good_path)
        self.assertTrue(os.path.exists(good_path))

    def test_select_idfs(self):
        self.gui.idf_list_store.clear()
        self.gui.idf_list_store.append([False, 'filename1', 'weather1'])
        self.gui.idf_list_store.append([False, 'filename2', 'weather2'])
        self.gui.idf_list_store.append([False, 'filename3', 'weather3'])
        self.gui.idf_list_store.append([False, 'filename4', 'weather4'])
        self.gui.idf_list_store.append([False, 'filename5', 'weather5'])
        self.gui.idf_selection_all(None, False)
        self.assertEqual(0, self.gui.update_status_with_num_selected())
        self.gui.idf_selection_from_list_worker(['filename1', 'filename2'])
        self.assertEqual(2, self.gui.update_status_with_num_selected())
        self.gui.idf_selection_all(None, True)
        self.assertEqual(5, self.gui.update_status_with_num_selected())
        self.gui.idf_selection_all(None, False)
        self.gui.file_list_num_files.set_value(3)
        self.gui.idf_selection_random(None)
        self.assertEqual(3, self.gui.update_status_with_num_selected())
        self.gui.file_list_num_files.set_value(20)
        self.gui.idf_selection_random(None)
        self.assertEqual(5, self.gui.update_status_with_num_selected())

    def test_restore_file_selection(self):
        self.gui.idf_selection_all(None, False)
        self.assertEqual(0, self.gui.update_status_with_num_selected())
        self.gui.restore_file_selection(['1ZoneEvapCooler.idf'])
        self.assertEqual(1, self.gui.update_status_with_num_selected())

    def test_clearing_log_works(self):
        self.gui.clear_log(None)
        self.assertEqual(0, len(self.gui.log_store))

    def test_log_entry_limit(self):
        for i in range(5005):
            self.gui.add_log_entry('message')
        self.assertEqual(5000, len(self.gui.log_store))

    def test_build_initialization(self):
        self.gui.case_1_dir = tempfile.gettempdir()
        self.gui.case_1_run = True
        self.gui.case_1_type = KnownBuildTypes.Makefile
        with self.assertRaises(Exception):  # this should raise because there isn't a cache file there
            self.gui.create_build_instances(1)
        self.gui.case_1_type = KnownBuildTypes.VisualStudio
        with self.assertRaises(Exception):  # this should raise because there isn't a cache file there
            self.gui.create_build_instances(1)
        self.gui.case_1_type = KnownBuildTypes.Installation
        self.gui.create_build_instances(1)  # install versions don't require anything, so this should pass

        self.gui.case_2_dir = tempfile.gettempdir()
        self.gui.case_2_run = True
        self.gui.case_2_type = KnownBuildTypes.Installation
        self.gui.create_build_instances(2)  # and it should pass on case 2 also

        with self.assertRaises(Exception):  # this should raise because we don't have a third case
            self.gui.create_build_instances(3)
        with self.assertRaises(Exception):  # this should raise because of a bad case type
            self.gui.case_1_type = 'Hey, what?'
            self.gui.create_build_instances(1)

    def test_callback_handlers(self):
        # should add a message to the log
        prev_log_length = len(self.gui.log_store)
        self.gui.print_callback_handler('MyMessage')
        self.assertEqual(prev_log_length + 1, len(self.gui.log_store))

        # should prepare the progress bar length appropriately
        self.gui.sim_starting_callback_handler(number_of_builds=2, number_of_cases_per_build=9)
        self.assertEqual(self.gui.progress_maximum_value, 27)

        # mimic run button function
        self.gui.test_suite_is_running = True

        # should increment progress when a case is completed
        prev_progress = self.gui.current_progress_value
        tc = TestCaseCompleted('/run/', 'case_name', True, False, 'thread-1')
        self.gui.case_completed_callback_handler(tc)
        self.assertEqual(prev_progress + 1, self.gui.current_progress_value)

        # can also handle failure cases
        prev_progress = self.gui.current_progress_value
        tc = TestCaseCompleted('/run/', 'case_name', False, False, 'thread-1')
        self.gui.case_completed_callback_handler(tc)
        self.assertEqual(prev_progress + 1, self.gui.current_progress_value)

        # nothing to really check here, just make sure it passes
        self.gui.simulations_complete_callback_handler()

        # should again increment progress when a diff is completed for a case
        prev_progress = self.gui.current_progress_value
        self.gui.diff_completed_callback_handler('case_name')
        self.assertEqual(prev_progress + 1, self.gui.current_progress_value)

        # if the sim is cancelled, just make sure the flag is tidied up
        self.gui.cancel_callback_handler()
        self.assertFalse(self.gui.test_suite_is_running)

        # if it completes successfully, then we
        cs = CompletedStructure('/a/src', '/a/build', '/b/src', '/b/build', '/results')
        self.gui.all_done_callback_handler(cs)
