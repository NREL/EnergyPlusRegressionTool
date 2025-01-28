import os

from energyplus_regressions.builds.base import BaseBuildDirectoryStructure, BuildTree
from energyplus_regressions.ep_platform import exe_extension


class CMakeCacheMakeFileBuildDirectory(BaseBuildDirectoryStructure):

    def __init__(self):
        super(CMakeCacheMakeFileBuildDirectory, self).__init__()
        self.source_directory: str = ""

    def set_build_directory(self, build_directory: str):
        """
        This method takes a build directory, and updates any dependent member variables, in this case the source dir.
        This method *does* allow an invalid build_directory, as could happen during program initialization

        :param build_directory:
        :return:
        """
        self.build_directory: str = build_directory
        if not os.path.exists(self.build_directory):
            self.source_directory = 'unknown - invalid build directory?'
            return
        cmake_cache_file = os.path.join(self.build_directory, 'CMakeCache.txt')
        if not os.path.exists(cmake_cache_file):
            raise Exception('Could not find cache file in build directory')
        with open(cmake_cache_file, 'r') as f_cache:
            for this_line in f_cache.readlines():
                if 'CMAKE_HOME_DIRECTORY:INTERNAL=' in this_line:
                    tokens = this_line.strip().split('=')
                    self.source_directory = tokens[1]
                    break
            else:
                raise Exception('Could not find source directory spec in the CMakeCache file')

    def get_idf_directory(self):
        if not self.build_directory:
            raise Exception('Build directory has not been set with set_build_directory()')
        return os.path.join(self.source_directory, 'testfiles')

    def get_build_tree(self) -> BuildTree:
        if not self.build_directory:
            raise Exception('Build directory has not been set with set_build_directory()')
        this_exe_ext = exe_extension()
        b = BuildTree()
        b.build_dir = self.build_directory
        b.source_dir = self.source_directory
        b.energyplus = os.path.join(self.build_directory, 'Products', 'energyplus' + this_exe_ext)
        b.basement = os.path.join(self.build_directory, 'Products', 'Basement' + this_exe_ext)
        b.idd_path = os.path.join(self.build_directory, 'Products', 'Energy+.idd')
        b.slab = os.path.join(self.build_directory, 'Products', 'Slab' + this_exe_ext)
        b.basementidd = os.path.join(self.build_directory, 'Products', 'BasementGHT.idd')
        b.slabidd = os.path.join(self.build_directory, 'Products', 'SlabGHT.idd')
        b.expandobjects = os.path.join(self.build_directory, 'Products', 'ExpandObjects' + this_exe_ext)
        b.epmacro = os.path.join(self.source_directory, 'bin', 'EPMacro', 'Linux', 'EPMacro' + this_exe_ext)
        b.readvars = os.path.join(self.build_directory, 'Products', 'ReadVarsESO' + this_exe_ext)
        b.parametric = os.path.join(self.build_directory, 'Products', 'ParametricPreprocessor' + this_exe_ext)
        b.test_files_dir = os.path.join(self.source_directory, 'testfiles')
        b.weather_dir = os.path.join(self.source_directory, 'weather')
        b.data_sets_dir = os.path.join(self.source_directory, 'datasets')
        return b
