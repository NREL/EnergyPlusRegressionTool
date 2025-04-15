from pathlib import Path
from typing import Callable

from energyplus_regressions.builds.base import BaseBuildDirectoryStructure, BuildTree
from energyplus_regressions.structures import ConfigType


class CMakeCacheVisualStudioBuildDirectory(BaseBuildDirectoryStructure):
    """
    A Visual Studio based build directory class
    This tries to use a "Release" folder, but if it does not exist it tries to fall back to a "Debug" folder
    """

    def __init__(self):
        super(CMakeCacheVisualStudioBuildDirectory, self).__init__()
        self.build_mode: str = ConfigType.RELEASE.value

    def set_build_mode(self, config: ConfigType, error_callback: Callable[[str], None] | None = None) -> None:
        build_mode_folder = config.value
        desired_build_directory = self.build_directory / 'Products' / build_mode_folder
        if desired_build_directory.exists():
            self.build_mode = config.value
        else:
            if error_callback:
                error_callback(
                    f"Attempted to set build mode as {config.value} but did not detect build dir, use caution! :)"
                )
            build_mode_folder = 'Release'
            release_folder = self.build_directory / 'Products' / build_mode_folder
            release_folder_exists = release_folder.exists()
            if release_folder_exists:
                self.build_mode = ConfigType.RELEASE.value
            else:  # Finally, if we can't find release either, just set it to debug and let the user deal with it
                self.build_mode = ConfigType.DEBUG.value

    def set_build_directory(self, build_directory: Path) -> None:
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
        cmake_cache_file = self.build_directory / 'CMakeCache.txt'
        with open(cmake_cache_file, 'r') as f_cache:
            for this_line in f_cache.readlines():
                if 'CMAKE_HOME_DIRECTORY:INTERNAL=' in this_line:
                    tokens = this_line.strip().split('=')
                    self.source_directory = Path(tokens[1])
                    break
            else:
                raise Exception('Could not find source directory spec in the CMakeCache file')

    def get_idf_directory(self) -> Path:
        if not self.build_directory:
            raise Exception('Build directory has not been set with set_build_directory()')
        return self.source_directory / 'testfiles'

    def get_build_tree(self) -> BuildTree:
        if not self.build_directory:
            raise Exception('Build directory has not been set with set_build_directory()')
        b = BuildTree()
        b.build_dir = self.build_directory
        b.source_dir = self.source_directory
        b.energyplus = self.build_directory / 'Products' / self.build_mode / 'energyplus.exe'
        b.basement = self.build_directory / 'Products' / 'Basement.exe'
        b.idd_path = self.build_directory / 'Products' / 'Energy+.idd'
        b.slab = self.build_directory / 'Products' / 'Slab.exe'
        b.basementidd = self.build_directory / 'Products' / 'BasementGHT.idd'
        b.slabidd = self.build_directory / 'Products' / 'SlabGHT.idd'
        b.expandobjects = self.build_directory / 'Products' / 'ExpandObjects.exe'
        b.epmacro = self.source_directory / 'bin' / 'EPMacro' / 'Linux' / 'EPMacro.exe'
        b.readvars = self.build_directory / 'Products' / 'ReadVarsESO.exe'
        b.parametric = self.build_directory / 'Products' / 'ParametricPreprocessor.exe'
        b.test_files_dir = self.source_directory / 'testfiles'
        b.weather_dir = self.source_directory / 'weather'
        b.data_sets_dir = self.source_directory / 'datasets'
        return b
