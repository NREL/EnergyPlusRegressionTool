import os
import tempfile
import unittest

from epregressions.builds.base import BaseBuildDirectoryStructure, autodetect_build_dir_type, KnownBuildTypes


class TestAutoDetectBuildType(unittest.TestCase):

    def setUp(self):
        self.build_dir = tempfile.mkdtemp()

    def add_cache_file(self, content):
        cache_file = os.path.join(self.build_dir, 'CMakeCache.txt')
        with open(cache_file, 'w') as f:
            f.write(content)

    def add_subdirectory(self, dir_name):
        os.makedirs(os.path.join(self.build_dir, dir_name))

    def test_empty_dir_is_unknown(self):
        self.assertEqual(KnownBuildTypes.Unknown, autodetect_build_dir_type(self.build_dir))

    def test_detect_install(self):
        self.add_subdirectory('ExampleFiles')
        self.assertEqual(KnownBuildTypes.Installation, autodetect_build_dir_type(self.build_dir))

    def test_detect_makefile(self):
        self.add_cache_file('CMAKE_GENERATOR:INTERNAL=Unix Makefiles')
        self.assertEqual(KnownBuildTypes.Makefile, autodetect_build_dir_type(self.build_dir))

    def test_detect_visual_studio(self):
        self.add_cache_file('CMAKE_GENERATOR:INTERNAL=Visual Studio 2019')
        self.assertEqual(KnownBuildTypes.VisualStudio, autodetect_build_dir_type(self.build_dir))


class TestBaseBuildMethods(unittest.TestCase):

    def setUp(self):
        self.base_build = BaseBuildDirectoryStructure()

    def test_set_build_directory_abstract(self):
        with self.assertRaises(NotImplementedError):
            self.base_build.set_build_directory('hello')

    def test_get_build_tree_abstract(self):
        with self.assertRaises(NotImplementedError):
            self.base_build.get_build_tree()

    def test_get_idf_directory(self):
        with self.assertRaises(NotImplementedError):
            self.base_build.get_idf_directory()

    def test_verify_without_setting_build_dir(self):
        with self.assertRaises(Exception):
            self.base_build.verify()

    def test_get_idfs(self):
        temp_idf_dir = tempfile.mkdtemp()
        self.assertSetEqual(set(), self.base_build.get_idfs_in_dir(temp_idf_dir))
        open(os.path.join(temp_idf_dir, 'file1.idf'), 'w').write('hi')
        open(os.path.join(temp_idf_dir, 'file2.iQQ'), 'w').write('he')
        open(os.path.join(temp_idf_dir, 'file3.idf'), 'w').write('ha')
        open(os.path.join(temp_idf_dir, 'file4.imf'), 'w').write('ha')  # macro
        open(os.path.join(temp_idf_dir, '_ExternalInterface-actuator.idf'), 'w').write('ha')  # ext interface as FMU
        open(os.path.join(temp_idf_dir, 'HVAC3ZoneGeometry.imf'), 'w').write('ha')  # macro resource file
        # TODO: Modify the test to expect relevant IMF files as well and fix the function
        self.assertEqual(3, len(self.base_build.get_idfs_in_dir(temp_idf_dir)))
