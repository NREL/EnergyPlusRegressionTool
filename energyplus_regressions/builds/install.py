from pathlib import Path

from energyplus_regressions.builds.base import BaseBuildDirectoryStructure, BuildTree
from energyplus_regressions.ep_platform import exe_extension


class EPlusInstallDirectory(BaseBuildDirectoryStructure):

    def set_build_directory(self, build_directory: Path):
        """
        This method takes a build directory, and updates any dependent member variables, in this case the source dir.
        This method *does* allow an invalid build_directory, as could happen during program initialization

        :param build_directory:
        :return:
        """
        self.build_directory: Path = build_directory
        if not self.build_directory.exists():
            self.source_directory = Path('unknown')
            return
        # For an E+ install, the source directory is kinda just the root repo
        self.source_directory = build_directory

    def get_idf_directory(self):
        if not self.build_directory:
            raise Exception('Build directory has not been set with set_build_directory()')
        return self.source_directory / 'ExampleFiles'

    def get_build_tree(self) -> BuildTree:
        if not self.build_directory:
            raise Exception('Build directory has not been set with set_build_directory()')
        this_exe_ext = exe_extension()
        b = BuildTree()
        b.build_dir = self.build_directory
        b.source_dir = self.source_directory
        b.energyplus = self.build_directory / ('energyplus' + this_exe_ext)
        b.basement = self.build_directory / 'PreProcess' / 'GrndTempCalc' / ('Basement' + this_exe_ext)
        b.idd_path = self.build_directory / 'Energy+.idd'
        b.slab = self.build_directory / 'PreProcess' / 'GrndTempCalc' / ('Slab' + this_exe_ext)
        b.basementidd = self.build_directory / 'PreProcess' / 'GrndTempCalc' / 'BasementGHT.idd'
        b.slabidd = self.build_directory / 'PreProcess' / 'GrndTempCalc' / 'SlabGHT.idd'
        b.expandobjects = self.build_directory / ('ExpandObjects' + this_exe_ext)
        b.epmacro = self.build_directory / ('EPMacro' + this_exe_ext)
        b.readvars = self.build_directory / 'PostProcess' / 'ReadVarsESO'
        pre = 'ParametricPreprocessor' + this_exe_ext
        b.parametric = self.build_directory / 'PreProcess' / 'ParametricPreprocessor' / pre
        b.test_files_dir = self.source_directory / 'ExampleFiles'
        b.weather_dir = self.source_directory / 'WeatherData'
        b.data_sets_dir = self.source_directory / 'DataSets'
        return b
