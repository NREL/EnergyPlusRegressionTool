import os
import sys
import tempfile
import unittest

from energyplus_regressions.energyplus import ExecutionArguments, execute_energyplus
from energyplus_regressions.structures import ReportingFreq, ForceRunType


class TestEnergyPlus(unittest.TestCase):

    def setUp(self):
        cur_dir_path = os.path.dirname(os.path.realpath(__file__))
        self.resource_dir = os.path.join(cur_dir_path, 'resources')
        self.build_tree = {
            'energyplus': os.path.join(self.resource_dir, 'dummy.energyplus.py'),
            'basement': os.path.join(self.resource_dir, 'dummy.basement.py'),
            'idd_path': os.path.join(self.resource_dir, 'dummy.Energy+.idd'),
            'slab': os.path.join(self.resource_dir, 'dummy.slab.py'),
            'basementidd': os.path.join(self.resource_dir, 'dummy.basement.idd'),
            'slabidd': os.path.join(self.resource_dir, 'dummy.slab.py'),
            'expandobjects': os.path.join(self.resource_dir, 'dummy.expandobjects.py'),
            'epmacro': os.path.join(self.resource_dir, 'dummy.epmacro.py'),
            'readvars': os.path.join(self.resource_dir, 'dummy.readvars.py'),
            'parametric': os.path.join(self.resource_dir, 'dummy.parametric.py'),
            'build_dir': '/dummy/'
        }
        self.run_dir = tempfile.mkdtemp()

    def test_eplus_passed_simple_dd_only(self):
        with open(os.path.join(self.run_dir, 'in.idf'), 'w') as f:
            f.write('')
        return_val = execute_energyplus(ExecutionArguments(
            build_tree=self.build_tree,
            entry_name='entry_name',
            test_run_directory=self.run_dir,
            run_type=ForceRunType.DD,
            min_reporting_freq=ReportingFreq.HOURLY,
            this_parametric_file=False,
            weather_file_name=''
        ))
        self.assertEqual('/dummy/', return_val[0])
        self.assertEqual('entry_name', return_val[1])
        self.assertTrue(return_val[2])
        self.assertFalse(return_val[3])

    def test_eplus_passed_simple_dd_only_with_rvi_mvi(self):
        with open(os.path.join(self.run_dir, 'in.idf'), 'w') as f:
            f.write('')
        with open(os.path.join(self.run_dir, 'in.rvi'), 'w') as f:
            f.write('HI')
        with open(os.path.join(self.run_dir, 'in.mvi'), 'w') as f:
            f.write('HI')
        return_val = execute_energyplus(ExecutionArguments(
            build_tree=self.build_tree,
            entry_name='entry_name',
            test_run_directory=self.run_dir,
            run_type=ForceRunType.DD,
            min_reporting_freq=ReportingFreq.HOURLY,
            this_parametric_file=False,
            weather_file_name=''
        ))
        self.assertEqual('/dummy/', return_val[0])
        self.assertEqual('entry_name', return_val[1])
        self.assertTrue(return_val[2])
        self.assertFalse(return_val[3])

    def test_eplus_passed_simple_annual(self):
        weather_file = os.path.join(self.resource_dir, 'dummy.in.epw')
        with open(os.path.join(self.run_dir, 'in.idf'), 'w') as f:
            f.write('')
        return_val = execute_energyplus(ExecutionArguments(
            build_tree=self.build_tree,
            entry_name='entry_name',
            test_run_directory=self.run_dir,
            run_type=ForceRunType.ANNUAL,
            min_reporting_freq=ReportingFreq.HOURLY,
            this_parametric_file=False,
            weather_file_name=weather_file
        ))
        self.assertEqual('/dummy/', return_val[0])
        self.assertEqual('entry_name', return_val[1])
        self.assertTrue(return_val[2])
        self.assertFalse(return_val[3])

    def test_eplus_passed_simple_no_force(self):
        weather_file = os.path.join(self.resource_dir, 'dummy.in.epw')
        with open(os.path.join(self.run_dir, 'in.idf'), 'w') as f:
            f.write('')
        return_val = execute_energyplus(ExecutionArguments(
            build_tree=self.build_tree,
            entry_name='entry_name',
            test_run_directory=self.run_dir,
            run_type=ForceRunType.NONE,
            min_reporting_freq=ReportingFreq.HOURLY,
            this_parametric_file=False,
            weather_file_name=weather_file
        ))
        self.assertEqual('/dummy/', return_val[0])
        self.assertEqual('entry_name', return_val[1])
        self.assertTrue(return_val[2])
        self.assertFalse(return_val[3])

    def test_eplus_passed_hvac_template(self):
        with open(os.path.join(self.run_dir, 'in.idf'), 'w') as f:
            f.write('HVACTEMPLATE')
        return_val = execute_energyplus(ExecutionArguments(
            build_tree=self.build_tree,
            entry_name='entry_name',
            test_run_directory=self.run_dir,
            run_type=ForceRunType.DD,
            min_reporting_freq=ReportingFreq.HOURLY,
            this_parametric_file=False,
            weather_file_name=''
        ))
        self.assertEqual('/dummy/', return_val[0])
        self.assertEqual('entry_name', return_val[1])
        self.assertTrue(return_val[2])
        self.assertFalse(return_val[3])

    @unittest.skipIf(sys.platform.startswith('win'), "GH Actions is having trouble executing dummy.epmacro")
    def test_eplus_passed_macro(self):
        with open(os.path.join(self.run_dir, 'in.imf'), 'w') as f:
            f.write('##fileprefix line\n')
            f.write('line2\n')
            f.write('##fileprefix line3\n')
        return_val = execute_energyplus(ExecutionArguments(
            build_tree=self.build_tree,
            entry_name='entry_name',
            test_run_directory=self.run_dir,
            run_type=ForceRunType.DD,
            min_reporting_freq=ReportingFreq.HOURLY,
            this_parametric_file=False,
            weather_file_name=''
        ))
        self.assertEqual('/dummy/', return_val[0])
        self.assertEqual('entry_name', return_val[1])
        self.assertTrue(return_val[2])
        self.assertFalse(return_val[3])

    @unittest.skipIf(sys.platform.startswith('win'), "GH Actions is having trouble executing dummy.parametric")
    def test_eplus_passed_parametric(self):
        with open(os.path.join(self.run_dir, 'in.idf'), 'w') as f:
            f.write('PARAMETRIC:')
        return_val = execute_energyplus(ExecutionArguments(
            build_tree=self.build_tree,
            entry_name='entry_name',
            test_run_directory=self.run_dir,
            run_type=ForceRunType.DD,
            min_reporting_freq=ReportingFreq.HOURLY,
            this_parametric_file=True,
            weather_file_name=''
        ))
        self.assertEqual('/dummy/', return_val[0])
        self.assertEqual('entry_name', return_val[1])
        self.assertTrue(return_val[2])
        self.assertFalse(return_val[3])

    def test_eplus_failed_parametric(self):
        with open(os.path.join(self.run_dir, 'in.idf'), 'w') as f:
            f.write('')
        return_val = execute_energyplus(ExecutionArguments(
            build_tree=self.build_tree,
            entry_name='entry_name',
            test_run_directory=self.run_dir,
            run_type=ForceRunType.DD,
            min_reporting_freq=ReportingFreq.HOURLY,
            this_parametric_file=True,
            weather_file_name=''
        ))
        self.assertEqual('/dummy/', return_val[0])
        self.assertEqual('entry_name', return_val[1])
        self.assertFalse(return_val[2])
        self.assertFalse(return_val[3])

    def test_eplus_failed_invalid_epw(self):
        weather_file = os.path.join(self.resource_dir, 'DOES.NOT.EXIST.in.epw')
        with open(os.path.join(self.run_dir, 'in.idf'), 'w') as f:
            f.write('')
        return_val = execute_energyplus(ExecutionArguments(
            build_tree=self.build_tree,
            entry_name='entry_name',
            test_run_directory=self.run_dir,
            run_type=ForceRunType.ANNUAL,
            min_reporting_freq=ReportingFreq.HOURLY,
            this_parametric_file=False,
            weather_file_name=weather_file
        ))
        self.assertEqual('/dummy/', return_val[0])
        self.assertEqual('entry_name', return_val[1])
        self.assertFalse(return_val[2])  # Fail
        self.assertFalse(return_val[3])
