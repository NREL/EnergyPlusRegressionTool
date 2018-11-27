import unittest

from epregressions.main_window import ResultsTreeRoots


class TestResultsTreeRoots(unittest.TestCase):

    def test_length(self):
        """If the length of this changes, the UI must be updated also"""
        tree_roots = ResultsTreeRoots.list_all()
        self.assertEqual(11, len(tree_roots))
