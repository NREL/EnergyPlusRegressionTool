import json
import os
import shutil
import tempfile
import unittest

from epregressions.builds.makefile import CMakeCacheMakeFileBuildDirectory
from epregressions.runtests import TestRunConfiguration, SuiteRunner
from epregressions.structures import ForceRunType, ReportingFreq, TestEntry


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
        }
        for source in products_map:
            shutil.copy(source, products_map[source])
        testfiles_dir = os.path.join(target_source_dir, 'testfiles')
        os.makedirs(testfiles_dir)
        with open(os.path.join(testfiles_dir, 'my_file.idf'), 'w') as f:
            f.write(json.dumps(idf_config))
        weather_dir = os.path.join(target_source_dir, 'weather')
        os.makedirs(weather_dir)
        shutil.copy(os.path.join(self.resources, 'dummy.in.epw'), os.path.join(weather_dir, 'my_weather.epw'))
        # os.path.join(self.resource_dir, 'dummy.epmacro.py'): os.path.join(products_dir, 'Energy+.idd'),
        # os.path.join(self.resource_dir, 'dummy.in.epw'): os.path.join(products_dir, 'Energy+.idd'),

    @staticmethod
    def dummy_callback(*args, **kwargs):
        pass

    def test_a(self):
        base = CMakeCacheMakeFileBuildDirectory()
        self.establish_build_folder(
            self.temp_base_build_dir,
            self.temp_base_source_dir,
            {
                "config": {
                    "run_time_string": "01hr 20min  0.17sec",
                    "num_warnings": 1,
                    "num_severe": 0,
                    "end_state": "success"
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
                    "end_state": "success"
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
            enderrcompleted_callback=TestTestSuiteRunner.dummy_callback,
            diffcompleted_callback=TestTestSuiteRunner.dummy_callback,
            alldone_callback=TestTestSuiteRunner.dummy_callback,
            cancel_callback=TestTestSuiteRunner.dummy_callback
        )
        diff_results = r.run_test_suite()
        i = 1
