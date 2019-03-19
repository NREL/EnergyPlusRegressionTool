import json
import os
import shutil
import tempfile
import unittest

from epregressions.builds.makefile import CMakeCacheMakeFileBuildDirectory
from epregressions.runtests import TestRunConfiguration, SuiteRunner
from epregressions.structures import (
    EndErrSummary, ForceRunType, ReportingFreq, TestEntry, TextDifferences
)


class TestTestSuiteRunner(unittest.TestCase):

    def setUp(self):
        self.cur_dir_path = os.path.dirname(os.path.realpath(__file__))
        self.resources = os.path.join(self.cur_dir_path, 'resources')
        self.temp_base_source_dir = tempfile.mkdtemp()
        self.temp_base_build_dir = tempfile.mkdtemp()
        self.temp_mod_source_dir = tempfile.mkdtemp()
        self.temp_mod_build_dir = tempfile.mkdtemp()
        self.temp_csv_file = tempfile.mkstemp(suffix='.csv')[1]

    def establish_build_folder(self, target_build_dir, target_source_dir, idf_config):
        with open(os.path.join(target_build_dir, 'CMakeCache.txt'), 'w') as f:
            f.write('HEY\n')
            f.write('CMAKE_HOME_DIRECTORY:INTERNAL=%s\n' % target_source_dir)
            f.write('HEY AGAIN\n')
        products_dir = os.path.join(target_build_dir, 'Products')
        os.makedirs(products_dir)
        read_vars_dir = os.path.join(target_source_dir, 'bin', 'EPMacro', 'Linux')
        os.makedirs(read_vars_dir)
        products_map = {
            os.path.join(self.resources, 'dummy.basement.idd'): os.path.join(products_dir, 'BasementGHT.idd'),
            os.path.join(self.resources, 'dummy.basement.py'): os.path.join(products_dir, 'Basement'),
            os.path.join(self.resources, 'dummy.Energy+.idd'): os.path.join(products_dir, 'Energy+.idd'),
            os.path.join(self.resources, 'dummy.energyplus.py'): os.path.join(products_dir, 'energyplus'),
            os.path.join(self.resources, 'dummy.expandobjects.py'): os.path.join(products_dir, 'ExpandObjects'),
            os.path.join(self.resources, 'dummy.parametric.py'): os.path.join(products_dir, 'ParametricPreprocessor'),
            os.path.join(self.resources, 'dummy.readvars.py'): os.path.join(products_dir, 'ReadVarsESO'),
            os.path.join(self.resources, 'dummy.slab.py'): os.path.join(products_dir, 'Slab'),
            os.path.join(self.resources, 'dummy.slab.idd'): os.path.join(products_dir, 'SlabGHT.idd'),
            os.path.join(self.resources, 'dummy.epmacro.py'): os.path.join(read_vars_dir, 'EPMacro'),
        }
        for source in products_map:
            shutil.copy(source, products_map[source])
        testfiles_dir = os.path.join(target_source_dir, 'testfiles')
        os.makedirs(testfiles_dir)
        json_text = json.dumps(idf_config)
        with open(os.path.join(testfiles_dir, 'my_file.idf'), 'w') as f:
            f.write(json_text)
        with open(os.path.join(testfiles_dir, 'my_file.rvi'), 'w') as f_rvi:
            f_rvi.write('RVI TEXT')
        with open(os.path.join(testfiles_dir, 'my_file.mvi'), 'w') as f_mvi:
            f_mvi.write('MVI TEXT')
        with open(os.path.join(testfiles_dir, 'HybridZoneModel_TemperatureData.csv'), 'w') as f_hybrid:
            f_hybrid.write('OK')
        with open(os.path.join(testfiles_dir, 'my_macro_file.imf'), 'w') as f_macro:
            f_macro.write(json_text)
        with open(os.path.join(testfiles_dir, 'extra.imf'), 'w') as f_macro_extra:
            f_macro_extra.write('##MACROTEXT')
        with open(os.path.join(testfiles_dir, 'EMSTestMathAndKill.idf'), 'w') as f_kill:
            f_kill.write(json_text)
        weather_dir = os.path.join(target_source_dir, 'weather')
        os.makedirs(weather_dir)
        shutil.copy(os.path.join(self.resources, 'dummy.in.epw'), os.path.join(weather_dir, 'my_weather.epw'))
        shutil.copy(
            os.path.join(self.resources, 'dummy.in.epw'),
            os.path.join(weather_dir, "USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw")
        )
        datasets_dir = os.path.join(target_source_dir, 'datasets')
        os.makedirs(datasets_dir)
        with open(os.path.join(datasets_dir, 'Window5DataFile.dat'), 'w') as f_window:
            f_window.write('HI')
        tdv_dir = os.path.join(datasets_dir, 'TDV')
        os.makedirs(tdv_dir)
        with open(os.path.join(tdv_dir, 'dummy.txt'), 'w') as f_tdv:
            f_tdv.write('HEY')
        # os.path.join(self.resource_dir, 'dummy.epmacro.py'): os.path.join(products_dir, 'Energy+.idd'),

    @staticmethod
    def dummy_callback(*args, **kwargs):
        pass

    def test_both_success_no_diffs_no_force(self):
        base = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_base_build_dir,
            self.temp_base_source_dir,
            {
                "config": {
                    "run_time_string": "01hr 20min  0.17sec",
                    "num_warnings": 1,
                    "num_severe": 0,
                    "end_state": "success",
                    "eso_results": "base",
                    "txt_results": "base"
                }
            }
        )
        base.set_build_directory(self.temp_base_build_dir)
        base.run = True

        mod = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_mod_build_dir,
            self.temp_mod_source_dir,
            {
                "config": {
                    "run_time_string": "00hr 10min  0.17sec",
                    "num_warnings": 2,
                    "num_severe": 1,
                    "end_state": "success",
                    "eso_results": "base",
                    "txt_results": "base"
                }
            }
        )
        mod.set_build_directory(self.temp_mod_build_dir)
        mod.run = True

        entries = [TestEntry('my_file', 'my_weather')]
        config = TestRunConfiguration(
            force_run_type=ForceRunType.NONE,
            single_test_run=False,
            num_threads=1,
            report_freq=ReportingFreq.HOURLY,
            build_a=base,
            build_b=mod
        )
        r = SuiteRunner(config, entries)
        r.add_callbacks(
            print_callback=TestTestSuiteRunner.dummy_callback,
            simstarting_callback=TestTestSuiteRunner.dummy_callback,
            casecompleted_callback=TestTestSuiteRunner.dummy_callback,
            simulationscomplete_callback=TestTestSuiteRunner.dummy_callback,
            diffcompleted_callback=TestTestSuiteRunner.dummy_callback,
            alldone_callback=TestTestSuiteRunner.dummy_callback,
            cancel_callback=TestTestSuiteRunner.dummy_callback
        )
        diff_results = r.run_test_suite()
        # there should be 1 file result
        self.assertEqual(1, len(diff_results.entries_by_file))
        results_for_file = diff_results.entries_by_file[0]
        # it should be named according to what we listed above
        self.assertEqual('my_file', results_for_file.basename)
        # it should have succeeded in both base and mod cases
        self.assertEqual(EndErrSummary.STATUS_SUCCESS, results_for_file.summary_result.simulation_status_case1)
        self.assertEqual(EndErrSummary.STATUS_SUCCESS, results_for_file.summary_result.simulation_status_case2)
        # it should have created a test directory and dropped the summaries there
        results_dir = diff_results.results_dir
        self.assertTrue(os.path.exists(os.path.join(results_dir, 'test_results.json')))
        self.assertTrue(os.path.exists(os.path.join(results_dir, 'run_times.csv')))
        # it should have created a run directory for this file, put input files there, and left output files there
        file_results_dir = os.path.join(results_dir, 'my_file')
        self.assertTrue(os.path.exists(file_results_dir))
        self.assertTrue(os.path.exists(os.path.join(file_results_dir, 'in.epw')))
        self.assertTrue(os.path.exists(os.path.join(file_results_dir, 'in.idf')))
        self.assertTrue(os.path.exists(os.path.join(file_results_dir, 'eplusout.eso')))
        self.assertTrue(os.path.exists(os.path.join(file_results_dir, 'eplusout.end')))
        self.assertTrue(os.path.exists(os.path.join(file_results_dir, 'eplusout.csv')))
        # check the diffs
        self.assertEqual('All Equal', results_for_file.eso_diffs.diff_type)
        self.assertEqual('All Equal', results_for_file.mtr_diffs.diff_type)
        self.assertEqual('All Equal', results_for_file.ssz_diffs.diff_type)
        self.assertEqual('All Equal', results_for_file.zsz_diffs.diff_type)
        self.assertEqual(TextDifferences.EQUAL, results_for_file.aud_diffs.diff_type)
        self.assertEqual(TextDifferences.EQUAL, results_for_file.bnd_diffs.diff_type)
        self.assertEqual(TextDifferences.EQUAL, results_for_file.dl_in_diffs.diff_type)
        self.assertEqual(TextDifferences.EQUAL, results_for_file.dl_out_diffs.diff_type)
        self.assertEqual(TextDifferences.EQUAL, results_for_file.dxf_diffs.diff_type)
        self.assertEqual(TextDifferences.EQUAL, results_for_file.eio_diffs.diff_type)
        self.assertEqual(TextDifferences.EQUAL, results_for_file.err_diffs.diff_type)
        self.assertEqual(TextDifferences.EQUAL, results_for_file.mdd_diffs.diff_type)
        self.assertEqual(TextDifferences.EQUAL, results_for_file.mtd_diffs.diff_type)
        self.assertEqual(TextDifferences.EQUAL, results_for_file.rdd_diffs.diff_type)
        self.assertEqual(TextDifferences.EQUAL, results_for_file.shd_diffs.diff_type)
        # TODO: Check TableDiff

    def test_case_a_fatal(self):
        base = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_base_build_dir,
            self.temp_base_source_dir,
            {
                "config": {
                    "run_time_string": "01hr 20min  0.17sec",
                    "num_warnings": 1,
                    "num_severe": 0,
                    "end_state": "fatal",
                    "eso_results": "base",
                    "txt_results": "base"
                }
            }
        )
        base.set_build_directory(self.temp_base_build_dir)
        base.run = True

        mod = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_mod_build_dir,
            self.temp_mod_source_dir,
            {
                "config": {
                    "run_time_string": "00hr 10min  0.17sec",
                    "num_warnings": 2,
                    "num_severe": 1,
                    "end_state": "success",
                    "eso_results": "base",
                    "txt_results": "base"
                }
            }
        )
        mod.set_build_directory(self.temp_mod_build_dir)
        mod.run = True

        entries = [TestEntry('my_file', 'my_weather')]
        config = TestRunConfiguration(
            force_run_type=ForceRunType.NONE,
            single_test_run=False,
            num_threads=1,
            report_freq=ReportingFreq.HOURLY,
            build_a=base,
            build_b=mod
        )
        r = SuiteRunner(config, entries)
        r.add_callbacks(
            print_callback=TestTestSuiteRunner.dummy_callback,
            simstarting_callback=TestTestSuiteRunner.dummy_callback,
            casecompleted_callback=TestTestSuiteRunner.dummy_callback,
            simulationscomplete_callback=TestTestSuiteRunner.dummy_callback,
            diffcompleted_callback=TestTestSuiteRunner.dummy_callback,
            alldone_callback=TestTestSuiteRunner.dummy_callback,
            cancel_callback=TestTestSuiteRunner.dummy_callback
        )
        diff_results = r.run_test_suite()
        # there should be 1 file result
        self.assertEqual(1, len(diff_results.entries_by_file))
        results_for_file = diff_results.entries_by_file[0]
        # it should be named according to what we listed above
        self.assertEqual('my_file', results_for_file.basename)
        # it should have succeeded in both base and mod cases
        self.assertEqual(EndErrSummary.STATUS_FATAL, results_for_file.summary_result.simulation_status_case1)
        self.assertEqual(EndErrSummary.STATUS_SUCCESS, results_for_file.summary_result.simulation_status_case2)

    def test_expect_death_succeeds(self):
        base = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_base_build_dir,
            self.temp_base_source_dir,
            {
                "config": {
                    "run_time_string": "01hr 20min  0.17sec",
                    "num_warnings": 1,
                    "num_severe": 0,
                    "end_state": "fatal",
                    "eso_results": "base",
                    "txt_results": "base"
                }
            }
        )
        base.set_build_directory(self.temp_base_build_dir)
        base.run = True

        mod = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_mod_build_dir,
            self.temp_mod_source_dir,
            {
                "config": {
                    "run_time_string": "00hr 10min  0.17sec",
                    "num_warnings": 2,
                    "num_severe": 1,
                    "end_state": "fatal",
                    "eso_results": "base",
                    "txt_results": "base"
                }
            }
        )
        mod.set_build_directory(self.temp_mod_build_dir)
        mod.run = True

        entries = [TestEntry('EMSTestMathAndKill', 'my_weather')]
        config = TestRunConfiguration(
            force_run_type=ForceRunType.NONE,
            single_test_run=False,
            num_threads=1,
            report_freq=ReportingFreq.HOURLY,
            build_a=base,
            build_b=mod
        )
        r = SuiteRunner(config, entries)
        r.add_callbacks(
            print_callback=TestTestSuiteRunner.dummy_callback,
            simstarting_callback=TestTestSuiteRunner.dummy_callback,
            casecompleted_callback=TestTestSuiteRunner.dummy_callback,
            simulationscomplete_callback=TestTestSuiteRunner.dummy_callback,
            diffcompleted_callback=TestTestSuiteRunner.dummy_callback,
            alldone_callback=TestTestSuiteRunner.dummy_callback,
            cancel_callback=TestTestSuiteRunner.dummy_callback
        )
        diff_results = r.run_test_suite()
        # there should be 1 file result
        self.assertEqual(1, len(diff_results.entries_by_file))
        results_for_file = diff_results.entries_by_file[0]
        # it should be named according to what we listed above
        self.assertEqual('EMSTestMathAndKill', results_for_file.basename)
        # it should have succeeded in both base and mod cases
        self.assertEqual(EndErrSummary.STATUS_SUCCESS, results_for_file.summary_result.simulation_status_case1)
        self.assertEqual(EndErrSummary.STATUS_SUCCESS, results_for_file.summary_result.simulation_status_case2)

    def test_case_b_fatal(self):
        base = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_base_build_dir,
            self.temp_base_source_dir,
            {
                "config": {
                    "run_time_string": "01hr 20min  0.17sec",
                    "num_warnings": 1,
                    "num_severe": 0,
                    "end_state": "success",
                    "eso_results": "base",
                    "txt_results": "base"
                }
            }
        )
        base.set_build_directory(self.temp_base_build_dir)
        base.run = True

        mod = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_mod_build_dir,
            self.temp_mod_source_dir,
            {
                "config": {
                    "run_time_string": "00hr 10min  0.17sec",
                    "num_warnings": 2,
                    "num_severe": 1,
                    "end_state": "fatal",
                    "eso_results": "base",
                    "txt_results": "base"
                }
            }
        )
        mod.set_build_directory(self.temp_mod_build_dir)
        mod.run = True

        entries = [TestEntry('my_file', 'my_weather')]
        config = TestRunConfiguration(
            force_run_type=ForceRunType.NONE,
            single_test_run=False,
            num_threads=1,
            report_freq=ReportingFreq.HOURLY,
            build_a=base,
            build_b=mod
        )
        r = SuiteRunner(config, entries)
        r.add_callbacks(
            print_callback=TestTestSuiteRunner.dummy_callback,
            simstarting_callback=TestTestSuiteRunner.dummy_callback,
            casecompleted_callback=TestTestSuiteRunner.dummy_callback,
            simulationscomplete_callback=TestTestSuiteRunner.dummy_callback,
            diffcompleted_callback=TestTestSuiteRunner.dummy_callback,
            alldone_callback=TestTestSuiteRunner.dummy_callback,
            cancel_callback=TestTestSuiteRunner.dummy_callback
        )
        diff_results = r.run_test_suite()
        # there should be 1 file result
        self.assertEqual(1, len(diff_results.entries_by_file))
        results_for_file = diff_results.entries_by_file[0]
        # it should be named according to what we listed above
        self.assertEqual('my_file', results_for_file.basename)
        # it should have succeeded in both base and mod cases
        self.assertEqual(EndErrSummary.STATUS_SUCCESS, results_for_file.summary_result.simulation_status_case1)
        self.assertEqual(EndErrSummary.STATUS_FATAL, results_for_file.summary_result.simulation_status_case2)

    def test_both_cases_fatal(self):
        base = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_base_build_dir,
            self.temp_base_source_dir,
            {
                "config": {
                    "run_time_string": "01hr 20min  0.17sec",
                    "num_warnings": 1,
                    "num_severe": 0,
                    "end_state": "fatal",
                    "eso_results": "base",
                    "txt_results": "base"
                }
            }
        )
        base.set_build_directory(self.temp_base_build_dir)
        base.run = True

        mod = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_mod_build_dir,
            self.temp_mod_source_dir,
            {
                "config": {
                    "run_time_string": "00hr 10min  0.17sec",
                    "num_warnings": 2,
                    "num_severe": 1,
                    "end_state": "fatal",
                    "eso_results": "base",
                    "txt_results": "base"
                }
            }
        )
        mod.set_build_directory(self.temp_mod_build_dir)
        mod.run = True

        entries = [TestEntry('my_file', 'my_weather')]
        config = TestRunConfiguration(
            force_run_type=ForceRunType.NONE,
            single_test_run=False,
            num_threads=1,
            report_freq=ReportingFreq.HOURLY,
            build_a=base,
            build_b=mod
        )
        r = SuiteRunner(config, entries)
        r.add_callbacks(
            print_callback=TestTestSuiteRunner.dummy_callback,
            simstarting_callback=TestTestSuiteRunner.dummy_callback,
            casecompleted_callback=TestTestSuiteRunner.dummy_callback,
            simulationscomplete_callback=TestTestSuiteRunner.dummy_callback,
            diffcompleted_callback=TestTestSuiteRunner.dummy_callback,
            alldone_callback=TestTestSuiteRunner.dummy_callback,
            cancel_callback=TestTestSuiteRunner.dummy_callback
        )
        diff_results = r.run_test_suite()
        # there should be 1 file result
        self.assertEqual(1, len(diff_results.entries_by_file))
        results_for_file = diff_results.entries_by_file[0]
        # it should be named according to what we listed above
        self.assertEqual('my_file', results_for_file.basename)
        # it should have succeeded in both base and mod cases
        self.assertEqual(EndErrSummary.STATUS_FATAL, results_for_file.summary_result.simulation_status_case1)
        self.assertEqual(EndErrSummary.STATUS_FATAL, results_for_file.summary_result.simulation_status_case2)

    def test_case_b_crash(self):
        base = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_base_build_dir,
            self.temp_base_source_dir,
            {
                "config": {
                    "run_time_string": "01hr 20min  0.17sec",
                    "num_warnings": 1,
                    "num_severe": 0,
                    "end_state": "success",
                    "eso_results": "base",
                    "txt_results": "base"
                }
            }
        )
        base.set_build_directory(self.temp_base_build_dir)
        base.run = True

        mod = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_mod_build_dir,
            self.temp_mod_source_dir,
            {
                "config": {
                    "run_time_string": "00hr 10min  0.17sec",
                    "num_warnings": 2,
                    "num_severe": 1,
                    "end_state": "crash",
                    "eso_results": "base",
                    "txt_results": "base"
                }
            }
        )
        mod.set_build_directory(self.temp_mod_build_dir)
        mod.run = True

        entries = [TestEntry('my_file', 'my_weather')]
        config = TestRunConfiguration(
            force_run_type=ForceRunType.NONE,
            single_test_run=False,
            num_threads=1,
            report_freq=ReportingFreq.HOURLY,
            build_a=base,
            build_b=mod
        )
        r = SuiteRunner(config, entries)
        r.add_callbacks(
            print_callback=TestTestSuiteRunner.dummy_callback,
            simstarting_callback=TestTestSuiteRunner.dummy_callback,
            casecompleted_callback=TestTestSuiteRunner.dummy_callback,
            simulationscomplete_callback=TestTestSuiteRunner.dummy_callback,
            diffcompleted_callback=TestTestSuiteRunner.dummy_callback,
            alldone_callback=TestTestSuiteRunner.dummy_callback,
            cancel_callback=TestTestSuiteRunner.dummy_callback
        )
        diff_results = r.run_test_suite()
        # there should be 1 file result
        self.assertEqual(1, len(diff_results.entries_by_file))
        results_for_file = diff_results.entries_by_file[0]
        # it should be named according to what we listed above
        self.assertEqual('my_file', results_for_file.basename)
        # it should have succeeded in both base and mod cases
        self.assertEqual(EndErrSummary.STATUS_SUCCESS, results_for_file.summary_result.simulation_status_case1)
        self.assertEqual(EndErrSummary.STATUS_MISSING, results_for_file.summary_result.simulation_status_case2)

    def test_case_b_unknown(self):
        base = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_base_build_dir,
            self.temp_base_source_dir,
            {
                "config": {
                    "run_time_string": "01hr 20min  0.17sec",
                    "num_warnings": 1,
                    "num_severe": 0,
                    "end_state": "success",
                    "eso_results": "base",
                    "txt_results": "base"
                }
            }
        )
        base.set_build_directory(self.temp_base_build_dir)
        base.run = True

        mod = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_mod_build_dir,
            self.temp_mod_source_dir,
            {
                "config": {
                    "run_time_string": "00hr 10min  0.17sec",
                    "num_warnings": 2,
                    "num_severe": 1,
                    "end_state": "unknown",
                    "eso_results": "base",
                    "txt_results": "base"
                }
            }
        )
        mod.set_build_directory(self.temp_mod_build_dir)
        mod.run = True

        entries = [TestEntry('my_file', 'my_weather')]
        config = TestRunConfiguration(
            force_run_type=ForceRunType.NONE,
            single_test_run=False,
            num_threads=1,
            report_freq=ReportingFreq.HOURLY,
            build_a=base,
            build_b=mod
        )
        r = SuiteRunner(config, entries)
        r.add_callbacks(
            print_callback=TestTestSuiteRunner.dummy_callback,
            simstarting_callback=TestTestSuiteRunner.dummy_callback,
            casecompleted_callback=TestTestSuiteRunner.dummy_callback,
            simulationscomplete_callback=TestTestSuiteRunner.dummy_callback,
            diffcompleted_callback=TestTestSuiteRunner.dummy_callback,
            alldone_callback=TestTestSuiteRunner.dummy_callback,
            cancel_callback=TestTestSuiteRunner.dummy_callback
        )
        diff_results = r.run_test_suite()
        # there should be 1 file result
        self.assertEqual(1, len(diff_results.entries_by_file))
        results_for_file = diff_results.entries_by_file[0]
        # it should be named according to what we listed above
        self.assertEqual('my_file', results_for_file.basename)
        # it should have succeeded in both base and mod cases
        self.assertEqual(EndErrSummary.STATUS_SUCCESS, results_for_file.summary_result.simulation_status_case1)
        self.assertEqual(EndErrSummary.STATUS_UNKNOWN, results_for_file.summary_result.simulation_status_case2)

    def test_small_diffs(self):
        base = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_base_build_dir,
            self.temp_base_source_dir,
            {
                "config": {
                    "run_time_string": "01hr 20min  0.17sec",
                    "num_warnings": 1,
                    "num_severe": 0,
                    "end_state": "success",
                    "eso_results": "base",
                    "txt_results": "base"
                }
            }
        )
        base.set_build_directory(self.temp_base_build_dir)
        base.run = True

        mod = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_mod_build_dir,
            self.temp_mod_source_dir,
            {
                "config": {
                    "run_time_string": "00hr 10min  0.17sec",
                    "num_warnings": 2,
                    "num_severe": 1,
                    "end_state": "success",
                    "eso_results": "smalldiffs",
                    "txt_results": "base"
                }
            }
        )
        mod.set_build_directory(self.temp_mod_build_dir)
        mod.run = True

        entries = [TestEntry('my_file', 'my_weather')]
        config = TestRunConfiguration(
            force_run_type=ForceRunType.NONE,
            single_test_run=False,
            num_threads=1,
            report_freq=ReportingFreq.HOURLY,
            build_a=base,
            build_b=mod
        )
        r = SuiteRunner(config, entries)
        r.add_callbacks(
            print_callback=TestTestSuiteRunner.dummy_callback,
            simstarting_callback=TestTestSuiteRunner.dummy_callback,
            casecompleted_callback=TestTestSuiteRunner.dummy_callback,
            simulationscomplete_callback=TestTestSuiteRunner.dummy_callback,
            diffcompleted_callback=TestTestSuiteRunner.dummy_callback,
            alldone_callback=TestTestSuiteRunner.dummy_callback,
            cancel_callback=TestTestSuiteRunner.dummy_callback
        )
        diff_results = r.run_test_suite()
        # there should be 1 file result
        self.assertEqual(1, len(diff_results.entries_by_file))
        results_for_file = diff_results.entries_by_file[0]
        # it should be named according to what we listed above
        self.assertEqual('my_file', results_for_file.basename)
        # it should have succeeded in both base and mod cases
        self.assertEqual(EndErrSummary.STATUS_SUCCESS, results_for_file.summary_result.simulation_status_case1)
        self.assertEqual(EndErrSummary.STATUS_SUCCESS, results_for_file.summary_result.simulation_status_case2)
        # it should have created a test directory and dropped the summaries there
        results_dir = diff_results.results_dir
        self.assertTrue(os.path.exists(os.path.join(results_dir, 'test_results.json')))
        self.assertTrue(os.path.exists(os.path.join(results_dir, 'run_times.csv')))
        # it should have created a run directory for this file, put input files there, and left output files there
        file_results_dir = os.path.join(results_dir, 'my_file')
        self.assertTrue(os.path.exists(file_results_dir))
        self.assertTrue(os.path.exists(os.path.join(file_results_dir, 'in.epw')))
        self.assertTrue(os.path.exists(os.path.join(file_results_dir, 'in.idf')))
        self.assertTrue(os.path.exists(os.path.join(file_results_dir, 'eplusout.eso')))
        self.assertTrue(os.path.exists(os.path.join(file_results_dir, 'eplusout.end')))
        self.assertTrue(os.path.exists(os.path.join(file_results_dir, 'eplusout.csv')))
        # check the diffs
        self.assertEqual('Small Diffs', results_for_file.eso_diffs.diff_type)
        self.assertEqual('Small Diffs', results_for_file.mtr_diffs.diff_type)
        self.assertEqual('Small Diffs', results_for_file.ssz_diffs.diff_type)
        self.assertEqual('Small Diffs', results_for_file.zsz_diffs.diff_type)

    def test_big_diffs(self):
        base = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_base_build_dir,
            self.temp_base_source_dir,
            {
                "config": {
                    "run_time_string": "01hr 20min  0.17sec",
                    "num_warnings": 1,
                    "num_severe": 0,
                    "end_state": "success",
                    "eso_results": "base",
                    "txt_results": "base"
                }
            }
        )
        base.set_build_directory(self.temp_base_build_dir)
        base.run = True

        mod = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_mod_build_dir,
            self.temp_mod_source_dir,
            {
                "config": {
                    "run_time_string": "00hr 10min  0.17sec",
                    "num_warnings": 2,
                    "num_severe": 1,
                    "end_state": "success",
                    "eso_results": "bigdiffs",
                    "txt_results": "base"
                }
            }
        )
        mod.set_build_directory(self.temp_mod_build_dir)
        mod.run = True

        entries = [TestEntry('my_file', 'my_weather')]
        config = TestRunConfiguration(
            force_run_type=ForceRunType.NONE,
            single_test_run=False,
            num_threads=1,
            report_freq=ReportingFreq.HOURLY,
            build_a=base,
            build_b=mod
        )
        r = SuiteRunner(config, entries)
        r.add_callbacks(
            print_callback=TestTestSuiteRunner.dummy_callback,
            simstarting_callback=TestTestSuiteRunner.dummy_callback,
            casecompleted_callback=TestTestSuiteRunner.dummy_callback,
            simulationscomplete_callback=TestTestSuiteRunner.dummy_callback,
            diffcompleted_callback=TestTestSuiteRunner.dummy_callback,
            alldone_callback=TestTestSuiteRunner.dummy_callback,
            cancel_callback=TestTestSuiteRunner.dummy_callback
        )
        diff_results = r.run_test_suite()
        # there should be 1 file result
        self.assertEqual(1, len(diff_results.entries_by_file))
        results_for_file = diff_results.entries_by_file[0]
        # it should be named according to what we listed above
        self.assertEqual('my_file', results_for_file.basename)
        # it should have succeeded in both base and mod cases
        self.assertEqual(EndErrSummary.STATUS_SUCCESS, results_for_file.summary_result.simulation_status_case1)
        self.assertEqual(EndErrSummary.STATUS_SUCCESS, results_for_file.summary_result.simulation_status_case2)
        # it should have created a test directory and dropped the summaries there
        results_dir = diff_results.results_dir
        self.assertTrue(os.path.exists(os.path.join(results_dir, 'test_results.json')))
        self.assertTrue(os.path.exists(os.path.join(results_dir, 'run_times.csv')))
        # it should have created a run directory for this file, put input files there, and left output files there
        file_results_dir = os.path.join(results_dir, 'my_file')
        self.assertTrue(os.path.exists(file_results_dir))
        self.assertTrue(os.path.exists(os.path.join(file_results_dir, 'in.epw')))
        self.assertTrue(os.path.exists(os.path.join(file_results_dir, 'in.idf')))
        self.assertTrue(os.path.exists(os.path.join(file_results_dir, 'eplusout.eso')))
        self.assertTrue(os.path.exists(os.path.join(file_results_dir, 'eplusout.end')))
        self.assertTrue(os.path.exists(os.path.join(file_results_dir, 'eplusout.csv')))
        # check the diffs
        self.assertEqual('Big Diffs', results_for_file.eso_diffs.diff_type)
        self.assertEqual('Big Diffs', results_for_file.mtr_diffs.diff_type)
        self.assertEqual('Big Diffs', results_for_file.ssz_diffs.diff_type)
        self.assertEqual('Big Diffs', results_for_file.zsz_diffs.diff_type)

    def test_text_diffs(self):
        base = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_base_build_dir,
            self.temp_base_source_dir,
            {
                "config": {
                    "run_time_string": "01hr 20min  0.17sec",
                    "num_warnings": 1,
                    "num_severe": 0,
                    "end_state": "success",
                    "eso_results": "base",
                    "txt_results": "base",
                }
            }
        )
        base.set_build_directory(self.temp_base_build_dir)
        base.run = True

        mod = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_mod_build_dir,
            self.temp_mod_source_dir,
            {
                "config": {
                    "run_time_string": "00hr 10min  0.17sec",
                    "num_warnings": 2,
                    "num_severe": 1,
                    "end_state": "success",
                    "eso_results": "base",
                    "txt_results": "diffs"
                }
            }
        )
        mod.set_build_directory(self.temp_mod_build_dir)
        mod.run = True

        entries = [TestEntry('my_file', 'my_weather')]
        config = TestRunConfiguration(
            force_run_type=ForceRunType.NONE,
            single_test_run=False,
            num_threads=1,
            report_freq=ReportingFreq.HOURLY,
            build_a=base,
            build_b=mod
        )
        r = SuiteRunner(config, entries)
        r.add_callbacks(
            print_callback=TestTestSuiteRunner.dummy_callback,
            simstarting_callback=TestTestSuiteRunner.dummy_callback,
            casecompleted_callback=TestTestSuiteRunner.dummy_callback,
            simulationscomplete_callback=TestTestSuiteRunner.dummy_callback,
            diffcompleted_callback=TestTestSuiteRunner.dummy_callback,
            alldone_callback=TestTestSuiteRunner.dummy_callback,
            cancel_callback=TestTestSuiteRunner.dummy_callback
        )
        diff_results = r.run_test_suite()
        # there should be 1 file result
        self.assertEqual(1, len(diff_results.entries_by_file))
        results_for_file = diff_results.entries_by_file[0]
        # check the diffs
        self.assertEqual(TextDifferences.DIFFS, results_for_file.aud_diffs.diff_type)
        self.assertEqual(TextDifferences.DIFFS, results_for_file.bnd_diffs.diff_type)
        self.assertEqual(TextDifferences.DIFFS, results_for_file.dl_in_diffs.diff_type)
        self.assertEqual(TextDifferences.DIFFS, results_for_file.dl_out_diffs.diff_type)
        self.assertEqual(TextDifferences.DIFFS, results_for_file.dxf_diffs.diff_type)
        self.assertEqual(TextDifferences.DIFFS, results_for_file.eio_diffs.diff_type)
        self.assertEqual(TextDifferences.DIFFS, results_for_file.err_diffs.diff_type)
        self.assertEqual(TextDifferences.DIFFS, results_for_file.mdd_diffs.diff_type)
        self.assertEqual(TextDifferences.DIFFS, results_for_file.mtd_diffs.diff_type)
        self.assertEqual(TextDifferences.DIFFS, results_for_file.rdd_diffs.diff_type)
        self.assertEqual(TextDifferences.DIFFS, results_for_file.shd_diffs.diff_type)

    def test_base_case_but_multi_process(self):
        base = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_base_build_dir,
            self.temp_base_source_dir,
            {
                "config": {
                    "run_time_string": "01hr 20min  0.17sec",
                    "num_warnings": 1,
                    "num_severe": 0,
                    "end_state": "success",
                    "eso_results": "base"
                }
            }
        )
        base.set_build_directory(self.temp_base_build_dir)
        base.run = True

        mod = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_mod_build_dir,
            self.temp_mod_source_dir,
            {
                "config": {
                    "run_time_string": "00hr 10min  0.17sec",
                    "num_warnings": 2,
                    "num_severe": 1,
                    "end_state": "success",
                    "eso_results": "base"
                }
            }
        )
        mod.set_build_directory(self.temp_mod_build_dir)
        mod.run = True

        entries = [TestEntry('my_file', 'my_weather'), TestEntry('my_macro_file', 'my_weather')]
        config = TestRunConfiguration(
            force_run_type=ForceRunType.NONE,
            single_test_run=False,
            num_threads=2,
            report_freq=ReportingFreq.HOURLY,
            build_a=base,
            build_b=mod
        )
        r = SuiteRunner(config, entries)
        r.add_callbacks(
            print_callback=TestTestSuiteRunner.dummy_callback,
            simstarting_callback=TestTestSuiteRunner.dummy_callback,
            casecompleted_callback=TestTestSuiteRunner.dummy_callback,
            simulationscomplete_callback=TestTestSuiteRunner.dummy_callback,
            diffcompleted_callback=TestTestSuiteRunner.dummy_callback,
            alldone_callback=TestTestSuiteRunner.dummy_callback,
            cancel_callback=TestTestSuiteRunner.dummy_callback
        )
        diff_results = r.run_test_suite()
        # there should be 1 file result
        self.assertEqual(2, len(diff_results.entries_by_file))
        results_for_file = diff_results.entries_by_file[0]
        # it should be named according to what we listed above
        self.assertEqual('my_file', results_for_file.basename)
        # it should have succeeded in both base and mod cases
        self.assertEqual(EndErrSummary.STATUS_SUCCESS, results_for_file.summary_result.simulation_status_case1)
        self.assertEqual(EndErrSummary.STATUS_SUCCESS, results_for_file.summary_result.simulation_status_case2)
        # it should have created a test directory and dropped the summaries there
        results_dir = diff_results.results_dir
        self.assertTrue(os.path.exists(os.path.join(results_dir, 'test_results.json')))
        self.assertTrue(os.path.exists(os.path.join(results_dir, 'run_times.csv')))
        # it should have created a run directory for this file, put input files there, and left output files there
        file_results_dir = os.path.join(results_dir, 'my_file')
        self.assertTrue(os.path.exists(file_results_dir))
        self.assertTrue(os.path.exists(os.path.join(file_results_dir, 'in.epw')))
        self.assertTrue(os.path.exists(os.path.join(file_results_dir, 'in.idf')))
        self.assertTrue(os.path.exists(os.path.join(file_results_dir, 'eplusout.eso')))
        self.assertTrue(os.path.exists(os.path.join(file_results_dir, 'eplusout.end')))
        self.assertTrue(os.path.exists(os.path.join(file_results_dir, 'eplusout.csv')))

    def test_window5_file_gets_dependencies(self):
        base = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_base_build_dir,
            self.temp_base_source_dir,
            {
                "config": {
                    "run_time_string": "01hr 20min  0.17sec",
                    "num_warnings": 1,
                    "num_severe": 0,
                    "end_state": "success",
                    "eso_results": "base",
                    "extra_data": "Window5DataFile.dat"
                }
            }
        )
        base.set_build_directory(self.temp_base_build_dir)
        base.run = True

        mod = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_mod_build_dir,
            self.temp_mod_source_dir,
            {
                "config": {
                    "run_time_string": "00hr 10min  0.17sec",
                    "num_warnings": 2,
                    "num_severe": 1,
                    "end_state": "success",
                    "eso_results": "base",
                    "extra_data": "Window5DataFile.dat"
                }
            }
        )
        mod.set_build_directory(self.temp_mod_build_dir)
        mod.run = True

        entries = [TestEntry('my_file', 'my_weather')]
        config = TestRunConfiguration(
            force_run_type=ForceRunType.NONE,
            single_test_run=False,
            num_threads=1,
            report_freq=ReportingFreq.HOURLY,
            build_a=base,
            build_b=mod
        )
        r = SuiteRunner(config, entries)
        r.add_callbacks(
            print_callback=TestTestSuiteRunner.dummy_callback,
            simstarting_callback=TestTestSuiteRunner.dummy_callback,
            casecompleted_callback=TestTestSuiteRunner.dummy_callback,
            simulationscomplete_callback=TestTestSuiteRunner.dummy_callback,
            diffcompleted_callback=TestTestSuiteRunner.dummy_callback,
            alldone_callback=TestTestSuiteRunner.dummy_callback,
            cancel_callback=TestTestSuiteRunner.dummy_callback
        )
        diff_results = r.run_test_suite()
        # there should be 1 file result
        self.assertEqual(1, len(diff_results.entries_by_file))
        results_for_file = diff_results.entries_by_file[0]
        # it should be named according to what we listed above
        self.assertEqual('my_file', results_for_file.basename)
        # it should have succeeded in both base and mod cases
        self.assertEqual(EndErrSummary.STATUS_SUCCESS, results_for_file.summary_result.simulation_status_case1)
        self.assertEqual(EndErrSummary.STATUS_SUCCESS, results_for_file.summary_result.simulation_status_case2)
        # it should have created a test directory and dropped the summaries there
        results_dir = diff_results.results_dir
        self.assertTrue(os.path.exists(os.path.join(results_dir, 'test_results.json')))
        self.assertTrue(os.path.exists(os.path.join(results_dir, 'run_times.csv')))
        # it should have put Window5 dataset files in the run directory
        file_results_dir = os.path.join(results_dir, 'my_file')
        self.assertTrue(os.path.exists(os.path.join(file_results_dir, 'datasets', 'Window5DataFile.dat')))

    def test_tdv_file_gets_dependencies(self):
        base = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(  # noqa: W605
            self.temp_base_build_dir,
            self.temp_base_source_dir,
            {
                "config": {
                    "run_time_string": "01hr 20min  0.17sec",
                    "num_warnings": 1,
                    "num_severe": 0,
                    "end_state": "success",
                    "eso_results": "base",
                    "extra_data": "DataSets\TDV"
                }
            }
        )
        base.set_build_directory(self.temp_base_build_dir)
        base.run = True

        mod = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(  # noqa: W605
            self.temp_mod_build_dir,
            self.temp_mod_source_dir,
            {
                "config": {
                    "run_time_string": "00hr 10min  0.17sec",
                    "num_warnings": 2,
                    "num_severe": 1,
                    "end_state": "success",
                    "eso_results": "base",
                    "extra_data": "DataSets\TDV"
                }
            }
        )
        mod.set_build_directory(self.temp_mod_build_dir)
        mod.run = True

        entries = [TestEntry('my_file', 'my_weather')]
        config = TestRunConfiguration(
            force_run_type=ForceRunType.NONE,
            single_test_run=False,
            num_threads=1,
            report_freq=ReportingFreq.HOURLY,
            build_a=base,
            build_b=mod
        )
        r = SuiteRunner(config, entries)
        r.add_callbacks(
            print_callback=TestTestSuiteRunner.dummy_callback,
            simstarting_callback=TestTestSuiteRunner.dummy_callback,
            casecompleted_callback=TestTestSuiteRunner.dummy_callback,
            simulationscomplete_callback=TestTestSuiteRunner.dummy_callback,
            diffcompleted_callback=TestTestSuiteRunner.dummy_callback,
            alldone_callback=TestTestSuiteRunner.dummy_callback,
            cancel_callback=TestTestSuiteRunner.dummy_callback
        )
        diff_results = r.run_test_suite()
        # there should be 1 file result
        self.assertEqual(1, len(diff_results.entries_by_file))
        results_for_file = diff_results.entries_by_file[0]
        # it should be named according to what we listed above
        self.assertEqual('my_file', results_for_file.basename)
        # it should have succeeded in both base and mod cases
        self.assertEqual(EndErrSummary.STATUS_SUCCESS, results_for_file.summary_result.simulation_status_case1)
        self.assertEqual(EndErrSummary.STATUS_SUCCESS, results_for_file.summary_result.simulation_status_case2)
        # it should have created a test directory and dropped the summaries there
        results_dir = diff_results.results_dir
        self.assertTrue(os.path.exists(os.path.join(results_dir, 'test_results.json')))
        self.assertTrue(os.path.exists(os.path.join(results_dir, 'run_times.csv')))
        # it should have put TDV dataset files in the run directory
        file_results_dir = os.path.join(results_dir, 'my_file')
        self.assertTrue(os.path.exists(os.path.join(file_results_dir, 'datasets', 'TDV', 'dummy.txt')))

    def test_hybrid_file_gets_dependencies(self):
        base = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_base_build_dir,
            self.temp_base_source_dir,
            {
                "config": {
                    "run_time_string": "01hr 20min  0.17sec",
                    "num_warnings": 1,
                    "num_severe": 0,
                    "end_state": "success",
                    "eso_results": "base",
                    "extra_data": "HybridZoneModel_TemperatureData.csv"
                }
            }
        )
        base.set_build_directory(self.temp_base_build_dir)
        base.run = True

        mod = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_mod_build_dir,
            self.temp_mod_source_dir,
            {
                "config": {
                    "run_time_string": "00hr 10min  0.17sec",
                    "num_warnings": 2,
                    "num_severe": 1,
                    "end_state": "success",
                    "eso_results": "base",
                    "extra_data": "HybridZoneModel_TemperatureData.csv"
                }
            }
        )
        mod.set_build_directory(self.temp_mod_build_dir)
        mod.run = True

        entries = [TestEntry('my_file', 'my_weather')]
        config = TestRunConfiguration(
            force_run_type=ForceRunType.NONE,
            single_test_run=False,
            num_threads=1,
            report_freq=ReportingFreq.HOURLY,
            build_a=base,
            build_b=mod
        )
        r = SuiteRunner(config, entries)
        r.add_callbacks(
            print_callback=TestTestSuiteRunner.dummy_callback,
            simstarting_callback=TestTestSuiteRunner.dummy_callback,
            casecompleted_callback=TestTestSuiteRunner.dummy_callback,
            simulationscomplete_callback=TestTestSuiteRunner.dummy_callback,
            diffcompleted_callback=TestTestSuiteRunner.dummy_callback,
            alldone_callback=TestTestSuiteRunner.dummy_callback,
            cancel_callback=TestTestSuiteRunner.dummy_callback
        )
        diff_results = r.run_test_suite()
        # there should be 1 file result
        self.assertEqual(1, len(diff_results.entries_by_file))
        results_for_file = diff_results.entries_by_file[0]
        # it should be named according to what we listed above
        self.assertEqual('my_file', results_for_file.basename)
        # it should have succeeded in both base and mod cases
        self.assertEqual(EndErrSummary.STATUS_SUCCESS, results_for_file.summary_result.simulation_status_case1)
        self.assertEqual(EndErrSummary.STATUS_SUCCESS, results_for_file.summary_result.simulation_status_case2)
        # it should have created a test directory and dropped the summaries there
        results_dir = diff_results.results_dir
        self.assertTrue(os.path.exists(os.path.join(results_dir, 'test_results.json')))
        self.assertTrue(os.path.exists(os.path.join(results_dir, 'run_times.csv')))
        # it should have put TDV dataset files in the run directory
        file_results_dir = os.path.join(results_dir, 'my_file')
        self.assertTrue(os.path.exists(os.path.join(file_results_dir, 'HybridZoneModel_TemperatureData.csv')))

    def test_macro_file_gets_dependencies(self):
        base = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_base_build_dir,
            self.temp_base_source_dir,
            {
                "config": {
                    "run_time_string": "01hr 20min  0.17sec",
                    "num_warnings": 1,
                    "num_severe": 0,
                    "end_state": "success",
                    "eso_results": "base",
                    "extra_data": ""
                }
            }
        )
        base.set_build_directory(self.temp_base_build_dir)
        base.run = True

        mod = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_mod_build_dir,
            self.temp_mod_source_dir,
            {
                "config": {
                    "run_time_string": "00hr 10min  0.17sec",
                    "num_warnings": 2,
                    "num_severe": 1,
                    "end_state": "success",
                    "eso_results": "base",
                    "extra_data": ""
                }
            }
        )
        mod.set_build_directory(self.temp_mod_build_dir)
        mod.run = True

        entries = [TestEntry('my_macro_file', 'my_weather')]
        config = TestRunConfiguration(
            force_run_type=ForceRunType.NONE,
            single_test_run=False,
            num_threads=1,
            report_freq=ReportingFreq.HOURLY,
            build_a=base,
            build_b=mod
        )
        r = SuiteRunner(config, entries)
        r.add_callbacks(
            print_callback=TestTestSuiteRunner.dummy_callback,
            simstarting_callback=TestTestSuiteRunner.dummy_callback,
            casecompleted_callback=TestTestSuiteRunner.dummy_callback,
            simulationscomplete_callback=TestTestSuiteRunner.dummy_callback,
            diffcompleted_callback=TestTestSuiteRunner.dummy_callback,
            alldone_callback=TestTestSuiteRunner.dummy_callback,
            cancel_callback=TestTestSuiteRunner.dummy_callback
        )
        diff_results = r.run_test_suite()
        # there should be 1 file result
        self.assertEqual(1, len(diff_results.entries_by_file))
        results_for_file = diff_results.entries_by_file[0]
        # it should be named according to what we listed above
        self.assertEqual('my_macro_file', results_for_file.basename)
        # it should have succeeded in both base and mod cases
        self.assertEqual(EndErrSummary.STATUS_SUCCESS, results_for_file.summary_result.simulation_status_case1)
        self.assertEqual(EndErrSummary.STATUS_SUCCESS, results_for_file.summary_result.simulation_status_case2)
        # it should have created a test directory and dropped the summaries there
        results_dir = diff_results.results_dir
        self.assertTrue(os.path.exists(os.path.join(results_dir, 'test_results.json')))
        self.assertTrue(os.path.exists(os.path.join(results_dir, 'run_times.csv')))
        # it should have put Macro files in the run directory
        file_results_dir = os.path.join(results_dir, 'my_macro_file')
        self.assertTrue(os.path.exists(os.path.join(file_results_dir, 'extra.imf')))

    def test_missing_weather_still_gets_epw(self):
        base = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_base_build_dir,
            self.temp_base_source_dir,
            {
                "config": {
                    "run_time_string": "01hr 20min  0.17sec",
                    "num_warnings": 1,
                    "num_severe": 0,
                    "end_state": "success",
                    "eso_results": "base",
                    "extra_data": ""
                }
            }
        )
        base.set_build_directory(self.temp_base_build_dir)
        base.run = True

        mod = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_mod_build_dir,
            self.temp_mod_source_dir,
            {
                "config": {
                    "run_time_string": "00hr 10min  0.17sec",
                    "num_warnings": 2,
                    "num_severe": 1,
                    "end_state": "success",
                    "eso_results": "base",
                    "extra_data": ""
                }
            }
        )
        mod.set_build_directory(self.temp_mod_build_dir)
        mod.run = True

        entries = [TestEntry('my_file', 'my_weather_DOES_NOT_EXIST')]
        config = TestRunConfiguration(
            force_run_type=ForceRunType.NONE,
            single_test_run=False,
            num_threads=1,
            report_freq=ReportingFreq.HOURLY,
            build_a=base,
            build_b=mod
        )
        r = SuiteRunner(config, entries)
        r.add_callbacks(
            print_callback=TestTestSuiteRunner.dummy_callback,
            simstarting_callback=TestTestSuiteRunner.dummy_callback,
            casecompleted_callback=TestTestSuiteRunner.dummy_callback,
            simulationscomplete_callback=TestTestSuiteRunner.dummy_callback,
            diffcompleted_callback=TestTestSuiteRunner.dummy_callback,
            alldone_callback=TestTestSuiteRunner.dummy_callback,
            cancel_callback=TestTestSuiteRunner.dummy_callback
        )
        diff_results = r.run_test_suite()
        # there should be 1 file result
        self.assertEqual(1, len(diff_results.entries_by_file))
        results_for_file = diff_results.entries_by_file[0]
        # it should be named according to what we listed above
        self.assertEqual('my_file', results_for_file.basename)
        # it should have succeeded in both base and mod cases
        self.assertEqual(EndErrSummary.STATUS_SUCCESS, results_for_file.summary_result.simulation_status_case1)
        self.assertEqual(EndErrSummary.STATUS_SUCCESS, results_for_file.summary_result.simulation_status_case2)
        # it should have created a test directory and dropped the summaries there
        results_dir = diff_results.results_dir
        self.assertTrue(os.path.exists(os.path.join(results_dir, 'test_results.json')))
        self.assertTrue(os.path.exists(os.path.join(results_dir, 'run_times.csv')))
        # it should have put an epw files in the run directory
        file_results_dir = os.path.join(results_dir, 'my_file')
        self.assertTrue(os.path.exists(os.path.join(file_results_dir, 'in.epw')))

    def test_report_variable_dictionary_gets_scrubbed(self):
        base = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_base_build_dir,
            self.temp_base_source_dir,
            {
                "config": {
                    "run_time_string": "01hr 20min  0.17sec",
                    "num_warnings": 1,
                    "num_severe": 0,
                    "end_state": "success",
                    "eso_results": "base",
                    "extra_data": 'report variable dictionary'
                }
            }
        )
        base.set_build_directory(self.temp_base_build_dir)
        base.run = True

        mod = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_mod_build_dir,
            self.temp_mod_source_dir,
            {
                "config": {
                    "run_time_string": "00hr 10min  0.17sec",
                    "num_warnings": 2,
                    "num_severe": 1,
                    "end_state": "success",
                    "eso_results": "base",
                    "extra_data": 'report variable dictionary'
                }
            }
        )
        mod.set_build_directory(self.temp_mod_build_dir)
        mod.run = True

        entries = [TestEntry('my_file', 'my_weather')]
        config = TestRunConfiguration(
            force_run_type=ForceRunType.NONE,
            single_test_run=False,
            num_threads=1,
            report_freq=ReportingFreq.HOURLY,
            build_a=base,
            build_b=mod
        )
        r = SuiteRunner(config, entries)
        r.add_callbacks(
            print_callback=TestTestSuiteRunner.dummy_callback,
            simstarting_callback=TestTestSuiteRunner.dummy_callback,
            casecompleted_callback=TestTestSuiteRunner.dummy_callback,
            simulationscomplete_callback=TestTestSuiteRunner.dummy_callback,
            diffcompleted_callback=TestTestSuiteRunner.dummy_callback,
            alldone_callback=TestTestSuiteRunner.dummy_callback,
            cancel_callback=TestTestSuiteRunner.dummy_callback
        )
        diff_results = r.run_test_suite()
        # there should be 1 file result
        self.assertEqual(1, len(diff_results.entries_by_file))
        results_for_file = diff_results.entries_by_file[0]
        # it should be named according to what we listed above
        self.assertEqual('my_file', results_for_file.basename)
        # it should have succeeded in both base and mod cases
        self.assertEqual(EndErrSummary.STATUS_SUCCESS, results_for_file.summary_result.simulation_status_case1)
        self.assertEqual(EndErrSummary.STATUS_SUCCESS, results_for_file.summary_result.simulation_status_case2)
        # it should have created a test directory and dropped the summaries there
        results_dir = diff_results.results_dir
        self.assertTrue(os.path.exists(os.path.join(results_dir, 'test_results.json')))
        self.assertTrue(os.path.exists(os.path.join(results_dir, 'run_times.csv')))
        # it should have put TDV dataset files in the run directory
        file_results_dir = os.path.join(results_dir, 'my_file')
        self.assertTrue(os.path.exists(os.path.join(file_results_dir, 'in.idf')))
        with open(os.path.join(file_results_dir, 'in.idf')) as f_idf:
            body = f_idf.read()
            self.assertNotIn('report variable dictionary', body)

    def test_parametric_is_signalled(self):
        base = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_base_build_dir,
            self.temp_base_source_dir,
            {
                "config": {
                    "run_time_string": "01hr 20min  0.17sec",
                    "num_warnings": 1,
                    "num_severe": 0,
                    "end_state": "success",
                    "eso_results": "base",
                    "extra_data": 'Parametric:'
                }
            }
        )
        base.set_build_directory(self.temp_base_build_dir)
        base.run = True

        mod = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_mod_build_dir,
            self.temp_mod_source_dir,
            {
                "config": {
                    "run_time_string": "00hr 10min  0.17sec",
                    "num_warnings": 2,
                    "num_severe": 1,
                    "end_state": "success",
                    "eso_results": "base",
                    "extra_data": 'Parametric:'
                }
            }
        )
        mod.set_build_directory(self.temp_mod_build_dir)
        mod.run = True

        entries = [TestEntry('my_file', 'my_weather')]
        config = TestRunConfiguration(
            force_run_type=ForceRunType.NONE,
            single_test_run=False,
            num_threads=1,
            report_freq=ReportingFreq.HOURLY,
            build_a=base,
            build_b=mod
        )
        r = SuiteRunner(config, entries)
        r.add_callbacks(
            print_callback=TestTestSuiteRunner.dummy_callback,
            simstarting_callback=TestTestSuiteRunner.dummy_callback,
            casecompleted_callback=TestTestSuiteRunner.dummy_callback,
            simulationscomplete_callback=TestTestSuiteRunner.dummy_callback,
            diffcompleted_callback=TestTestSuiteRunner.dummy_callback,
            alldone_callback=TestTestSuiteRunner.dummy_callback,
            cancel_callback=TestTestSuiteRunner.dummy_callback
        )
        diff_results = r.run_test_suite()
        # there should be 1 file result
        self.assertEqual(1, len(diff_results.entries_by_file))
        results_for_file = diff_results.entries_by_file[0]
        # it should be named according to what we listed above
        self.assertEqual('my_file', results_for_file.basename)
        # it should have succeeded in both base and mod cases
        self.assertEqual(EndErrSummary.STATUS_SUCCESS, results_for_file.summary_result.simulation_status_case1)
        self.assertEqual(EndErrSummary.STATUS_SUCCESS, results_for_file.summary_result.simulation_status_case2)
        # it should have created a test directory and dropped the summaries there
        results_dir = diff_results.results_dir
        self.assertTrue(os.path.exists(os.path.join(results_dir, 'test_results.json')))
        self.assertTrue(os.path.exists(os.path.join(results_dir, 'run_times.csv')))
        # it should have put TDV dataset files in the run directory
        file_results_dir = os.path.join(results_dir, 'my_file')
        self.assertTrue(os.path.exists(os.path.join(file_results_dir, 'in.idf')))
        self.assertTrue(os.path.exists(os.path.join(file_results_dir, 'in-02.idf')))

    def test_external_interface_is_skipped(self):
        base = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_base_build_dir,
            self.temp_base_source_dir,
            {
                "config": {
                    "run_time_string": "01hr 20min  0.17sec",
                    "num_warnings": 1,
                    "num_severe": 0,
                    "end_state": "success",
                    "eso_results": "base",
                    "extra_data": 'ExternalInterface:'
                }
            }
        )
        base.set_build_directory(self.temp_base_build_dir)
        base.run = True

        mod = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_mod_build_dir,
            self.temp_mod_source_dir,
            {
                "config": {
                    "run_time_string": "00hr 10min  0.17sec",
                    "num_warnings": 2,
                    "num_severe": 1,
                    "end_state": "success",
                    "eso_results": "base",
                    "extra_data": 'ExternalInterface:'
                }
            }
        )
        mod.set_build_directory(self.temp_mod_build_dir)
        mod.run = True

        entries = [TestEntry('my_file', 'my_weather')]
        config = TestRunConfiguration(
            force_run_type=ForceRunType.NONE,
            single_test_run=False,
            num_threads=1,
            report_freq=ReportingFreq.HOURLY,
            build_a=base,
            build_b=mod
        )
        r = SuiteRunner(config, entries)
        r.add_callbacks(
            print_callback=TestTestSuiteRunner.dummy_callback,
            simstarting_callback=TestTestSuiteRunner.dummy_callback,
            casecompleted_callback=TestTestSuiteRunner.dummy_callback,
            simulationscomplete_callback=TestTestSuiteRunner.dummy_callback,
            diffcompleted_callback=TestTestSuiteRunner.dummy_callback,
            alldone_callback=TestTestSuiteRunner.dummy_callback,
            cancel_callback=TestTestSuiteRunner.dummy_callback
        )
        diff_results = r.run_test_suite()
        # there should be 1 file result
        self.assertEqual(1, len(diff_results.entries_by_file))
        results_for_file = diff_results.entries_by_file[0]
        # it should be named according to what we listed above
        self.assertEqual('my_file', results_for_file.basename)
        # it should have been skipped in both cases, so missing
        self.assertEqual(EndErrSummary.STATUS_MISSING, results_for_file.summary_result.simulation_status_case1)
        self.assertEqual(EndErrSummary.STATUS_MISSING, results_for_file.summary_result.simulation_status_case2)

    def test_both_success_no_diffs_dd_only(self):
        base = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_base_build_dir,
            self.temp_base_source_dir,
            {
                "config": {
                    "run_time_string": "01hr 20min  0.17sec",
                    "num_warnings": 1,
                    "num_severe": 0,
                    "end_state": "success",
                    "eso_results": "base"
                }
            }
        )
        base.set_build_directory(self.temp_base_build_dir)
        base.run = True

        mod = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_mod_build_dir,
            self.temp_mod_source_dir,
            {
                "config": {
                    "run_time_string": "00hr 10min  0.17sec",
                    "num_warnings": 2,
                    "num_severe": 1,
                    "end_state": "success",
                    "eso_results": "base"
                }
            }
        )
        mod.set_build_directory(self.temp_mod_build_dir)
        mod.run = True

        entries = [TestEntry('my_file', 'my_weather')]
        config = TestRunConfiguration(
            force_run_type=ForceRunType.DD,
            single_test_run=False,
            num_threads=1,
            report_freq=ReportingFreq.HOURLY,
            build_a=base,
            build_b=mod
        )
        r = SuiteRunner(config, entries)
        r.add_callbacks(
            print_callback=TestTestSuiteRunner.dummy_callback,
            simstarting_callback=TestTestSuiteRunner.dummy_callback,
            casecompleted_callback=TestTestSuiteRunner.dummy_callback,
            simulationscomplete_callback=TestTestSuiteRunner.dummy_callback,
            diffcompleted_callback=TestTestSuiteRunner.dummy_callback,
            alldone_callback=TestTestSuiteRunner.dummy_callback,
            cancel_callback=TestTestSuiteRunner.dummy_callback
        )
        diff_results = r.run_test_suite()
        # there should be 1 file result
        self.assertEqual(1, len(diff_results.entries_by_file))
        results_for_file = diff_results.entries_by_file[0]
        # it should be named according to what we listed above
        self.assertEqual('my_file', results_for_file.basename)
        # it should have succeeded in both base and mod cases
        self.assertEqual(EndErrSummary.STATUS_SUCCESS, results_for_file.summary_result.simulation_status_case1)
        self.assertEqual(EndErrSummary.STATUS_SUCCESS, results_for_file.summary_result.simulation_status_case2)
        # it should have created a test directory and dropped the summaries there
        results_dir = diff_results.results_dir
        self.assertIn('DDOnly', results_dir)

    def test_both_success_no_diffs_annual(self):
        base = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_base_build_dir,
            self.temp_base_source_dir,
            {
                "config": {
                    "run_time_string": "01hr 20min  0.17sec",
                    "num_warnings": 1,
                    "num_severe": 0,
                    "end_state": "success",
                    "eso_results": "base"
                }
            }
        )
        base.set_build_directory(self.temp_base_build_dir)
        base.run = True

        mod = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_mod_build_dir,
            self.temp_mod_source_dir,
            {
                "config": {
                    "run_time_string": "00hr 10min  0.17sec",
                    "num_warnings": 2,
                    "num_severe": 1,
                    "end_state": "success",
                    "eso_results": "base"
                }
            }
        )
        mod.set_build_directory(self.temp_mod_build_dir)
        mod.run = True

        entries = [TestEntry('my_file', 'my_weather')]
        config = TestRunConfiguration(
            force_run_type=ForceRunType.ANNUAL,
            single_test_run=False,
            num_threads=1,
            report_freq=ReportingFreq.HOURLY,
            build_a=base,
            build_b=mod
        )
        r = SuiteRunner(config, entries)
        r.add_callbacks(
            print_callback=TestTestSuiteRunner.dummy_callback,
            simstarting_callback=TestTestSuiteRunner.dummy_callback,
            casecompleted_callback=TestTestSuiteRunner.dummy_callback,
            simulationscomplete_callback=TestTestSuiteRunner.dummy_callback,
            diffcompleted_callback=TestTestSuiteRunner.dummy_callback,
            alldone_callback=TestTestSuiteRunner.dummy_callback,
            cancel_callback=TestTestSuiteRunner.dummy_callback
        )
        diff_results = r.run_test_suite()
        # there should be 1 file result
        self.assertEqual(1, len(diff_results.entries_by_file))
        results_for_file = diff_results.entries_by_file[0]
        # it should be named according to what we listed above
        self.assertEqual('my_file', results_for_file.basename)
        # it should have succeeded in both base and mod cases
        self.assertEqual(EndErrSummary.STATUS_SUCCESS, results_for_file.summary_result.simulation_status_case1)
        self.assertEqual(EndErrSummary.STATUS_SUCCESS, results_for_file.summary_result.simulation_status_case2)
        # it should have created a test directory and dropped the summaries there
        results_dir = diff_results.results_dir
        self.assertIn('Annual', results_dir)

    def test_file_does_not_exist(self):
        base = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_base_build_dir,
            self.temp_base_source_dir,
            {
                "config": {
                    "run_time_string": "01hr 20min  0.17sec",
                    "num_warnings": 1,
                    "num_severe": 0,
                    "end_state": "success",
                    "eso_results": "base"
                }
            }
        )
        base.set_build_directory(self.temp_base_build_dir)
        base.run = True

        mod = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_mod_build_dir,
            self.temp_mod_source_dir,
            {
                "config": {
                    "run_time_string": "00hr 10min  0.17sec",
                    "num_warnings": 2,
                    "num_severe": 1,
                    "end_state": "success",
                    "eso_results": "base"
                }
            }
        )
        mod.set_build_directory(self.temp_mod_build_dir)
        mod.run = True

        entries = [TestEntry('my_file_DOES_NOT_EXIST', 'my_weather')]
        config = TestRunConfiguration(
            force_run_type=ForceRunType.NONE,
            single_test_run=False,
            num_threads=1,
            report_freq=ReportingFreq.HOURLY,
            build_a=base,
            build_b=mod
        )
        r = SuiteRunner(config, entries)
        r.add_callbacks(
            print_callback=TestTestSuiteRunner.dummy_callback,
            simstarting_callback=TestTestSuiteRunner.dummy_callback,
            casecompleted_callback=TestTestSuiteRunner.dummy_callback,
            simulationscomplete_callback=TestTestSuiteRunner.dummy_callback,
            diffcompleted_callback=TestTestSuiteRunner.dummy_callback,
            alldone_callback=TestTestSuiteRunner.dummy_callback,
            cancel_callback=TestTestSuiteRunner.dummy_callback
        )
        diff_results = r.run_test_suite()
        # there should be 1 file result
        self.assertEqual(1, len(diff_results.entries_by_file))
        results_for_file = diff_results.entries_by_file[0]
        # it should be named according to what we listed above
        self.assertEqual('my_file_DOES_NOT_EXIST', results_for_file.basename)
        # it should have failed in both base and mod cases
        self.assertEqual(EndErrSummary.STATUS_MISSING, results_for_file.summary_result.simulation_status_case1)
        self.assertEqual(EndErrSummary.STATUS_MISSING, results_for_file.summary_result.simulation_status_case2)

    def test_eio_diff_with_utf8(self):
        base_eio = os.path.join(self.resources, 'eplusout_with_utf8_base.eio')
        mod_eio = os.path.join(self.resources, 'eplusout_with_utf8_mod.eio')
        diff_file = os.path.join(self.temp_base_build_dir, 'eio.diff')
        self.assertEqual(TextDifferences.DIFFS, SuiteRunner.diff_text_files(base_eio, mod_eio, diff_file))

    def test_content_reader(self):
        file_path_to_read = os.path.join(self.resources, 'BadUTF8Marker.idf')
        # this should simply pass without throwing an exception
        SuiteRunner.read_file_content(file_path_to_read)
