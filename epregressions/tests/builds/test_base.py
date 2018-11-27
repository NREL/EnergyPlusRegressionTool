import unittest

from epregressions.builds.base import BaseBuildDirectoryStructure


class TestBaseBuildMethods(unittest.TestCase):

    def setUp(self):
        self.base_build = BaseBuildDirectoryStructure()

    def test_set_build_directory_abstract(self):
        with self.assertRaises(NotImplementedError):
            self.base_build.set_build_directory('hello')

    def test_verify_abstract(self):
        with self.assertRaises(NotImplementedError):
            self.base_build.verify()

    def test_get_build_tree_abstract(self):
        with self.assertRaises(NotImplementedError):
            self.base_build.get_build_tree()
