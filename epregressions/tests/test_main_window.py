import unittest

from epregressions.main_window import RegressionGUI, ResultsTreeRoots
from epregressions.structures import ForceRunType, ReportingFreq


class TestResultsTreeRoots(unittest.TestCase):

    def test_length(self):
        """If the length of this changes, the UI must be updated also"""
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
        self.gui.force_run_type = ForceRunType.NONE
        self.gui.gui_fill_with_data()
        value_no_force = self.gui.run_type_combo_box.get_active()
        self.gui.force_run_type = ForceRunType.DD
        self.gui.gui_fill_with_data()
        value_dd = self.gui.run_type_combo_box.get_active()
        self.gui.force_run_type = ForceRunType.ANNUAL
        self.gui.gui_fill_with_data()
        value_annual = self.gui.run_type_combo_box.get_active()
        unique_list = {value_no_force, value_dd, value_annual}
        self.assertEqual(3, len(unique_list))
