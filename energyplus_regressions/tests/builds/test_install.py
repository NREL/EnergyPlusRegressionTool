from pathlib import Path
import tempfile
import unittest

from energyplus_regressions.builds.base import BuildTree
from energyplus_regressions.builds.install import EPlusInstallDirectory


class TestEPInstallBuildMethods(unittest.TestCase):

    def setUp(self):
        self.build = EPlusInstallDirectory()
        self.run_dir = Path(tempfile.mkdtemp())

    def test_set_build_directory_does_not_exist(self):
        self.build.set_build_directory(Path('z'))
        self.assertIn('unknown', str(self.build.source_directory))

    def test_set_build_directory_does_exist(self):
        self.build.set_build_directory(self.run_dir)
        self.assertEqual(self.run_dir, self.build.source_directory)

    def test_verify_before_setting_build_directory(self):
        with self.assertRaises(Exception):
            self.build.verify()

    def test_verify_but_nothing_exists(self):
        self.build.set_build_directory(self.run_dir)
        check = self.build.verify()
        self.assertIsInstance(check, list)
        self.assertGreaterEqual(len(check), 4)  # there should be some errors

    def test_get_build_tree_before_setting_build_directory(self):
        with self.assertRaises(Exception):
            self.build.get_build_tree()

    def test_get_build_tree(self):
        self.build.set_build_directory(self.run_dir)
        tree = self.build.get_build_tree()
        self.assertIsInstance(tree, BuildTree)

    def test_get_idf_dir_before_setting_build_directory(self):
        with self.assertRaises(Exception):
            self.build.get_idf_directory()

    def test_get_idf_dir(self):
        self.build.set_build_directory(self.run_dir)
        idf_dir = self.build.get_idf_directory()
        self.assertEqual(self.run_dir / 'ExampleFiles', idf_dir)
