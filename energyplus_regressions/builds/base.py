from pathlib import Path
from typing import Optional, Set


class KnownBuildTypes:
    Makefile = "makefile"
    VisualStudio = "visual_studio"
    Installation = "install"
    Unknown = "unknown"  # could be used to ask user to manually specify type


def autodetect_build_dir_type(build_dir: Path) -> str:
    # detect the cmake cache file first
    cmake_cache_file = build_dir / 'CMakeCache.txt'
    if not cmake_cache_file.exists():
        # leaning toward install folder
        example_files_dir = build_dir / 'ExampleFiles'
        if example_files_dir.exists():
            return KnownBuildTypes.Installation
    else:  # we have a cache file, read it to find the generator
        with open(cmake_cache_file, 'r') as f_cache:
            for this_line in f_cache.readlines():
                if 'CMAKE_GENERATOR:INTERNAL=' in this_line:
                    tokens = this_line.strip().split('=')
                    generator_name = tokens[1]
                    if "Visual Studio" in generator_name:
                        return KnownBuildTypes.VisualStudio
                    elif 'Makefile' in generator_name:
                        return KnownBuildTypes.Makefile
                    elif 'Ninja' in generator_name:
                        return KnownBuildTypes.Makefile
    return KnownBuildTypes.Unknown


class BuildTree:
    def __init__(self) -> None:
        self.build_dir: Path = Path()
        self.source_dir: Path = Path()
        self.energyplus: Path = Path()
        self.basement: Path = Path()
        self.idd_path: Path = Path()
        self.slab: Path = Path()
        self.basementidd: Path = Path()
        self.slabidd: Path = Path()
        self.expandobjects: Path = Path()
        self.epmacro: Path = Path()
        self.readvars: Path = Path()
        self.parametric: Path = Path()
        self.test_files_dir: Path = Path()
        self.weather_dir: Path = Path()
        self.data_sets_dir: Path = Path()


class BaseBuildDirectoryStructure(object):
    def __init__(self):
        self.build_directory: Optional[Path] = None
        self.source_directory: Optional[Path] = None

    @staticmethod
    def get_idfs_in_dir(idf_dir: Path) -> Set[Path]:
        idf_path = Path(idf_dir)
        all_idfs_absolute_path = list(idf_path.rglob('*.idf'))
        all_idfs_absolute_path.extend(list(idf_path.rglob('*.imf')))
        all_idfs_absolute_path.extend(list(idf_path.rglob('*.epJSON')))
        all_idfs_relative_path = set([idf.relative_to(idf_path) for idf in all_idfs_absolute_path])
        known_ignore_list = [
            # these files are for running EnergyPlus _as an FMU_ and we aren't doing that
            '_ExternalInterface-actuator.idf',
            '_ExternalInterface-schedule.idf',
            '_ExternalInterface-variable.idf',
            # these files are macro resource files, imported by AbsorptionChiller_Macro.imf
            'HVAC3ZoneGeometry.imf',
            'HVAC3ZoneMat-Const.imf',
            'HVAC3ZoneChillerSpec.imf',
            'HVAC3Zone-IntGains-Def.imf',
        ]

        def should_keep(file_path: Path):
            for i in known_ignore_list:
                if i in str(file_path):
                    return False
                if 'API' in file_path.parts:
                    # the testfiles/API directory is for Python API calls, we aren't doing that here, yet.
                    return False
            return True

        filtered_list = filter(should_keep, all_idfs_relative_path)
        return set(filtered_list)

    def set_build_directory(self, build_directory: Path):
        raise NotImplementedError('Must implement set_build_directory(str) in derived classes')

    def verify(self):
        results: list[tuple[str, Path, bool]] = []
        if not self.build_directory:
            raise Exception('Build directory has not been set with set_build_directory()')
        build_dir = self.build_directory
        results.append(
            ("Case %s Build Directory Exists? ", build_dir, build_dir.exists())
        )
        results.append(
            ("Case %s Source Directory Exists? ", self.source_directory, self.source_directory.exists())
        )
        # get everything else off the build tree
        tree: BuildTree = self.get_build_tree()
        test_files_dir = tree.test_files_dir
        results.append(
            ("Case %s Test Files Directory Exists? ", test_files_dir, test_files_dir.exists())
        )
        data_sets_dir = tree.data_sets_dir
        results.append(
            ("Case %s Data Sets Directory Exists? ", data_sets_dir, data_sets_dir.exists())
        )
        energy_plus_exe = tree.energyplus
        results.append(
            ("Case %s EnergyPlus Binary Exists? ", energy_plus_exe, energy_plus_exe.exists())
        )
        basement_exe = tree.basement
        results.append(
            ("Case %s Basement (Fortran) Binary Exists? ", basement_exe, basement_exe.exists())
        )
        slab_exe = tree.slab
        results.append(
            ("Case %s Slab (Fortran) Binary Exists? ", slab_exe, slab_exe.exists())
        )
        expand_objects_exe = tree.expandobjects
        results.append(
            ("Case %s ExpandObjects (Fortran) Binary Exists? ", expand_objects_exe, expand_objects_exe.exists())
        )
        read_vars_exe = tree.readvars
        results.append(
            ("Case %s ReadVarsESO (Fortran) Binary Exists? ", read_vars_exe, read_vars_exe.exists())
        )
        parametric_exe = tree.parametric
        results.append(
            ("Case %s Parametric Preprocessor (Fortran) Binary Exists? ", parametric_exe, parametric_exe.exists())
        )
        return results

    def get_build_tree(self) -> BuildTree:
        raise NotImplementedError('Must implement get_build_tree() in derived classes')

    def get_idf_directory(self):
        raise NotImplementedError()
