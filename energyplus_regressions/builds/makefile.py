from pathlib import Path

from energyplus_regressions.builds.base import BaseBuildDirectoryStructure, BuildTree
from energyplus_regressions.ep_platform import exe_extension


class CMakeCacheMakeFileBuildDirectory(BaseBuildDirectoryStructure):

    def set_build_directory(self, build_directory: Path):
        """
        This method takes a build directory, and updates any dependent member variables, in this case the source dir.
        This method *does* allow an invalid build_directory, as could happen during program initialization

        :param build_directory:
        :return:
        """
        self.build_directory: Path = build_directory
        if not self.build_directory.exists():
            self.source_directory = Path("unknown")
            return
        cmake_cache_file = self.build_directory / 'CMakeCache.txt'
        if not cmake_cache_file.exists():
            raise Exception('Could not find cache file in build directory')
        with open(cmake_cache_file, 'r') as f_cache:
            for this_line in f_cache.readlines():
                if 'CMAKE_HOME_DIRECTORY:INTERNAL=' in this_line:
                    tokens = this_line.strip().split('=')
                    self.source_directory = Path(tokens[1])
                    break
            else:
                raise Exception('Could not find source directory spec in the CMakeCache file')

    def get_idf_directory(self):
        if not self.build_directory:
            raise Exception('Build directory has not been set with set_build_directory()')
        return self.source_directory / 'testfiles'

    def get_build_tree(self) -> BuildTree:
        if not self.build_directory:
            raise Exception('Build directory has not been set with set_build_directory()')
        this_exe_ext = exe_extension()
        b = BuildTree()
        b.build_dir = self.build_directory
        b.source_dir = self.source_directory
        b.energyplus = self.build_directory / 'Products' / ('energyplus' + this_exe_ext)
        b.basement = self.build_directory / 'Products' / ('Basement' + this_exe_ext)
        b.idd_path = self.build_directory / 'Products' / 'Energy+.idd'
        b.slab = self.build_directory / 'Products' / ('Slab' + this_exe_ext)
        b.basementidd = self.build_directory / 'Products' / 'BasementGHT.idd'
        b.slabidd = self.build_directory / 'Products' / 'SlabGHT.idd'
        b.expandobjects = self.build_directory / 'Products' / ('ExpandObjects' + this_exe_ext)
        b.epmacro = self.source_directory / 'bin' / 'EPMacro' / 'Linux' / ('EPMacro' + this_exe_ext)
        b.readvars = self.build_directory / 'Products' / ('ReadVarsESO' + this_exe_ext)
        b.parametric = self.build_directory / 'Products' / ('ParametricPreprocessor' + this_exe_ext)
        b.test_files_dir = self.source_directory / 'testfiles'
        b.weather_dir = self.source_directory / 'weather'
        b.data_sets_dir = self.source_directory / 'datasets'
        return b
