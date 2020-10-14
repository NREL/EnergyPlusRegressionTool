import os


class KnownBuildTypes:
    Makefile = "makefile"
    VisualStudio = "visual_studio"
    Installation = "install"
    Unknown = "unknown"  # could be used to ask user to manually specify type


def autodetect_build_dir_type(build_dir: str) -> str:
    # detect the cmake cache file first
    cmake_cache_file = os.path.join(build_dir, 'CMakeCache.txt')
    if not os.path.exists(cmake_cache_file):
        # leaning toward install folder
        example_files_dir = os.path.join(build_dir, 'ExampleFiles')
        if os.path.exists(example_files_dir):
            return KnownBuildTypes.Installation

    # ok, at this point we have a cache file, read it to find the generator
    with open(cmake_cache_file, 'r') as f_cache:
        for this_line in f_cache.readlines():
            if 'CMAKE_GENERATOR:INTERNAL=' in this_line:
                tokens = this_line.strip().split('=')
                generator_name = tokens[1]
                if "Visual Studio" in generator_name:
                    return KnownBuildTypes.VisualStudio
                elif 'Makefile' in generator_name:
                    return KnownBuildTypes.Makefile
    return KnownBuildTypes.Unknown


class BaseBuildDirectoryStructure(object):
    def __init__(self):
        self.build_directory = None
        self.run = None

    def set_build_directory(self, build_directory):
        raise NotImplementedError('Must implement set_build_directory(str) in derived classes')

    def verify(self):
        raise NotImplementedError('Must implement verify() in derived classes')

    def get_build_tree(self):
        raise NotImplementedError('Must implement get_build_tree() in derived classes')

    def get_idf_directory(self):
        raise NotImplementedError()
