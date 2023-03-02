import os
import tempfile
import unittest

from energyplus_regressions.epw_map import get_epw_for_idf


class TestGetEPW(unittest.TestCase):

    def setUp(self) -> None:
        self.repo_source_dir = tempfile.mkdtemp()

    def add_test_files_dir(self, content_to_add_to_cmake_lists=None):
        test_files_dir = os.path.join(self.repo_source_dir, 'testfiles')
        os.makedirs(test_files_dir)
        if content_to_add_to_cmake_lists:
            cmake_lists = os.path.join(test_files_dir, 'CMakeLists.txt')
            with open(cmake_lists, 'w') as f:
                f.write(content_to_add_to_cmake_lists)

    def test_repo_dir_does_not_exist(self):
        fake_dir = os.path.join(self.repo_source_dir, 'not_there')
        epw = get_epw_for_idf(fake_dir, "DoesntMatter.idf")
        self.assertIsNone(epw)

    def test_install_style_lookup_in_map(self):
        epw = get_epw_for_idf(self.repo_source_dir, "ZoneWSHP_wDOAS.idf")
        self.assertIsInstance(epw, str)

    def test_install_style_lookup_not_in_map(self):
        epw = get_epw_for_idf(self.repo_source_dir, "NOT_ZoneWSHP_wDOAS.idf")
        self.assertIsNone(epw)

    def test_build_folder_but_no_cmake_lists(self):
        self.add_test_files_dir()
        epw = get_epw_for_idf(self.repo_source_dir, "DoesntMatterAgain.idf")
        self.assertIsNone(epw)

    def test_find_idf_in_cmake_lists(self):
        content = """
# Four lines here, one plain comment, one comment with the filename in it, one real line, one real line with suffix
# ADD_SIMULATION_TEST(IDF_FILE HELLO.idf EPW_FILE WORLD.epw)
ADD_SIMULATION_TEST(IDF_FILE FOO.idf EPW_FILE BAR.epw)
ADD_SIMULATION_TEST(IDF_FILE BLAH.idf EPW_FILE OK.epw ANNUAL_SIMULATION)
        """
        self.add_test_files_dir(content_to_add_to_cmake_lists=content)
        epw = get_epw_for_idf(self.repo_source_dir, "FOO.idf")
        self.assertEqual(epw, "BAR.epw")
        epw = get_epw_for_idf(self.repo_source_dir, "NOT_HOSPITAL.idf")
        self.assertIsNone(epw)
        epw = get_epw_for_idf(self.repo_source_dir, "BLAH.idf")
        self.assertEqual(epw, "OK.epw")
