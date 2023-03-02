import os
import tempfile
import unittest

from energyplus_regressions.builds.visualstudio import CMakeCacheVisualStudioBuildDirectory


class TestVisualStudioBuildMethods(unittest.TestCase):

    def setUp(self):
        self.build = CMakeCacheVisualStudioBuildDirectory()
        self.run_dir = tempfile.mkdtemp()
        self.dummy_source_dir = '/dummy/source/dir'

    def set_cache_file(self):
        with open(os.path.join(self.run_dir, 'CMakeCache.txt'), 'w') as f:
            f.write('HEY\n')
            f.write('CMAKE_HOME_DIRECTORY:INTERNAL=%s\n' % self.dummy_source_dir)
            f.write('HEY AGAIN\n')

    def test_set_build_directory_does_not_exist(self):
        self.build.set_build_directory('hello')
        self.assertIn('unknown', self.build.source_directory)

    def test_set_build_directory_does_exist_but_no_cache(self):
        with self.assertRaises(Exception):
            self.build.set_build_directory(self.run_dir)

    def test_set_build_directory_does_exist_but_empty_cache(self):
        with open(os.path.join(self.run_dir, 'CMakeCache.txt'), 'w') as f:
            f.write('\n')
        with self.assertRaises(Exception):
            self.build.set_build_directory(self.run_dir)

    def test_set_build_directory_and_has_cache(self):
        self.set_cache_file()
        self.build.set_build_directory(self.run_dir)
        self.assertEqual(self.dummy_source_dir, self.build.source_directory)

    def test_verify_before_setting_build_directory(self):
        with self.assertRaises(Exception):
            self.build.verify()

    def test_verify_but_nothing_exists(self):
        self.set_cache_file()
        self.build.set_build_directory(self.run_dir)
        check = self.build.verify()
        self.assertIsInstance(check, list)
        self.assertGreaterEqual(len(check), 4)  # there should be some errors

    def test_verify_with_release_folder(self):
        self.set_cache_file()
        os.makedirs(os.path.join(self.run_dir, 'Products', 'Release'))
        self.build.set_build_directory(self.run_dir)
        check = self.build.verify()
        self.assertIsInstance(check, list)
        self.assertGreaterEqual(len(check), 4)  # there should be some errors

    def test_get_build_tree_before_setting_build_directory(self):
        with self.assertRaises(Exception):
            self.build.get_build_tree()

    def test_get_build_tree(self):
        self.set_cache_file()
        self.build.set_build_directory(self.run_dir)
        tree = self.build.get_build_tree()
        self.assertIsInstance(tree, dict)

    def test_get_idf_dir_before_setting_build_directory(self):
        with self.assertRaises(Exception):
            self.build.get_idf_directory()

    def test_get_idf_dir(self):
        self.set_cache_file()
        self.build.set_build_directory(self.run_dir)
        idf_dir = self.build.get_idf_directory()
        self.assertEqual(os.path.join(self.dummy_source_dir, 'testfiles'), idf_dir)
